"""Módulo do Motor de Regras e Roteamento do TCC-IPA."""
from src.ipa.rules.normalizar import (
    limpar_documento,
    normalizar_quantidade,
    normalizar_texto,
    padronizar_codigo_produto,
    remover_acentos,
)
from src.ipa.rules.resolver import (
    SCORE_MINIMO_AUTOMATICO,
    SCORE_MINIMO_REVISAO,
    obter_catalogo_clientes,
    obter_catalogo_produtos,
    resolver_cliente,
    resolver_produto,
)
from src.ipa.rules.rotear import (
    DecisaoRoteamento,
    ItemRoteado,
    ResultadoRoteamento,
    rotear_pedido,
)
from src.ipa.rules.validar import (
    data_entrega_retroativa,
    validar_cnpj,
    validar_cpf,
    validar_data_iso,
    validar_documento,
    validar_quantidade,
)

__all__ = [
    "remover_acentos",
    "normalizar_texto",
    "limpar_documento",
    "padronizar_codigo_produto",
    "normalizar_quantidade",
    "validar_cpf",
    "validar_cnpj",
    "validar_documento",
    "validar_data_iso",
    "data_entrega_retroativa",
    "validar_quantidade",
    "obter_catalogo_produtos",
    "obter_catalogo_clientes",
    "resolver_produto",
    "resolver_cliente",
    "SCORE_MINIMO_AUTOMATICO",
    "SCORE_MINIMO_REVISAO",
    "DecisaoRoteamento",
    "ItemRoteado",
    "ResultadoRoteamento",
    "rotear_pedido",
]
