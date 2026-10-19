"""Script para o Experimento 4 (EXP4 - Curva de Risco vs Cobertura e Varredura de Limiares).
Varia o limiar de confiança mínima de 0.50 a 0.99 e calcula a taxa de cobertura
de automação e o erro residual, gerando results/raw/exp4_limiares.csv.
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
from src.ipa.rules.rotear import rotear_pedido


def main() -> None:
    caminho_splits = raiz_projeto / "data" / "splits.json"
    splits_data = json.loads(caminho_splits.read_text(encoding="utf-8"))
    docs_teste = splits_data.get("teste", [])

    csv_path = raiz_projeto / "results" / "raw" / "exp4_limiares.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP4: VARREDURA DE LIMIARES DE CONFIANÇA ({len(docs_teste)} docs)")
    print("=" * 65)

    # 1. Pré-carrega predições e avaliações de todos os docs do teste
    dados_docs = []
    for doc_id in docs_teste:
        gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        tipo = gold.get("tipo_arquivo", "txt")
        caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

        pedido_pred = processar_documento(str(caminho_doc))
        res_roteamento = rotear_pedido(pedido_pred)
        avaliacao = avaliar_campos_criticos(pedido_pred, gold)

        dados_docs.append({
            "doc_id": doc_id,
            "gold": gold,
            "pedido_pred": pedido_pred,
            "roteamento": res_roteamento,
            "avaliacao": avaliacao,
            "confianca": res_roteamento.confianca_geral,
            "rota_base": res_roteamento.decisao.value,
        })

    total_docs = len(dados_docs)

    # 2. Varredura de limiares de 0.50 a 0.99
    limiares = [round(x * 0.01, 2) for x in range(50, 100)]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["limiar", "total_docs", "qtd_automaticos", "cobertura_pct", "erros_automatico", "erro_residual_pct"])

        ponto_otimo = None

        for limiar in limiares:
            qtd_automaticos = 0
            erros_automatico = 0

            for item in dados_docs:
                conf = item["confianca"]
                rota_base = item["rota_base"]

                # O pedido só vai para AUTOMATICO se as regras de negócio permitirem E a confiança superar o limiar
                eh_automatico = (rota_base == "AUTOMATICO" and conf >= limiar)

                if eh_automatico:
                    qtd_automaticos += 1
                    # Houve erro em algum campo crítico?
                    if not item["avaliacao"]["acerto_completo"]:
                        erros_automatico += 1

            cobertura_pct = round((qtd_automaticos / total_docs) * 100.0, 2)
            erro_residual_pct = round((erros_automatico / qtd_automaticos) * 100.0, 2) if qtd_automaticos > 0 else 0.0

            writer.writerow([limiar, total_docs, qtd_automaticos, cobertura_pct, erros_automatico, erro_residual_pct])

            # Ponto ótimo para Hipótese H3: maior cobertura com erro residual <= 2.0%
            if erro_residual_pct <= 2.0 and (ponto_otimo is None or cobertura_pct > ponto_otimo["cobertura"]):
                ponto_otimo = {"limiar": limiar, "cobertura": cobertura_pct, "erro": erro_residual_pct}

    print("\n[CURVA RISCO vs COBERTURA CONCLUÍDA]")
    if ponto_otimo:
        print(f"• Ponto Ótimo Selecionado (H3): Limiar = {ponto_otimo['limiar']:.2f}")
        print(f"• Cobertura de Automação:      {ponto_otimo['cobertura']:.1f}%")
        print(f"• Erro Residual nos Pedidos:   {ponto_otimo['erro']:.1f}% (Meta <= 2.0% atingida!)")
    print(f"\n✅ Resultados salvos em: {csv_path.resolve()}\n")


if __name__ == "__main__":
    main()
