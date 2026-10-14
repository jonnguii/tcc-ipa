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


import json

def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o Orquestrador IPA em lotes de documentos da inbox.")
    parser.add_argument("--limite", "-n", type=int, default=10, help="Quantidade máxima de documentos a processar (default: 10).")
    parser.add_argument("--inicio", "-i", type=int, default=1, help="Número/offset do documento inicial (1 a 80).")
    parser.add_argument("--docs", "-d", type=str, default="", help="IDs específicos separados por vírgula (ex: DOC-0012,DOC-0039).")
    parser.add_argument("--categoria", "-c", choices=["limpo", "ruidoso", "adversarial"], default=None, help="Filtrar por categoria.")
    parser.add_argument("--split", "-s", choices=["dev", "teste"], default=None, help="Filtrar por split (dev: 1-30, teste: 31-80).")
    parser.add_argument("--executor", "-e", choices=["stub", "rpa"], default="stub", help="Tipo de executor a utilizar.")
    parser.add_argument("--pasta", "-p", type=str, default="data/inbox", help="Pasta com os documentos de entrada.")
    args = parser.parse_args()

    arquivos = sorted(glob.glob(f"{args.pasta}/DOC-*.*"))
    if not arquivos:
        print(f"[ERRO] Nenhum documento encontrado em '{args.pasta}'.")
        sys.exit(1)

    # 1. Filtro por IDs específicos
    if args.docs:
        alvos = {d.strip().upper() for d in args.docs.split(",") if d.strip()}
        # Suporta tanto "39" quanto "DOC-0039"
        alvos_normalizados = set()
        for a in alvos:
            alvos_normalizados.add(a if a.startswith("DOC-") else f"DOC-{int(a):04d}")
        arquivos = [arq for arq in arquivos if Path(arq).stem in alvos_normalizados]

    # 2. Filtro por Split
    if args.split == "dev":
        arquivos = arquivos[:30]
    elif args.split == "teste":
        arquivos = arquivos[30:]

    # 3. Filtro por Categoria (lendo do gabarito em data/gold)
    if args.categoria:
        filtrados = []
        for arq in arquivos:
            doc_id = Path(arq).stem
            gold_file = Path("data/gold") / f"{doc_id}.json"
            if gold_file.exists():
                try:
                    cat = json.loads(gold_file.read_text(encoding="utf-8")).get("categoria", "").lower()
                    if cat == args.categoria.lower():
                        filtrados.append(arq)
                except Exception:
                    pass
        arquivos = filtrados

    # 4. Offset de início e limite
    if not args.docs:
        offset = max(0, args.inicio - 1)
        selecionados = arquivos[offset : offset + args.limite]
    else:
        selecionados = arquivos

    if not selecionados:
        print(f"[AVISO] Nenhum documento atendeu aos filtros selecionados.")
        sys.exit(0)

    print(f"\n=======================================================")
    print(f" ORQUESTRADOR IPA: Executando Lote ({len(selecionados)} docs)")
    print(f" Modo do Executor: {args.executor.upper()}")
    if args.docs:
        print(f" Filtro IDs:       {args.docs}")
    if args.categoria:
        print(f" Categoria:        {args.categoria.upper()}")
    if args.split:
        print(f" Split:            {args.split.upper()}")
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
