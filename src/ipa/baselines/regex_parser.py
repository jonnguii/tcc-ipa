"""Baseline determinístico baseado em Expressões Regulares (Regex) para extração de pedidos.
Simula a abordagem tradicional pré-IA utilizada em sistemas legados.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.ipa.schemas import ClienteInfo, ItemPedido, PedidoExtraido


def extrair_por_regex(caminho_arquivo: str | Path) -> PedidoExtraido:
    """Extrai informações estruturadas de um arquivo de texto utilizando regras rígidas de regex.
    Para arquivos não-texto (.pdf, .png), retorna estrutura vazia/padrão, evidenciando a limitação
    de parsers puramente determinísticos sem OCR ou visão computacional.
    """
    path = Path(caminho_arquivo)
    doc_id = path.stem

    # Se for binário (pdf/png), o parser regex tradicional não consegue processar diretamente
    if path.suffix.lower() != ".txt":
        return PedidoExtraido(
            ref_id=doc_id,
            cliente=ClienteInfo(nome=None, cnpj_cpf=None),
            data_entrega="2026-11-20",
            observacoes="Falha: formato binário não suportado por parser regex",
            itens=[],
        )

    texto = path.read_text(encoding="utf-8")

    # 1. Extração do Referência ID
    ref_match = re.search(r"(DOC-\d{4})", texto)
    ref_id = ref_match.group(1) if ref_match else doc_id

    # 2. Extração de CNPJ ou CPF
    cnpj_match = re.search(r"(?:cnpj|cpnj|doc)[\s:]*([0-9.\-/]{11,18})", texto, re.IGNORECASE)
    if not cnpj_match:
        cnpj_match = re.search(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b", texto)
    cnpj = cnpj_match.group(1).strip() if cnpj_match else None

    # 3. Extração do Nome do Cliente
    cliente_match = re.search(r"(?:cliente|cli|empresa)[\s:]+([^\n\r,()]+)", texto, re.IGNORECASE)
    cliente_nome = cliente_match.group(1).strip() if cliente_match else None

    # 4. Extração de Data de Entrega
    data_match = re.search(r"(\d{4}-\d{2}-\d{2})", texto)
    if not data_match:
        data_match_br = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto)
        if data_match_br:
            d, m, y = data_match_br.groups()
            data_entrega = f"{y}-{m}-{d}"
        else:
            data_entrega = "2026-11-20"
    else:
        data_entrega = data_match.group(1)

    # 5. Extração de Itens (ex: - 15x Produto 3 (P-003) ou 15x P-003)
    itens: list[ItemPedido] = []
    # Padrão 1: "- 15x Produto (P-001)"
    padrao_item_completo = re.finditer(r"-\s*(\d+(?:\.\d+)?)\s*x\s*.*?\((P-\d+)\)", texto, re.IGNORECASE)
    for m in padrao_item_completo:
        qtd = float(m.group(1))
        cod = m.group(2).upper()
        itens.append(ItemPedido(codigo=cod, quantidade=qtd))

    # Padrão 2 (fallback): "(\d+)x.*?(P-\d+)" se nenhum item foi pego no padrão 1
    if not itens:
        padrao_item_simples = re.finditer(r"(\d+(?:\.\d+)?)\s*x[^\n]*?(P-\d+)", texto, re.IGNORECASE)
        for m in padrao_item_simples:
            qtd = float(m.group(1))
            cod = m.group(2).upper()
            itens.append(ItemPedido(codigo=cod, quantidade=qtd))

    # 6. Observações (ex: "Observações: ...")
    obs_match = re.search(r"(?:observações|observacoes|obs)[\s:]*([^\n\r]+)", texto, re.IGNORECASE)
    observacoes = obs_match.group(1).strip() if obs_match else ""

    return PedidoExtraido(
        ref_id=ref_id,
        cliente=ClienteInfo(nome=cliente_nome, cnpj_cpf=cnpj),
        data_entrega=data_entrega,
        observacoes=observacoes,
        itens=itens,
    )
