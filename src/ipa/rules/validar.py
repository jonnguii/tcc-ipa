"""Módulo de validação de documentos fiscais (CPF/CNPJ), datas e integridade do pedido.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

from src.ipa.rules.normalizar import limpar_documento


def validar_cpf(cpf_raw: str | None) -> bool:
    """Valida número de CPF conforme cálculo oficial dos dois dígitos verificadores."""
    cpf = limpar_documento(cpf_raw)
    if len(cpf) != 11:
        return False
    # Rejeita sequências com todos os dígitos iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False

    # Primeiro dígito
    soma_1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto_1 = (soma_1 * 10) % 11
    d1 = 0 if resto_1 == 10 else resto_1
    if int(cpf[9]) != d1:
        return False

    # Segundo dígito
    soma_2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto_2 = (soma_2 * 10) % 11
    d2 = 0 if resto_2 == 10 else resto_2
    return int(cpf[10]) == d2


def validar_cnpj(cnpj_raw: str | None) -> bool:
    """Valida número de CNPJ conforme cálculo oficial dos dois dígitos verificadores."""
    cnpj = limpar_documento(cnpj_raw)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_1 = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
    resto_1 = soma_1 % 11
    d1 = 0 if resto_1 < 2 else 11 - resto_1
    if int(cnpj[12]) != d1:
        return False

    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_2 = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
    resto_2 = soma_2 % 11
    d2 = 0 if resto_2 < 2 else 11 - resto_2
    return int(cnpj[13]) == d2


def validar_documento(doc_raw: str | None) -> tuple[bool, str]:
    """Identifica se é CPF ou CNPJ e retorna (eh_valido, tipo_doc)."""
    digitos = limpar_documento(doc_raw)
    if len(digitos) == 11:
        return validar_cpf(digitos), "CPF"
    if len(digitos) == 14:
        return validar_cnpj(digitos), "CNPJ"
    return False, "INVALIDO"


def validar_data_iso(data_str: str | None) -> bool:
    """Verifica se a string é uma data no formato ISO YYYY-MM-DD válida no calendário."""
    if not data_str or not isinstance(data_str, str):
        return False
    try:
        date.fromisoformat(data_str.strip())
        return True
    except (ValueError, TypeError):
        return False


def data_entrega_retroativa(data_str: str | None, hoje: date | None = None) -> bool:
    """Retorna True se a data de entrega informada for anterior à data de referência (hoje)."""
    if not validar_data_iso(data_str):
        return False
    hoje = hoje or date.today()
    try:
        data_pedido = date.fromisoformat(data_str.strip())
        return data_pedido < hoje
    except Exception:
        return False


def validar_quantidade(quantidade: Any) -> bool:
    """Valida se a quantidade é um número positivo e finito."""
    if isinstance(quantidade, bool):
        return False
    try:
        qtd = float(quantidade)
        return math.isfinite(qtd) and qtd > 0
    except (ValueError, TypeError):
        return False
