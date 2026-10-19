"""Motor central de orquestração do workflow (Máquina de Estados Executável).
Espelha o diagrama BPMN TO-BE e orquestra IA, Regras, Execução e Métricas.
"""
from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.ipa.contracts import ExecutorPedido
from src.ipa.executor import obter_executor
from src.ipa.metrics.eventos import EventoEtapa, RelatorioMetricasExecucao
from src.ipa.rules import DecisaoRoteamento, ResultadoRoteamento
from src.ipa.schemas import PedidoExtraido
from src.ipa.workflow.estados import EstadoWorkflow, validar_transicao
from src.ipa.workflow.handlers import (
    handler_execucao_pedido,
    handler_extracao_ia,
    handler_regras_triagem,
    handler_revisao_pendencia,
)

logger = logging.getLogger(__name__)


class ResultadoExecucaoWorkflow(BaseModel):
    """Resultado detalhado do processamento completo de um documento."""

    run_id: str
    doc_id: str
    caminho_documento: str
    estado_final: EstadoWorkflow
    decisao_roteamento: str | None = None
    resultado_executor: dict[str, Any] | None = None
    pendencia_revisao: dict[str, Any] | None = None
    pedido_processado: PedidoExtraido | None = None
    eventos: list[EventoEtapa] = Field(default_factory=list)
    tempo_total_s: float = 0.0
    erro: str | None = None


class OrquestradorIPA:
    """Orquestrador que gerencia o ciclo de vida e a transição da máquina de estados."""

    def __init__(
        self,
        tipo_executor: str = "stub",
        executor_customizado: ExecutorPedido | None = None,
        catalogo_produtos: list[dict[str, Any]] | None = None,
        clientes_cadastrados: list[dict[str, Any]] | None = None,
        executor: ExecutorPedido | str | None = None,
    ) -> None:
        if isinstance(executor, str):
            tipo_executor = executor
        elif executor is not None:
            executor_customizado = executor

        self.tipo_executor = tipo_executor
        self.executor = executor_customizado or obter_executor(tipo=tipo_executor)
        self.catalogo_produtos = catalogo_produtos
        self.clientes_cadastrados = clientes_cadastrados

    def processar_documento(self, caminho_doc: str | Path) -> ResultadoExecucaoWorkflow:
        """Executa a máquina de estados completa para um único documento."""
        caminho = Path(caminho_doc)
        doc_id = caminho.stem
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        inicio_total = time.perf_counter()

        estado_atual = EstadoWorkflow.INICIADO
        eventos: list[EventoEtapa] = []

        resultado_roteamento: ResultadoRoteamento | None = None
        resultado_executor: dict[str, Any] | None = None
        pendencia_revisao: dict[str, Any] | None = None
        pedido_extraido: PedidoExtraido | None = None

        try:
            # ---------------------------------------------------------------
            # Transição 1: INICIADO -> EXTRACAO_IA
            # ---------------------------------------------------------------
            if not validar_transicao(estado_atual, EstadoWorkflow.EXTRACAO_IA):
                raise RuntimeError(f"Transição inválida de {estado_atual} para EXTRACAO_IA")
            estado_atual = EstadoWorkflow.EXTRACAO_IA

            pedido_extraido, ev_ia = handler_extracao_ia(caminho)
            eventos.append(ev_ia)

            # ---------------------------------------------------------------
            # Transição 2: EXTRACAO_IA -> REGRAS_TRIAGEM
            # ---------------------------------------------------------------
            if not validar_transicao(estado_atual, EstadoWorkflow.REGRAS_TRIAGEM):
                raise RuntimeError(f"Transição inválida de {estado_atual} para REGRAS_TRIAGEM")
            estado_atual = EstadoWorkflow.REGRAS_TRIAGEM

            resultado_roteamento, ev_regras = handler_regras_triagem(
                pedido_extraido,
                catalogo_produtos=self.catalogo_produtos,
                clientes_cadastrados=self.clientes_cadastrados,
            )
            eventos.append(ev_regras)

            # ---------------------------------------------------------------
            # Transição 3: Decisão do Gateway BPMN (3 Vias)
            # ---------------------------------------------------------------
            decisao = resultado_roteamento.decisao

            if decisao == DecisaoRoteamento.AUTOMATICO:
                # Via Verde: Despacho direto ao Executor (Stub ou RPA)
                if not validar_transicao(estado_atual, EstadoWorkflow.EXECUTOR_RPA):
                    raise RuntimeError(f"Transição inválida de {estado_atual} para EXECUTOR_RPA")
                estado_atual = EstadoWorkflow.EXECUTOR_RPA

                pedido_pronto = resultado_roteamento.pedido_pronto or pedido_extraido
                resultado_executor, ev_exec = handler_execucao_pedido(pedido_pronto, self.executor)
                eventos.append(ev_exec)

                estado_atual = (
                    EstadoWorkflow.CONCLUIDO
                    if resultado_executor.get("status") in ("sucesso", "duplicado")
                    else EstadoWorkflow.FALHA
                )

            elif decisao == DecisaoRoteamento.REVISAO:
                # Via Amarela: Fila de Revisão Humana
                if not validar_transicao(estado_atual, EstadoWorkflow.REVISAO_HUMANA):
                    raise RuntimeError(f"Transição inválida de {estado_atual} para REVISAO_HUMANA")
                estado_atual = EstadoWorkflow.REVISAO_HUMANA

                pendencia_revisao, ev_rev = handler_revisao_pendencia(
                    pedido_extraido, resultado_roteamento, caminho_doc=caminho
                )
                eventos.append(ev_rev)

            elif decisao == DecisaoRoteamento.REJEICAO:
                # Via Vermelha: Descarte / Auditoria
                if not validar_transicao(estado_atual, EstadoWorkflow.REJEITADO):
                    raise RuntimeError(f"Transição inválida de {estado_atual} para REJEITADO")
                estado_atual = EstadoWorkflow.REJEITADO

        except Exception as exc:
            logger.exception("Falha durante o workflow do documento %s: %s", doc_id, exc)
            estado_atual = EstadoWorkflow.FALHA
            tempo_total = round(time.perf_counter() - inicio_total, 4)
            return ResultadoExecucaoWorkflow(
                run_id=run_id,
                doc_id=doc_id,
                caminho_documento=str(caminho),
                estado_final=estado_atual,
                decisao_roteamento=resultado_roteamento.decisao.value if resultado_roteamento else None,
                eventos=eventos,
                tempo_total_s=tempo_total,
                erro=str(exc),
            )

        tempo_total = round(time.perf_counter() - inicio_total, 4)
        return ResultadoExecucaoWorkflow(
            run_id=run_id,
            doc_id=doc_id,
            caminho_documento=str(caminho),
            estado_final=estado_atual,
            decisao_roteamento=resultado_roteamento.decisao.value if resultado_roteamento else None,
            resultado_executor=resultado_executor,
            pendencia_revisao=pendencia_revisao,
            pedido_processado=pedido_extraido,
            eventos=eventos,
            tempo_total_s=tempo_total,
            erro=None,
        )

    def processar_lote(
        self,
        caminhos: list[str | Path],
    ) -> list[ResultadoExecucaoWorkflow]:
        """Processa uma lista sequencial de documentos."""
        resultados: list[ResultadoExecucaoWorkflow] = []
        for caminho in caminhos:
            res = self.processar_documento(caminho)
            resultados.append(res)
        return resultados

    def retomar_apos_revisao(
        self,
        revisao_id: int,
        acao: str,  # 'aprovar' | 'rejeitar'
        pedido_corrigido: PedidoExtraido | dict[str, Any] | None = None,
        tempo_revisao_s: float | None = None,
    ) -> ResultadoExecucaoWorkflow:
        """Retoma o ciclo de vida de um pedido após deliberação de um operador humano (Fase 9).
        
        Espelha o fluxo BPMN:
        - Se aprovado: REVISAO_HUMANA -> EXECUTOR_RPA -> CONCLUIDO
        - Se rejeitado: REVISAO_HUMANA -> REJEITADO
        """
        import uuid
        from src.ipa.metrics.eventos import CronometroEtapa
        from src.ipa.review.fila import obter_pendencia, resolver_pendencia

        inicio_total = time.perf_counter()
        run_id = f"review-resume-{uuid.uuid4().hex[:8]}"
        eventos: list[EventoEtapa] = []

        pendencia = obter_pendencia(revisao_id)
        if not pendencia:
            raise ValueError(f"Pendência de revisão {revisao_id} não encontrada.")

        doc_caminho = pendencia.get("payload", {}).get("documento", "")
        doc_id = Path(doc_caminho).name if doc_caminho else f"revisao_{revisao_id}"
        estado_atual = EstadoWorkflow.REVISAO_HUMANA

        if acao.lower() == "rejeitar":
            if not validar_transicao(estado_atual, EstadoWorkflow.REJEITADO):
                raise RuntimeError(f"Transição inválida de {estado_atual} para REJEITADO")

            resolver_pendencia(
                revisao_id=revisao_id,
                status="rejeitada",
                correcao=None,
                tempo_revisao_s=tempo_revisao_s,
            )
            estado_atual = EstadoWorkflow.REJEITADO
            tempo_total = round(time.perf_counter() - inicio_total, 4)

            return ResultadoExecucaoWorkflow(
                run_id=run_id,
                doc_id=doc_id,
                caminho_documento=doc_caminho,
                estado_final=estado_atual,
                decisao_roteamento="REVISAO_REJEITADA",
                resultado_executor=None,
                pendencia_revisao=pendencia,
                pedido_processado=None,
                eventos=eventos,
                tempo_total_s=tempo_total,
                erro=None,
            )

        # Se aprovado / corrigido:
        if not validar_transicao(estado_atual, EstadoWorkflow.EXECUTOR_RPA):
            raise RuntimeError(f"Transição inválida de {estado_atual} para EXECUTOR_RPA")

        # Reconstruir o PedidoExtraido
        if isinstance(pedido_corrigido, PedidoExtraido):
            pedido_final = pedido_corrigido
        elif isinstance(pedido_corrigido, dict):
            pedido_final = PedidoExtraido.model_validate(pedido_corrigido)
        else:
            # Usa o original gravado no payload
            dados_originais = pendencia.get("payload", {}).get("pedido_original", {})
        # Garantir resolução cadastral do cliente antes do envio ao robô
        if pedido_final.cliente and not pedido_final.cliente.id:
            import re as _re
            from src.ipa.rules.resolver import resolver_cliente

            res_cli = resolver_cliente(pedido_final.cliente, clientes_cadastrados=self.clientes_cadastrados)
            if res_cli.get("cliente_id"):
                pedido_final.cliente.id = res_cli["cliente_id"]
            elif res_cli.get("status") == "CLIENTE_NOVO_VALIDO":
                pedido_final.cliente.novo = True
                pedido_final.cliente.email = (
                    res_cli.get("cliente", {}).get("email")
                    or pedido_final.cliente.email
                    or "contato@cliente.com"
                )
            else:
                pedido_final.cliente.novo = True
                if not pedido_final.cliente.email:
                    slug = _re.sub(r"[^a-zA-Z0-9]", "", (pedido_final.cliente.nome or "cliente").lower()) or "cliente"
                    pedido_final.cliente.email = f"contato@{slug}.com.br"

        estado_atual = EstadoWorkflow.EXECUTOR_RPA
        resultado_executor, ev_exec = handler_execucao_pedido(pedido_final, self.executor)
        eventos.append(ev_exec)

        correcao_registro = {
            "pedido": pedido_final.model_dump(),
            "numero_pedido": resultado_executor.get("numero_pedido"),
            "status_executor": resultado_executor.get("status"),
        }

        resolver_pendencia(
            revisao_id=revisao_id,
            status="resolvida",
            correcao=correcao_registro,
            tempo_revisao_s=tempo_revisao_s,
        )

        estado_atual = (
            EstadoWorkflow.CONCLUIDO
            if resultado_executor.get("status") in ("sucesso", "duplicado")
            else EstadoWorkflow.FALHA
        )

        tempo_total = round(time.perf_counter() - inicio_total, 4)
        return ResultadoExecucaoWorkflow(
            run_id=run_id,
            doc_id=doc_id,
            caminho_documento=doc_caminho,
            estado_final=estado_atual,
            decisao_roteamento="REVISAO_APROVADA",
            resultado_executor=resultado_executor,
            pendencia_revisao=pendencia,
            pedido_processado=pedido_final,
            eventos=eventos,
            tempo_total_s=tempo_total,
            erro=None,
        )
