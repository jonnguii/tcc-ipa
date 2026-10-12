"""Testes automatizados do módulo de Revisão Humana (Fase 9 - Human-in-the-Loop)."""

from datetime import date
import pytest

from src.ipa.executor import StubExecutor
from src.ipa.review import fila
from src.ipa.schemas import ClienteInfo, ItemPedido, PedidoExtraido
from src.ipa.workflow.engine import OrquestradorIPA
from src.ipa.workflow.estados import EstadoWorkflow


@pytest.fixture
def pedido_exemplo() -> PedidoExtraido:
    return PedidoExtraido(
        ref_id="TESTE-REV-001",
        cliente=ClienteInfo(nome="Oficina Mecânica São José Ltda", cnpj_cpf="12.345.679/0001-90"),
        data_entrega=date.today().isoformat(),
        itens=[
            ItemPedido(
                codigo="P-001",
                quantidade=10.0,
            )
        ],
    )


def test_inserir_e_listar_pendencias(pedido_exemplo: PedidoExtraido):
    """Testa se uma pendência é cadastrada com sucesso e listada."""
    registro = fila.inserir_pendencia(
        payload={"ref_id": pedido_exemplo.ref_id, "pedido_original": pedido_exemplo.model_dump()},
        motivos=["Item com similaridade ambígua: 78%"],
        tipo="REVISAO",
        simulada=True,
    )

    assert registro is not None
    assert "id" in registro
    assert registro["status"] == "pendente"

    # Listar pendências
    pendentes = fila.listar_pendencias(status="pendente")
    ids = [p["id"] for p in pendentes]
    assert registro["id"] in ids


def test_obter_pendencia(pedido_exemplo: PedidoExtraido):
    """Testa recuperação dos detalhes de uma pendência específica."""
    registro = fila.inserir_pendencia(
        payload={"ref_id": "TESTE-OBTER-002", "pedido_original": pedido_exemplo.model_dump()},
        motivos=["Data de entrega retroativa"],
        tipo="REVISAO",
        simulada=True,
    )

    pendencia = fila.obter_pendencia(registro["id"])
    assert pendencia is not None
    assert pendencia["id"] == registro["id"]
    assert "Data de entrega retroativa" in pendencia["motivo"]


def test_resolver_pendencia_aprovada(pedido_exemplo: PedidoExtraido):
    """Testa atualização de pendência resolvida com correções e tempo registrado."""
    registro = fila.inserir_pendencia(
        payload={"ref_id": "TESTE-RESOLVER-003", "pedido_original": pedido_exemplo.model_dump()},
        motivos=["Score baixo"],
        tipo="REVISAO",
        simulada=True,
    )

    correcao = {"cliente": "Nome Corrigido", "itens": []}
    resolvida = fila.resolver_pendencia(
        revisao_id=registro["id"],
        status="resolvida",
        correcao=correcao,
        tempo_revisao_s=12.450,
    )

    assert resolvida is not None
    assert resolvida["status"] == "resolvida"
    assert resolvida["correcao"] == correcao
    assert float(resolvida["tempo_revisao_s"]) == 12.450


def test_resolver_pendencia_rejeitada(pedido_exemplo: PedidoExtraido):
    """Testa rejeição de uma pendência pelo operador."""
    registro = fila.inserir_pendencia(
        payload={"ref_id": "TESTE-REJEITAR-004", "pedido_original": pedido_exemplo.model_dump()},
        motivos=["Tentativa de fraude cadastral"],
        tipo="REVISAO",
        simulada=True,
    )

    rejeitada = fila.resolver_pendencia(
        revisao_id=registro["id"],
        status="rejeitada",
        tempo_revisao_s=4.120,
    )

    assert rejeitada is not None
    assert rejeitada["status"] == "rejeitada"
    assert float(rejeitada["tempo_revisao_s"]) == 4.120


def test_orquestrador_retomar_apos_revisao_aprovar(pedido_exemplo: PedidoExtraido):
    """Testa retomada completa do workflow pelo orquestrador com aprovação humana."""
    registro = fila.inserir_pendencia(
        payload={
            "ref_id": pedido_exemplo.ref_id,
            "pedido_original": pedido_exemplo.model_dump(),
        },
        motivos=["Score fuzzy ambíguo"],
        tipo="REVISAO",
        simulada=True,
    )

    orquestrador = OrquestradorIPA(executor=StubExecutor())
    resultado = orquestrador.retomar_apos_revisao(
        revisao_id=registro["id"],
        acao="aprovar",
        pedido_corrigido=pedido_exemplo,
        tempo_revisao_s=8.5,
    )

    assert resultado.estado_final == EstadoWorkflow.CONCLUIDO
    assert resultado.decisao_roteamento == "REVISAO_APROVADA"
    assert resultado.resultado_executor is not None
    assert resultado.resultado_executor["status"] == "sucesso"

    # Verificar se a pendência agora está resolvida no banco
    pendencia_banco = fila.obter_pendencia(registro["id"])
    assert pendencia_banco["status"] == "resolvida"


def test_orquestrador_retomar_apos_revisao_rejeitar(pedido_exemplo: PedidoExtraido):
    """Testa encerramento do workflow pelo orquestrador com rejeição humana."""
    registro = fila.inserir_pendencia(
        payload={
            "ref_id": "TESTE-REV-REJ",
            "pedido_original": pedido_exemplo.model_dump(),
        },
        motivos=["Dados inconsistentes"],
        tipo="REVISAO",
        simulada=True,
    )

    orquestrador = OrquestradorIPA(executor=StubExecutor())
    resultado = orquestrador.retomar_apos_revisao(
        revisao_id=registro["id"],
        acao="rejeitar",
        tempo_revisao_s=3.2,
    )

    assert resultado.estado_final == EstadoWorkflow.REJEITADO
    assert resultado.decisao_roteamento == "REVISAO_REJEITADA"
    assert resultado.resultado_executor is None

    pendencia_banco = fila.obter_pendencia(registro["id"])
    assert pendencia_banco["status"] == "rejeitada"
