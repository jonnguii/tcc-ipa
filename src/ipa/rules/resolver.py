"""Módulo de resolução e casamento fuzzy de itens e clientes contra o catálogo do ERP.
Utiliza RapidFuzz para correspondência robusta contra ruídos, erros de digitação e variações.
"""
from __future__ import annotations

import logging
from typing import Any

from rapidfuzz import fuzz

from erp_sim.seed_data import CLIENTES as SEED_CLIENTES, PRODUTOS as SEED_PRODUTOS
from src.ipa.rules.normalizar import limpar_documento, normalizar_texto, padronizar_codigo_produto
from src.ipa.rules.validar import validar_documento
from src.ipa.schemas import ClienteInfo

logger = logging.getLogger(__name__)

# Limiares de confiança da regra de negócio
SCORE_MINIMO_AUTOMATICO = 85.0
SCORE_MINIMO_REVISAO = 70.0


def obter_catalogo_produtos() -> list[dict[str, Any]]:
    """Carrega o catálogo de produtos do banco de dados do ERP com fallback seguro para seed_data."""
    try:
        from erp_sim import repo
        produtos = repo.get_produtos()
        if produtos:
            return produtos
    except Exception as exc:
        logger.warning("Falha ao carregar produtos do ERP (%s). Usando semente local.", exc)
    return list(SEED_PRODUTOS)


def obter_catalogo_clientes() -> list[dict[str, Any]]:
    """Carrega clientes cadastrados no ERP com fallback seguro para seed_data."""
    try:
        from erp_sim import repo
        clientes = repo.get_clientes()
        if clientes:
            return clientes
    except Exception as exc:
        logger.warning("Falha ao carregar clientes do ERP (%s). Usando semente local.", exc)
    return list(SEED_CLIENTES)


def resolver_produto(
    termo: str,
    catalogo: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Casa o termo ou código informado contra o catálogo oficial de produtos do ERP.

    Status possíveis:
    - 'EXATO': Código padronizado idêntico ou descrição idêntica (Score 100).
    - 'FUZZY_ALTA': Alta similaridade >= 85 (apto para fluxo automático).
    - 'AMBIGUO': Similaridade limítrofe entre 70 e 84 (requer revisão humana).
    - 'NAO_ENCONTRADO': Similaridade < 70 ou nenhum correspondente.
    """
    if catalogo is None:
        catalogo = obter_catalogo_produtos()

    termo_str = str(termo or "").strip()
    if not termo_str:
        return {
            "termo_original": termo_str,
            "produto": None,
            "codigo": None,
            "score": 0.0,
            "status": "NAO_ENCONTRADO",
        }

    codigo_tentativa = padronizar_codigo_produto(termo_str)
    termo_norm = normalizar_texto(termo_str)

    # 1. Checagem Exata por Código
    for p in catalogo:
        if p.get("codigo") == codigo_tentativa:
            return {
                "termo_original": termo_str,
                "produto": p,
                "codigo": p["codigo"],
                "score": 100.0,
                "status": "EXATO",
            }

    # 2. Checagem Exata por Descrição Normalizada
    for p in catalogo:
        desc_norm = normalizar_texto(p.get("descricao", ""))
        if termo_norm == desc_norm and desc_norm:
            return {
                "termo_original": termo_str,
                "produto": p,
                "codigo": p["codigo"],
                "score": 100.0,
                "status": "EXATO",
            }

    # 3. Correspondência Fuzzy com RapidFuzz
    melhor_produto: dict[str, Any] | None = None
    melhor_score: float = 0.0

    for p in catalogo:
        cod = p.get("codigo", "")
        desc = p.get("descricao", "")
        candidatos = [
            normalizar_texto(cod),
            normalizar_texto(desc),
            normalizar_texto(f"{cod} {desc}"),
        ]

        # Calcula a melhor pontuação contra qualquer uma das variações do produto
        scores = [fuzz.token_sort_ratio(termo_norm, cand) for cand in candidatos if cand]
        if not scores:
            continue
        score_atual = max(scores)

        if score_atual > melhor_score:
            melhor_score = float(score_atual)
            melhor_produto = p

    # Classificação por limiar
    if melhor_score >= SCORE_MINIMO_AUTOMATICO and melhor_produto:
        status = "FUZZY_ALTA"
    elif melhor_score >= SCORE_MINIMO_REVISAO and melhor_produto:
        status = "AMBIGUO"
    else:
        status = "NAO_ENCONTRADO"
        melhor_produto = None

    return {
        "termo_original": termo_str,
        "produto": melhor_produto,
        "codigo": melhor_produto.get("codigo") if melhor_produto else None,
        "score": round(melhor_score, 2),
        "status": status,
    }


def resolver_cliente(
    cliente_info: ClienteInfo,
    clientes_cadastrados: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Identifica o cliente no ERP ou valida os requisitos de cadastro para cliente novo.

    Status possíveis:
    - 'CLIENTE_EXISTENTE': Cliente encontrado e validado no ERP.
    - 'CLIENTE_NOVO_VALIDO': Cliente novo com dados cadastrais e documento válidos.
    - 'CLIENTE_NOVO_INCOMPLETO': Cliente novo faltando nome, email ou com documento inválido.
    - 'CLIENTE_NAO_ENCONTRADO': Cliente não localizado e flag novo=False.
    """
    if clientes_cadastrados is None:
        clientes_cadastrados = obter_catalogo_clientes()

    # Cenário 1: Cliente já possui ID explícito
    if cliente_info.id:
        for c in clientes_cadastrados:
            if c.get("id") == cliente_info.id:
                return {
                    "cliente": c,
                    "cliente_id": c.get("id"),
                    "status": "CLIENTE_EXISTENTE",
                    "detalhes": f"Identificado pelo ID #{c.get('id')}",
                }

    # Cenário 2: Busca por Documento (CNPJ/CPF) limpo
    doc_limpo = limpar_documento(cliente_info.cnpj_cpf)
    if doc_limpo:
        for c in clientes_cadastrados:
            doc_c = limpar_documento(c.get("cnpj_cpf"))
            if doc_c and doc_c == doc_limpo:
                return {
                    "cliente": c,
                    "cliente_id": c.get("id"),
                    "status": "CLIENTE_EXISTENTE",
                    "detalhes": f"Identificado pelo documento {doc_limpo}",
                }

    # Cenário 3: Cliente Novo (precisa cadastrar)
    if cliente_info.novo:
        valido_doc, tipo_doc = validar_documento(cliente_info.cnpj_cpf)
        tem_nome = bool(cliente_info.nome and cliente_info.nome.strip())
        tem_email = bool(cliente_info.email and "@" in cliente_info.email)

        if not valido_doc or not tem_nome or not tem_email:
            motivos = []
            if not valido_doc:
                motivos.append(f"Documento fiscal {cliente_info.cnpj_cpf} inválido")
            if not tem_nome:
                motivos.append("Nome do cliente ausente")
            if not tem_email:
                motivos.append("E-mail do cliente ausente ou inválido")
            return {
                "cliente": None,
                "cliente_id": None,
                "status": "CLIENTE_NOVO_INCOMPLETO",
                "detalhes": "; ".join(motivos),
            }

        return {
            "cliente": {
                "nome": cliente_info.nome.strip(),
                "cnpj_cpf": doc_limpo,
                "email": cliente_info.email.strip(),
            },
            "cliente_id": None,
            "status": "CLIENTE_NOVO_VALIDO",
            "detalhes": f"Cliente novo válido ({tipo_doc}: {doc_limpo})",
        }

    return {
        "cliente": None,
        "cliente_id": None,
        "status": "CLIENTE_NAO_ENCONTRADO",
        "detalhes": "Cliente não localizado no ERP e flag de cliente novo não habilitada",
    }
