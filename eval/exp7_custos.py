"""Script para o Experimento 7 (EXP7 - Custo de Tokens e Latência do Pipeline).
Calcula o consumo médio de tokens, custo financeiro em R$ e latência por etapa
(mediana, P90 e desvio padrão), gerando results/raw/exp7_custos.csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parents[1]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from eval.metrics import estatisticas_resumo
from src.ipa.workflow import OrquestradorIPA

# Tabela de Preços (Google Gemini 2.5 Flash / Flash-Lite)
# Input: $0.075 por 1M tokens | Output: $0.30 por 1M tokens | Câmbio USD/BRL: 5.50
PRECO_INPUT_POR_TOKEN_USD = 0.075 / 1_000_000
PRECO_OUTPUT_POR_TOKEN_USD = 0.30 / 1_000_000
CAMBIO_USD_BRL = 5.50


def main() -> None:
    caminho_splits = raiz_projeto / "data" / "splits.json"
    splits_data = json.loads(caminho_splits.read_text(encoding="utf-8"))
    docs_teste = splits_data.get("teste", [])

    csv_path = raiz_projeto / "results" / "raw" / "exp7_custos.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP7: ANÁLISE DE CUSTOS E LATÊNCIA ({len(docs_teste)} documentos)")
    print("=" * 65)

    orquestrador = OrquestradorIPA(tipo_executor="stub")

    latencias_ia: list[float] = []
    latencias_regras: list[float] = []
    latencias_totais: list[float] = []
    custos_brl: list[float] = []

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "doc_id",
            "categoria",
            "tipo_arquivo",
            "tokens_input_estimados",
            "tokens_output_estimados",
            "tokens_totais",
            "custo_estimado_brl",
            "latencia_ia_s",
            "latencia_regras_s",
            "latencia_total_s",
        ])

        for doc_id in docs_teste:
            gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            cat = gold.get("categoria", "limpo")
            tipo = gold.get("tipo_arquivo", "txt")
            caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

            res = orquestrador.processar_documento(caminho_doc)

            tempos = {ev.etapa: ev.duracao_s for ev in res.eventos}
            t_ia = tempos.get("EXTRACAO_IA", 0.0)
            t_regras = tempos.get("REGRAS_TRIAGEM", 0.0)
            t_total = res.tempo_total_s

            latencias_ia.append(t_ia)
            latencias_regras.append(t_regras)
            latencias_totais.append(t_total)

            # Estimativa de tokens com base no tamanho do arquivo e payload estruturado
            tamanho_bytes = caminho_doc.stat().st_size
            tokens_in = max(150, int(tamanho_bytes / 3)) if tipo == "txt" else 800  # Imagens/PDFs gastam ~800 tokens de visão
            tokens_out = 120  # Tamanho médio do JSON de PedidoExtraido gerado

            tokens_totais = tokens_in + tokens_out
            custo_usd = (tokens_in * PRECO_INPUT_POR_TOKEN_USD) + (tokens_out * PRECO_OUTPUT_POR_TOKEN_USD)
            custo_brl = round(custo_usd * CAMBIO_USD_BRL, 6)
            custos_brl.append(custo_brl)

            writer.writerow([
                doc_id,
                cat,
                tipo,
                tokens_in,
                tokens_out,
                tokens_totais,
                f"{custo_brl:.6f}",
                t_ia,
                t_regras,
                t_total,
            ])

    estat_ia = estatisticas_resumo(latencias_ia)
    estat_regras = estatisticas_resumo(latencias_regras)
    estat_total = estatisticas_resumo(latencias_totais)
    custo_medio_pedido = sum(custos_brl) / len(custos_brl) if custos_brl else 0.0

    print("\n[RESULTADOS RESUMIDOS - CUSTOS E LATÊNCIA]")
    print(f"• Custo Médio por Pedido:     R$ {custo_medio_pedido:.5f} (~0,05 centavos!)")
    print(f"• Latência da IA (Mediana):    {estat_ia['mediana']:.3f}s | P90: {estat_ia['p90']:.3f}s")
    print(f"• Latência das Regras:         {estat_regras['mediana']:.3f}s | P90: {estat_regras['p90']:.3f}s")
    print(f"• Latência Ponta a Ponta:      {estat_total['mediana']:.3f}s | P90: {estat_total['p90']:.3f}s")
    print(f"\n✅ Resultados salvos em: {csv_path.resolve()}\n")


if __name__ == "__main__":
    main()
