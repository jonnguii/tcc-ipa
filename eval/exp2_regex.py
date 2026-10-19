"""Script para o Experimento 2 (EXP2 - Comparação Regex Baseline vs IA).
Executa o parser determinístico regex em todo o conjunto de TESTE e
avalia a acurácia de extração por campo e por categoria.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parents[1]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from eval.metrics import avaliar_campos_criticos
from src.ipa.baselines.regex_parser import extrair_por_regex
from src.ipa.rules import rotear_pedido


def main() -> None:
    caminho_splits = raiz_projeto / "data" / "splits.json"
    splits_data = json.loads(caminho_splits.read_text(encoding="utf-8"))
    docs_teste = splits_data.get("teste", [])

    csv_path = raiz_projeto / "results" / "raw" / "exp2_regex.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP2: EXECUÇÃO DO BASELINE REGEX ({len(docs_teste)} documentos)")
    print("=" * 65)

    totais_por_cat = {}
    acertos_por_cat = {}

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "doc_id",
            "categoria",
            "tipo_arquivo",
            "acerto_cliente",
            "acerto_data",
            "itens_precision",
            "itens_recall",
            "itens_f1",
            "acerto_completo",
            "rota_decidida",
        ])

        for doc_id in docs_teste:
            gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            cat = gold.get("categoria", "limpo")
            tipo = gold.get("tipo_arquivo", "txt")
            caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

            # Extração via baseline regex
            pedido_pred = extrair_por_regex(caminho_doc)
            res_roteamento = rotear_pedido(pedido_pred)

            # Avaliação contra o gabarito oficial
            avaliacao = avaliar_campos_criticos(pedido_pred, gold)

            writer.writerow([
                doc_id,
                cat,
                tipo,
                int(avaliacao["acerto_cliente"]),
                int(avaliacao["acerto_data"]),
                avaliacao["itens_precision"],
                avaliacao["itens_recall"],
                avaliacao["itens_f1"],
                int(avaliacao["acerto_completo"]),
                res_roteamento.decisao.value,
            ])

            totais_por_cat[cat] = totais_por_cat.get(cat, 0) + 1
            if avaliacao["acerto_completo"]:
                acertos_por_cat[cat] = acertos_por_cat.get(cat, 0) + 1

    print("\n[RESULTADOS RESUMIDOS - REGEX BASELINE]")
    for cat, tot in totais_por_cat.items():
        acertos = acertos_por_cat.get(cat, 0)
        taxa = (acertos / tot) * 100.0 if tot > 0 else 0.0
        print(f"• Categoria {cat.upper():<12}: {acertos}/{tot} acertos completos ({taxa:.1f}%)")
    print(f"\n[OK] Resultados salvos em: {csv_path.resolve()}\n")


if __name__ == "__main__":
    main()
