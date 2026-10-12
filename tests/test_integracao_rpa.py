"""Testes de integração ponta a ponta do Robô Playwright (RPA) com o ERP Simulado.
Valida o fluxo real no navegador Chromium, prevenção contra duplicidade (idempotência)
e despacho automático a partir da fila de revisão humana.
"""
from __future__ import annotations

import time
import urllib.request
import pytest

from src.ipa.executor import RpaExecutor
from src.ipa.review.fila import inserir_pendencia, obter_pendencia
from src.ipa.schemas import ClienteInfo, ItemPedido, PedidoExtraido
from src.ipa.workflow.engine import OrquestradorIPA
from src.ipa.workflow.estados import EstadoWorkflow


def erp_disponivel() -> bool:
    """Verifica se o servidor do ERP Simulado está respondendo em localhost:8000."""
    try:
        req = urllib.request.Request("http://localhost:8000/pedidos", method="HEAD")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status in (200, 302, 303)
    except Exception:
        # Tenta GET caso HEAD não seja aceito
        try:
            with urllib.request.urlopen("http://localhost:8000/pedidos", timeout=2.0) as resp:
                return resp.status in (200, 302, 303)
        except Exception:
            return False


@pytest.fixture(autouse=True)
def verificar_servidor_erp():
    """Pula os testes de integração do robô se o servidor web do ERP não estiver rodando."""
    if not erp_disponivel():
        pytest.skip("ERP Simulado não está rodando em http://localhost:8000 (necessário para testes com Playwright).")


def test_rpa_executor_insercao_e_idempotencia():
    """Valida inserção de pedido real pelo Playwright e retorno 'duplicado' na 2ª tentativa."""
    timestamp = int(time.time() * 1000)
    ref_unica = f"TESTE-RPA-IDEMPOTENCIA-{timestamp}"

    payload = {
        "ref_id": ref_unica,
        "cliente": {
            "id": 1,  # Cliente existente no ERP
        },
        "data_entrega": "2026-11-15",
        "observacoes": "Pedido de teste automatizado de integração RPA",
        "itens": [
            {"codigo": "P-001", "quantidade": 2},
            {"codigo": "P-002", "quantidade": 4},
        ],
    }

    executor = RpaExecutor()

    # 1. Primeira execução: deve ter sucesso e gerar número de pedido
    res1 = executor.executar(payload)
    assert res1["status"] == "sucesso"
    assert res1["numero_pedido"] is not None
    assert isinstance(res1["numero_pedido"], int)
    assert res1["screenshot"] is not None
    assert res1["modo"] == "RPA"

    num_pedido_criado = res1["numero_pedido"]

    # 2. Segunda execução (mesmo ref_id): deve detectar duplicidade e NÃO criar novo
    res2 = executor.executar(payload)
    assert res2["status"] == "duplicado"
    assert res2["numero_pedido"] == num_pedido_criado
    assert res2["modo"] == "RPA"


def test_orquestrador_com_executor_rpa(tmp_path):
    """Valida o OrquestradorIPA executando o robô Playwright de ponta a ponta."""
    timestamp = int(time.time() * 1000)
    ref_unica = f"TESTE-ORQ-RPA-{timestamp}"

    # Criamos um documento de texto simples simulando a entrada
    doc_teste = tmp_path / f"{ref_unica}.txt"
    doc_teste.write_text(
        f"PEDIDO DE COMPRA: {ref_unica}\n"
        "CLIENTE: Metalúrgica Silva & Filhos Ltda\n"
        "CNPJ: 12.345.678/0001-95\n"
        "DATA: 2026-11-20\n"
        "ITENS:\n"
        "- 5 un Parafuso Sextavado (P-001)\n"
    )

    orquestrador = OrquestradorIPA(tipo_executor="rpa")
    resultado = orquestrador.processar_documento(doc_teste)

    # Verifica transição até conclusão ou roteamento
    assert resultado.estado_final in (EstadoWorkflow.CONCLUIDO, EstadoWorkflow.REVISAO_HUMANA)
    if resultado.estado_final == EstadoWorkflow.CONCLUIDO:
        assert resultado.resultado_executor is not None
        assert resultado.resultado_executor.get("status") in ("sucesso", "duplicado")
        assert resultado.resultado_executor.get("modo") == "RPA"


def test_revisao_humana_retomada_com_rpa():
    """Valida que aprovação na fila de revisão humana despacha o robô Playwright com sucesso."""
    timestamp = int(time.time() * 1000)
    ref_unica = f"TESTE-REV-RPA-{timestamp}"

    # Cria pendência na fila
    pendencia = inserir_pendencia(
        payload={
            "ref_id": ref_unica,
            "pedido_original": {
                "ref_id": ref_unica,
                "cliente": {"nome": "Cliente Teste RPA", "cnpj_cpf": "12345678000195"},
                "data_entrega": "2026-12-01",
                "itens": [{"codigo": "P-005", "quantidade": 10}],
            },
        },
        motivos=["Item com similaridade duvidosa na triagem automática"],
        tipo="REVISAO",
    )
    revisao_id = pendencia["id"]

    # Cria o pedido corrigido aprovado pelo operador humano
    pedido_aprovado = PedidoExtraido(
        ref_id=ref_unica,
        cliente=ClienteInfo(
            id=1,  # Operador vinculou ao cliente cadastrado #1
            nome="Metalúrgica Silva",
            cnpj_cpf="12345678000195",
        ),
        data_entrega="2026-12-01",
        itens=[ItemPedido(codigo="P-005", quantidade=10.0)],
    )

    orquestrador = OrquestradorIPA(tipo_executor="rpa")
    res_retomada = orquestrador.retomar_apos_revisao(
        revisao_id=revisao_id,
        acao="aprovar",
        pedido_corrigido=pedido_aprovado,
        tempo_revisao_s=3.45,
    )

    assert res_retomada.estado_final == EstadoWorkflow.CONCLUIDO
    assert res_retomada.resultado_executor is not None
    assert res_retomada.resultado_executor.get("status") in ("sucesso", "duplicado")
    assert res_retomada.resultado_executor.get("numero_pedido") is not None
    assert res_retomada.resultado_executor.get("modo") == "RPA"

    # Confere se a pendência foi marcada como resolvida
    pendencia_atualizada = obter_pendencia(revisao_id)
    assert pendencia_atualizada is not None
    assert pendencia_atualizada["status"] == "resolvida"
    assert pendencia_atualizada["tempo_revisao_s"] == 3.45
