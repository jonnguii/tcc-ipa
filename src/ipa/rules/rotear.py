"""Módulo de roteamento determinístico para triagem de pedidos.
Decide se o pedido segue para AUTOMATICO (RPA), REVISAO (humana) ou REJEICAO (descarte).
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.ipa.rules.normalizar import normalizar_quantidade, normalizar_texto
from src.ipa.rules.resolver import (
    SCORE_MINIMO_AUTOMATICO,
    resolver_cliente,
    resolver_produto,
)
from src.ipa.rules.validar import (
    data_entrega_retroativa,
    validar_data_iso,
    validar_quantidade,
)
from src.ipa.schemas import ClienteInfo, ItemPedido, PedidoExtraido


class DecisaoRoteamento(str, Enum):
    AUTOMATICO = "AUTOMATICO"
    REVISAO = "REVISAO"
    REJEICAO = "REJEICAO"


class ItemRoteado(BaseModel):
    termo_original: str
    codigo_resolvido: str | None = None
    descricao_resolvida: str | None = None
    quantidade: float
    score_fuzzy: float = 0.0
    status_resolucao: str = "NAO_ENCONTRADO"


class ResultadoRoteamento(BaseModel):
    decisao: DecisaoRoteamento
    motivos: list[str] = Field(default_factory=list)
    pedido_pronto: PedidoExtraido | None = None
    itens_roteados: list[ItemRoteado] = Field(default_factory=list)
    dados_cliente: dict[str, Any] | None = None
    confianca_geral: float = 1.0


# Padrões comumente associados a injeção adversarial ou ruído malicioso
PADROES_ADVERSARIAIS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*:\s*you\s+are",
    r"drop\s+table",
    r"<\s*script[^>]*>",
    r"prompt\s+injection",
]


def detectar_conteudo_adversarial(texto: str | None) -> bool:
    """Verifica se há tentativa flagrante de manipulação ou script injection no texto."""
    if not texto:
        return False
    texto_min = texto.lower()
    for padrao in PADROES_ADVERSARIAIS:
        if re.search(padrao, texto_min):
            return True
    return False


def rotear_pedido(
    pedido: PedidoExtraido,
    catalogo_produtos: list[dict[str, Any]] | None = None,
    clientes_cadastrados: list[dict[str, Any]] | None = None,
    ignorar_data_retroativa: bool = False,
) -> ResultadoRoteamento:
    """Analisa o PedidoExtraido através da malha de regras e define o roteamento determinístico."""
    motivos_rejeicao: list[str] = []
    motivos_revisao: list[str] = []

    # 1. Checagem Anti-Injeção e Fraude
    obs = pedido.observacoes or ""
    if detectar_conteudo_adversarial(obs):
        motivos_rejeicao.append("Conteúdo adversarial ou instrução não autorizada detectada nas observações")

    for item in pedido.itens or []:
        if detectar_conteudo_adversarial(item.codigo):
            motivos_rejeicao.append(f"Conteúdo malicioso detectado no código do item: '{item.codigo}'")

    # 2. Integridade Estrutural Mínima
    if not pedido.itens or len(pedido.itens) == 0:
        motivos_rejeicao.append("Pedido não possui itens informados")
        return ResultadoRoteamento(
            decisao=DecisaoRoteamento.REJEICAO,
            motivos=motivos_rejeicao,
            confianca_geral=0.0,
        )

    # 3. Validação do Cliente
    res_cliente = resolver_cliente(pedido.cliente, clientes_cadastrados=clientes_cadastrados)
    status_cli = res_cliente["status"]

    if status_cli == "CLIENTE_NOVO_INCOMPLETO":
        motivos_revisao.append(f"Cliente novo com pendências cadastrais: {res_cliente['detalhes']}")
    elif status_cli == "CLIENTE_NAO_ENCONTRADO":
        motivos_revisao.append("Cliente não localizado no ERP e não sinalizado como novo")

    # 4. Validação de Data de Entrega
    if not validar_data_iso(pedido.data_entrega):
        motivos_revisao.append(f"Data de entrega '{pedido.data_entrega}' possui formato ou calendário inválido")
    elif not ignorar_data_retroativa and data_entrega_retroativa(pedido.data_entrega):
        motivos_revisao.append(f"Data de entrega '{pedido.data_entrega}' é anterior à data de processamento")

    # 5. Resolução e Validação dos Itens
    itens_resolvidos_prontos: list[ItemPedido] = []
    itens_roteados: list[ItemRoteado] = []
    scores_fuzzy: list[float] = []

    for idx, item in enumerate(pedido.itens, start=1):
        # Validação de Quantidade
        if not validar_quantidade(item.quantidade):
            motivos_revisao.append(f"Item #{idx} ({item.codigo}): quantidade inválida '{item.quantidade}'")
            qtd_normalizada = 0.0
        else:
            qtd_normalizada = normalizar_quantidade(item.quantidade)

        # Resolução Fuzzy de Catálogo
        res_prod = resolver_produto(item.codigo, catalogo=catalogo_produtos)
        status_prod = res_prod["status"]
        score_prod = res_prod["score"]
        codigo_final = res_prod["codigo"]
        prod_obj = res_prod["produto"]
        scores_fuzzy.append(score_prod)

        item_rot = ItemRoteado(
            termo_original=item.codigo,
            codigo_resolvido=codigo_final,
            descricao_resolvida=prod_obj.get("descricao") if prod_obj else None,
            quantidade=qtd_normalizada,
            score_fuzzy=score_prod,
            status_resolucao=status_prod,
        )
        itens_roteados.append(item_rot)

        if status_prod == "NAO_ENCONTRADO":
            motivos_revisao.append(f"Item #{idx}: produto '{item.codigo}' não encontrado no catálogo do ERP")
        elif status_prod == "AMBIGUO":
            motivos_revisao.append(
                f"Item #{idx}: produto '{item.codigo}' com similaridade ambígua ({score_prod}%) para '{codigo_final}'"
            )
        elif status_prod in ("EXATO", "FUZZY_ALTA"):
            if codigo_final and qtd_normalizada > 0:
                itens_resolvidos_prontos.append(
                    ItemPedido(codigo=codigo_final, quantidade=qtd_normalizada)
                )

    # Cálculo da confiança geral média dos itens
    confianca_geral = (
        round(sum(scores_fuzzy) / (len(scores_fuzzy) * 100.0), 2)
        if scores_fuzzy
        else 0.0
    )

    # 6. Decisão Final da Matriz de Roteamento
    if motivos_rejeicao:
        return ResultadoRoteamento(
            decisao=DecisaoRoteamento.REJEICAO,
            motivos=motivos_rejeicao + motivos_revisao,
            itens_roteados=itens_roteados,
            dados_cliente=res_cliente.get("cliente"),
            confianca_geral=confianca_geral,
        )

    if motivos_revisao:
        return ResultadoRoteamento(
            decisao=DecisaoRoteamento.REVISAO,
            motivos=motivos_revisao,
            itens_roteados=itens_roteados,
            dados_cliente=res_cliente.get("cliente"),
            confianca_geral=confianca_geral,
        )

    # Fluxo AUTOMÁTICO garantido: monta objeto pronto e higienizado para o robô RPA
    cliente_pronto = ClienteInfo(
        id=res_cliente.get("cliente_id"),
        novo=(res_cliente["status"] == "CLIENTE_NOVO_VALIDO"),
        nome=res_cliente.get("cliente", {}).get("nome"),
        cnpj_cpf=res_cliente.get("cliente", {}).get("cnpj_cpf"),
        email=res_cliente.get("cliente", {}).get("email"),
    )

    pedido_pronto = PedidoExtraido(
        ref_id=pedido.ref_id.strip(),
        cliente=cliente_pronto,
        data_entrega=pedido.data_entrega.strip(),
        observacoes=normalizar_texto(pedido.observacoes or ""),
        itens=itens_resolvidos_prontos,
    )

    return ResultadoRoteamento(
        decisao=DecisaoRoteamento.AUTOMATICO,
        motivos=[],
        pedido_pronto=pedido_pronto,
        itens_roteados=itens_roteados,
        dados_cliente=res_cliente.get("cliente"),
        confianca_geral=confianca_geral,
    )
