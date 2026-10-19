"""Script para o Experimento 3 (EXP3 - Avaliação de Extração Inteligente com IA).
Executa a extração via Gemini no conjunto de TESTE e calcula Precision, Recall e F1
por campo crítico e categoria, gerando results/raw/exp3_extracao.csv.
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
from src.ipa.ai.extractor import processar_documento
from src.ipa.rules import rotear_pedido


def main() -> None:
    caminho_splits = raiz_projeto / "data" / "splits.json"
    splits_data = json.loads(caminho_splits.read_text(encoding="utf-8"))
    docs_teste = splits_data.get("teste", [])

    csv_path = raiz_projeto / "results" / "raw" / "exp3_extracao.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP3: AVALIAÇÃO DA EXTRAÇÃO COM IA ({len(docs_teste)} documentos)")
    print("=" * 65)

    totais_por_cat = {}
    f1_itens_por_cat = {}
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
            "confianca_geral",
        ])

        for idx, doc_id in enumerate(docs_teste, start=1):
            gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            cat = gold.get("categoria", "limpo")
            tipo = gold.get("tipo_arquivo", "txt")
            caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

            print(f"[{idx}/{len(docs_teste)}] Extraindo {doc_id}...", end="", flush=True)

            pedido_pred = processar_documento(str(caminho_doc))
            res_roteamento = rotear_pedido(pedido_pred)
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
                res_roteamento.confianca_geral,
            ])
            f.flush()

            totais_por_cat[cat] = totais_por_cat.get(cat, 0) + 1
            f1_itens_por_cat.setdefault(cat, []).append(avaliacao["itens_f1"])
            if avaliacao["acerto_completo"]:
                acertos_por_cat[cat] = acertos_por_cat.get(cat, 0) + 1

            print(f" F1={avaliacao['itens_f1']:.2f} | Rota={res_roteamento.decisao.value}")

    print("\n[RESULTADOS RESUMIDOS - EXTRAÇÃO IA]")
    for cat, tot in totais_por_cat.items():
        acertos = acertos_por_cat.get(cat, 0)
        f1_medio = sum(f1_itens_por_cat[cat]) / len(f1_itens_por_cat[cat]) if f1_itens_por_cat[cat] else 0.0
        taxa = (acertos / tot) * 100.0 if tot > 0 else 0.0
        print(f"• Categoria {cat.upper():<12}: F1 Médio={f1_medio:.4f} | Acertos Completos={acertos}/{tot} ({taxa:.1f}%)")

    print(f"\n✅ Resultados salvos em: {csv_path.resolve()}\n")


if __name__ == "__main__":
    main()
