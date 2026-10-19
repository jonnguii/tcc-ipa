"""Módulo central de métricas científicas de avaliação para o TCC-IPA.
Implementa cálculo exato de Precision, Recall, F1-Score por campo crítico
(cliente, data, itens e quantidades) e estatísticas descritivas (mediana, P90, desvio).
"""
from __future__ import annotations

import math
from typing import Any

from src.ipa.schemas import PedidoExtraido


def calcular_metricas_itens(itens_pred: list[dict[str, Any]], itens_gold: list[dict[str, Any]]) -> dict[str, float]:
    """Calcula Precision, Recall e F1 para conjuntos de itens considerando (código, quantidade)."""
    set_pred = {(it["codigo"], float(it["quantidade"])) for it in itens_pred}
    set_gold = {(it["codigo"], float(it["quantidade"])) for it in itens_gold}

    if not set_gold and not set_pred:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not set_gold and set_pred:
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0}
    if set_gold and not set_pred:
        return {"precision": 1.0, "recall": 0.0, "f1": 0.0}

    tp = len(set_pred.intersection(set_gold))
    fp = len(set_pred - set_gold)
    fn = len(set_gold - set_pred)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def avaliar_campos_criticos(
    pedido_pred: PedidoExtraido | dict[str, Any],
    gabarito_gold: dict[str, Any],
) -> dict[str, Any]:
    """Compara campo a campo a predição contra o gabarito oficial do pedido_verdade."""
    if isinstance(pedido_pred, PedidoExtraido):
        pred_dict = pedido_pred.model_dump()
    else:
        pred_dict = pedido_pred

    gold_pedido = gabarito_gold.get("pedido_verdade", {})

    # 1. Avaliação do Cliente
    # Confere por ID se ambos tiverem, ou por CNPJ
    gold_cli = gold_pedido.get("cliente", {})
    pred_cli = pred_dict.get("cliente", {})

    acerto_cliente = False
    if gold_cli.get("id") is not None and pred_cli.get("id") is not None:
        acerto_cliente = (gold_cli["id"] == pred_cli["id"])
    elif gold_cli.get("cnpj_cpf") and pred_cli.get("cnpj_cpf"):
        # Limpa pontuação
        doc_gold = "".join(filter(str.isdigit, str(gold_cli["cnpj_cpf"])))
        doc_pred = "".join(filter(str.isdigit, str(pred_cli["cnpj_cpf"])))
        acerto_cliente = (doc_gold == doc_pred and bool(doc_gold))
    elif gold_cli.get("id") is None and gold_cli.get("cnpj_cpf") is None:
        # Caso em que cliente não tinha documento (cliente incompleto ou não-pedido)
        acerto_cliente = (pred_cli.get("id") is None and (not pred_cli.get("cnpj_cpf") or pred_cli.get("cnpj_cpf") == "Não informado"))

    # 2. Avaliação da Data
    gold_data = str(gold_pedido.get("data_entrega") or "").strip()
    pred_data = str(pred_dict.get("data_entrega") or "").strip()
    acerto_data = (gold_data == pred_data)

    # 3. Avaliação dos Itens
    gold_itens = gold_pedido.get("itens", [])
    pred_itens = pred_dict.get("itens", [])
    metricas_itens = calcular_metricas_itens(pred_itens, gold_itens)

    # Todos os campos críticos acertados com exatidão?
    acerto_completo = (acerto_cliente and acerto_data and metricas_itens["f1"] == 1.0)

    return {
        "acerto_cliente": acerto_cliente,
        "acerto_data": acerto_data,
        "itens_precision": metricas_itens["precision"],
        "itens_recall": metricas_itens["recall"],
        "itens_f1": metricas_itens["f1"],
        "acerto_completo": acerto_completo,
    }


def estatisticas_resumo(valores: list[float]) -> dict[str, float]:
    """Calcula estatísticas descritivas (média, mediana, p90, desvio padrão)."""
    if not valores:
        return {"media": 0.0, "mediana": 0.0, "p90": 0.0, "desvio": 0.0}

    ordenados = sorted(valores)
    n = len(ordenados)
    media = sum(ordenados) / n

    # Mediana
    if n % 2 == 1:
        mediana = ordenados[n // 2]
    else:
        mediana = (ordenados[n // 2 - 1] + ordenados[n // 2]) / 2.0

    # Percentil 90
    idx_p90 = max(0, min(n - 1, int(math.ceil(0.90 * n)) - 1))
    p90 = ordenados[idx_p90]

    # Desvio padrão
    variancia = sum((x - media) ** 2 for x in ordenados) / n if n > 1 else 0.0
    desvio = math.sqrt(variancia)

    return {
        "media": round(media, 4),
        "mediana": round(mediana, 4),
        "p90": round(p90, 4),
        "desvio": round(desvio, 4),
    }
