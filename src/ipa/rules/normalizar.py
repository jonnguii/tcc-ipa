"""Módulo de normalização de textos, códigos e documentos para o motor de regras.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def remover_acentos(texto: str) -> str:
    """Remove caracteres diacríticos (acentos, cedilhas, tils) preservando a base."""
    if not texto:
        return ""
    forma_nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in forma_nfkd if not unicodedata.combining(c))


def normalizar_texto(texto: str) -> str:
    """Converte para caixa baixa, remove acentos, normaliza espaçamentos e pontuações excessivas."""
    if not texto:
        return ""
    sem_acentos = remover_acentos(texto).lower()
    # Substitui caracteres especiais redundantes por espaços, mantendo letras, números e hífens
    limpo = re.sub(r"[^\w\s\-]", " ", sem_acentos)
    # Colapsa múltiplos espaços em branco
    return re.sub(r"\s+", " ", limpo).strip()


def limpar_documento(doc: str | None) -> str:
    """Extrai estritamente os dígitos numéricos de um documento (CPF ou CNPJ)."""
    if not doc:
        return ""
    return re.sub(r"\D", "", str(doc))


def padronizar_codigo_produto(codigo: str | None) -> str:
    """Padroniza variações de código de produto (ex: 'p-1', 'p01', 'P 001') para o formato canônico 'P-001'."""
    if not codigo:
        return ""
    texto = codigo.strip().upper()
    padrao = re.match(r"^P[\s_-]?(\d{1,3})$", texto)
    if padrao:
        numero = int(padrao.group(1))
        return f"P-{numero:03d}"
    return texto


def normalizar_quantidade(quantidade: Any) -> float:
    """Converte quantidade para float positivo, tratando vírgulas decimais e strings."""
    if isinstance(quantidade, (int, float)):
        return float(quantidade)
    if isinstance(quantidade, str):
        # Trata formato com vírgula '3,5' -> '3.5'
        limpo = quantidade.strip().replace(",", ".")
        return float(limpo)
    raise ValueError(f"Quantidade inválida: {quantidade}")
