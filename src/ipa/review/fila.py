"""Gerenciador da Fila de Revisão Humana (Fase 9).

Responsável por persistir, consultar e atualizar os pedidos retidos
na triagem para validação humana ('Human-in-the-Loop').
Integra diretamente com a tabela `ipa_revisoes` do Supabase com fallback local.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ipa.config import settings

logger = logging.getLogger(__name__)

# Fallback local em memória/disco se Supabase estiver inacessível
_FALLBACK_FILE = Path("data/revisoes_local.json")
_memoria_revisoes: list[dict[str, Any]] = []


def _obter_cliente_supabase():
    try:
        from supabase import Client, create_client
        if settings.supabase_url and settings.supabase_service_key:
            return create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as exc:
        logger.warning("Falha ao inicializar cliente Supabase: %s", exc)
    return None


def _carregar_fallback_local() -> list[dict[str, Any]]:
    global _memoria_revisoes
    if _FALLBACK_FILE.exists():
        try:
            dados = json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
            if isinstance(dados, list):
                _memoria_revisoes = dados
        except Exception:
            pass
    return _memoria_revisoes


def _salvar_fallback_local():
    try:
        _FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        _FALLBACK_FILE.write_text(
            json.dumps(_memoria_revisoes, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Erro ao salvar fallback local de revisões: %s", exc)


def inserir_pendencia(
    payload: dict[str, Any],
    motivos: list[str] | str,
    execucao_id: int | None = None,
    tipo: str = "REVISAO",
    caminho_doc: str | None = None,
    simulada: bool = False,
) -> dict[str, Any]:
    """Registra uma nova pendência na fila de revisão humana."""
    motivo_str = "; ".join(motivos) if isinstance(motivos, list) else str(motivos)
    
    # Se fornecido o caminho do arquivo, enriquecer payload com texto original se disponível
    payload_completo = dict(payload)
    if caminho_doc:
        payload_completo["_caminho_doc"] = caminho_doc
        doc_path = Path(caminho_doc)
        if doc_path.exists() and doc_path.suffix.lower() == ".txt":
            try:
                payload_completo["_conteudo_bruto"] = doc_path.read_text(encoding="utf-8")
            except Exception:
                pass

    dados_registro = {
        "execucao_id": execucao_id,
        "tipo": tipo,
        "motivo": motivo_str,
        "payload": payload_completo,
        "status": "pendente",
        "correcao": None,
        "simulada": simulada,
        "tempo_revisao_s": None,
    }

    client = _obter_cliente_supabase()
    if client:
        try:
            resposta = client.table("ipa_revisoes").insert(dados_registro).execute()
            if resposta.data:
                logger.info("Pendência registrada no Supabase com ID: %s", resposta.data[0].get("id"))
                return resposta.data[0]
        except Exception as exc:
            logger.warning("Falha ao salvar no Supabase, usando fallback local: %s", exc)

    # Fallback local
    _carregar_fallback_local()
    novo_id = len(_memoria_revisoes) + 1
    registro = {
        "id": novo_id,
        **dados_registro,
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    _memoria_revisoes.append(registro)
    _salvar_fallback_local()
    logger.info("Pendência registrada no fallback local com ID: %s", novo_id)
    return registro


def listar_pendencias(status: str | None = "pendente") -> list[dict[str, Any]]:
    """Lista as revisões cadastradas, com filtro opcional por status."""
    client = _obter_cliente_supabase()
    if client:
        try:
            query = client.table("ipa_revisoes").select("*").order("id", desc=True)
            if status:
                query = query.eq("status", status)
            resposta = query.execute()
            if resposta.data is not None:
                return resposta.data
        except Exception as exc:
            logger.warning("Falha ao listar do Supabase, lendo fallback local: %s", exc)

    # Fallback local
    _carregar_fallback_local()
    if status:
        return [r for r in _memoria_revisoes if r.get("status") == status]
    return list(_memoria_revisoes)


def obter_pendencia(revisao_id: int) -> dict[str, Any] | None:
    """Obtém uma pendência específica por ID."""
    client = _obter_cliente_supabase()
    if client:
        try:
            resposta = client.table("ipa_revisoes").select("*").eq("id", revisao_id).execute()
            if resposta.data:
                return resposta.data[0]
        except Exception as exc:
            logger.warning("Falha ao buscar pendência %s no Supabase: %s", revisao_id, exc)

    # Fallback local
    _carregar_fallback_local()
    for item in _memoria_revisoes:
        if item.get("id") == revisao_id:
            return item
    return None


def resolver_pendencia(
    revisao_id: int,
    status: str,  # 'resolvida' | 'rejeitada'
    correcao: dict[str, Any] | None = None,
    tempo_revisao_s: float | None = None,
) -> dict[str, Any] | None:
    """Atualiza a pendência como resolvida ou rejeitada com os dados corrigidos."""
    campos_atualizacao: dict[str, Any] = {
        "status": status,
        "correcao": correcao,
        "tempo_revisao_s": round(tempo_revisao_s, 3) if tempo_revisao_s is not None else None,
    }

    client = _obter_cliente_supabase()
    if client:
        try:
            # Trava atômica (optimistic lock): só atualiza se ainda estiver pendente
            resposta = (
                client.table("ipa_revisoes")
                .update(campos_atualizacao)
                .eq("id", revisao_id)
                .eq("status", "pendente")
                .execute()
            )
            if resposta.data:
                logger.info("Pendência %s resolvida no Supabase com status %s", revisao_id, status)
                return resposta.data[0]
            else:
                logger.warning("Pendência %s já havia sido resolvida por outro operador (concorrência bloqueada)", revisao_id)
                return None
        except Exception as exc:
            logger.warning("Falha ao atualizar pendência %s no Supabase: %s", revisao_id, exc)

    # Fallback local com controle de concorrência
    _carregar_fallback_local()
    for item in _memoria_revisoes:
        if item.get("id") == revisao_id:
            if item.get("status") != "pendente":
                logger.warning("Pendência %s já resolvida no fallback local", revisao_id)
                return None
            item.update(campos_atualizacao)
            _salvar_fallback_local()
            return item

    return None
