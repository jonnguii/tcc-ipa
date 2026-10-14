"""Script executável para rodar o Orquestrador IPA em lotes de documentos.
Suporta execução em modo STUB (simulado) ou RPA (robô real).
"""
from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

# Garante que a raiz do projeto esteja no path ao rodar diretamente o script
raiz_projeto = Path(__file__).resolve().parents[2]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from src.ipa.executor import StubExecutor
from src.ipa.workflow import OrquestradorIPA


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o Orquestrador IPA em lotes de documentos da inbox.")
    parser.add_argument("--limite", "-n", type=int, default=10, help="Quantidade máxima de documentos a processar (default: 10).")
    parser.add_argument("--executor", "-e", choices=["stub", "rpa"], default="stub", help="Tipo de executor a utilizar.")
    parser.add_argument("--pasta", "-p", type=str, default="data/inbox", help="Pasta com os documentos de entrada.")
    args = parser.parse_args()

    arquivos = sorted(glob.glob(f"{args.pasta}/DOC-*.*"))
    if not arquivos:
        print(f"[ERRO] Nenhum documento encontrado em '{args.pasta}'.")
        sys.exit(1)

    selecionados = arquivos[: args.limite]
    print(f"\n=======================================================")
    print(f" ORQUESTRADOR IPA: Executando Lote ({len(selecionados)} docs)")
    print(f" Modo do Executor: {args.executor.upper()}")
    print(f"=======================================================\n")

    orquestrador = OrquestradorIPA(tipo_executor=args.executor)
    inicio_lote = time.perf_counter()

    totais = {"AUTOMATICO": 0, "REVISAO": 0, "REJEICAO": 0, "FALHA": 0}

    print(f"{'DOC ID':<12} | {'ROTA / DECISÃO':<14} | {'ESTADO FINAL':<15} | {'TEMPO (s)':<10} | {'STATUS EXECUTOR'}")
    print("-" * 75)

    for caminho in selecionados:
        resultado = orquestrador.processar_documento(caminho)
        rota = resultado.decisao_roteamento or "N/A"
        estado = resultado.estado_final.value
        tempo = f"{resultado.tempo_total_s:.3f}s"

        status_exec = "-"
        if resultado.resultado_executor:
            status_exec = f"{resultado.resultado_executor.get('status')} (#{resultado.resultado_executor.get('numero_pedido')})"
        elif resultado.pendencia_revisao:
            status_exec = f"Fila Revisão ({len(resultado.pendencia_revisao['motivos'])} mot)"
        elif resultado.erro:
            status_exec = f"Erro: {resultado.erro[:25]}"

        totais[rota] = totais.get(rota, 0) + 1
        print(f"{resultado.doc_id:<12} | {rota:<14} | {estado:<15} | {tempo:<10} | {status_exec}")

    duracao_total = time.perf_counter() - inicio_lote
    print("-" * 75)
    print(f"\n[RESUMO DO LOTE]")
    print(f"• Duração Total: {duracao_total:.2f}s")
    print(f"• Automático:    {totais.get('AUTOMATICO', 0)}")
    print(f"• Revisão:       {totais.get('REVISAO', 0)}")
    print(f"• Rejeição:      {totais.get('REJEICAO', 0)}")
    print(f"• Falhas:        {totais.get('FALHA', 0)}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    main()
