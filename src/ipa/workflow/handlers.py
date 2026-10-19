"""Handlers (manipuladores) de execução para cada estágio da máquina de estados do workflow.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.ipa.ai.extractor import processar_documento
from src.ipa.contracts import ExecutorPedido
from src.ipa.metrics.eventos import CronometroEtapa, EventoEtapa
from src.ipa.rules import ResultadoRoteamento, rotear_pedido
from src.ipa.schemas import PedidoExtraido

logger = logging.getLogger(__name__)


def handler_extracao_ia(caminho_doc: str | Path) -> tuple[PedidoExtraido, EventoEtapa]:
    """Estágio 1: Extração inteligente via Gemini Flash com cronometragem."""
    caminho = Path(caminho_doc)
    with CronometroEtapa("EXTRACAO_IA") as crono:
        pedido_extraido = processar_documento(str(caminho))
        crono.detalhes["arquivo"] = caminho.name
        crono.detalhes["tipo_arquivo"] = caminho.suffix.lower().lstrip(".")
        crono.detalhes["itens_extraidos"] = len(pedido_extraido.itens)

    return pedido_extraido, crono.to_evento()


def handler_regras_triagem(
    pedido: PedidoExtraido,
    catalogo_produtos: list[dict[str, Any]] | None = None,
    clientes_cadastrados: list[dict[str, Any]] | None = None,
) -> tuple[ResultadoRoteamento, EventoEtapa]:
    """Estágio 2: Normalização, validação fiscal, RapidFuzz e triagem determinística."""
    with CronometroEtapa("REGRAS_TRIAGEM") as crono:
        resultado = rotear_pedido(
            pedido,
            catalogo_produtos=catalogo_produtos,
            clientes_cadastrados=clientes_cadastrados,
        )
        crono.detalhes["decisao"] = resultado.decisao.value
        crono.detalhes["confianca"] = resultado.confianca_geral
        crono.detalhes["motivos"] = resultado.motivos

    return resultado, crono.to_evento()


def handler_execucao_pedido(
    pedido_pronto: PedidoExtraido,
    executor: ExecutorPedido,
) -> tuple[dict[str, Any], EventoEtapa]:
    """Estágio 3: Despacho do pedido aprovado para o executor (Stub ou RPA)."""
    with CronometroEtapa("EXECUTOR_RPA") as crono:
        payload_exec = {
            "ref_id": pedido_pronto.ref_id,
            "cliente": {
                "id": pedido_pronto.cliente.id,
                "novo": pedido_pronto.cliente.novo,
                "nome": pedido_pronto.cliente.nome,
                "cnpj_cpf": pedido_pronto.cliente.cnpj_cpf,
                "email": pedido_pronto.cliente.email,
            },
            "data_entrega": pedido_pronto.data_entrega,
            "observacoes": pedido_pronto.observacoes,
            "itens": [
                {"codigo": it.codigo, "quantidade": it.quantidade}
                for it in pedido_pronto.itens
            ],
        }
        resultado_exec = executor.executar(payload_exec)
        crono.detalhes.update(resultado_exec)
        if resultado_exec.get("status") == "erro":
            crono.resultado = "ERRO"

    return resultado_exec, crono.to_evento()


def handler_revisao_pendencia(
    pedido: PedidoExtraido,
    resultado_roteamento: ResultadoRoteamento,
    caminho_doc: str | Path | None = None,
) -> tuple[dict[str, Any], EventoEtapa]:
    """Estágio 4: Registro de pendência na fila de revisão humana (Fase 9)."""
    from src.ipa.review.fila import inserir_pendencia

    with CronometroEtapa("REVISAO_HUMANA") as crono:
        payload_dados = {
            "ref_id": pedido.ref_id,
            "pedido_original": pedido.model_dump(),
            "itens_analisados": [it.model_dump() for it in resultado_roteamento.itens_roteados],
            "documento": str(caminho_doc) if caminho_doc else None,
        }
        
        registro = inserir_pendencia(
            payload=payload_dados,
            motivos=resultado_roteamento.motivos,
            tipo="REVISAO",
            caminho_doc=str(caminho_doc) if caminho_doc else None,
        )

        pendencia = {
            "revisao_id": registro.get("id"),
            "ref_id": pedido.ref_id,
            "status": "pendente",
            "motivos": resultado_roteamento.motivos,
            "documento": str(caminho_doc) if caminho_doc else None,
            "pedido_original": pedido.model_dump(),
            "itens_analisados": [it.model_dump() for it in resultado_roteamento.itens_roteados],
        }
        crono.detalhes["revisao_id"] = registro.get("id")
        crono.detalhes["ref_id"] = pedido.ref_id
        crono.detalhes["total_motivos"] = len(resultado_roteamento.motivos)

    return pendencia, crono.to_evento()
