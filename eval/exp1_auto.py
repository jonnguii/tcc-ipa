"""Script para o Experimento 1 (EXP1 - Automação IPA).
Processa os mesmos 30 documentos do teste utilizados no teste manual (Apêndice G)
e registra os tempos de cada estágio em results/raw/exp1_auto.csv.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parents[1]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from eval.exp1_manual import selecionar_documentos_exp1
from src.ipa.workflow import OrquestradorIPA


def main() -> None:
    docs_exp1 = selecionar_documentos_exp1()
    csv_path = raiz_projeto / "results" / "raw" / "exp1_auto.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP1: EXECUÇÃO DO ORQUESTRADOR IPA ({len(docs_exp1)} documentos)")
    print("=" * 65)

    orquestrador = OrquestradorIPA(tipo_executor="stub")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "doc_id",
            "categoria",
            "tipo_arquivo",
            "tempo_ia_s",
            "tempo_regras_s",
            "tempo_executor_s",
            "tempo_revisao_s",
            "tempo_total_s",
            "rota_decidida",
            "status_final",
        ])

        for idx, doc_id in enumerate(docs_exp1, start=1):
            gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            cat = gold.get("categoria", "limpo")
            tipo = gold.get("tipo_arquivo", "txt")
            caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

            print(f"[{idx}/{len(docs_exp1)}] Processando {doc_id} ({caminho_doc.name})...", end="", flush=True)

            res = orquestrador.processar_documento(caminho_doc)

            # Extração de tempos de cada evento
            tempos_etapa = {}
            for ev in res.eventos:
                tempos_etapa[ev.etapa] = ev.duracao_s

            tempo_ia = tempos_etapa.get("EXTRACAO_IA", 0.0)
            tempo_regras = tempos_etapa.get("REGRAS_TRIAGEM", 0.0)
            tempo_exec = tempos_etapa.get("EXECUTOR_RPA", 0.0)
            tempo_rev = tempos_etapa.get("REVISAO_HUMANA", 0.0)

            writer.writerow([
                doc_id,
                cat,
                tipo,
                tempo_ia,
                tempo_regras,
                tempo_exec,
                tempo_rev,
                res.tempo_total_s,
                res.decisao_roteamento,
                res.estado_final.value,
            ])
            f.flush()
            print(f" Concluído: {res.decisao_roteamento} em {res.tempo_total_s:.3f}s")

    print("\n" + "=" * 65)
    print(f"✅ Execução do EXP1 IPA finalizada com sucesso!")
    print(f"Resultados registrados em: {csv_path.resolve()}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
