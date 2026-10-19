"""Script mestre de execução sequencial de todos os experimentos da Fase 11.
Gera toda a base de dados científicos bruta em results/raw/ e consolida as tabelas em results/tables/.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parents[1]

PASSOS_EXPERIMENTAIS = [
    ("EXP1 (Baseline Manual)", [sys.executable, "eval/exp1_manual.py", "--simular", "--lote", "1"]),
    ("EXP1 (Baseline Manual - Lote 2)", [sys.executable, "eval/exp1_manual.py", "--simular", "--lote", "2"]),
    ("EXP1 (Baseline Manual - Lote 3)", [sys.executable, "eval/exp1_manual.py", "--simular", "--lote", "3"]),
    ("EXP1 (Automação IPA)", [sys.executable, "eval/exp1_auto.py"]),
    ("EXP2 (Baseline Regex)", [sys.executable, "eval/exp2_regex.py"]),
    ("EXP3 (Extração IA)", [sys.executable, "eval/exp3_extracao.py"]),
    ("EXP4 (Curva de Limiares)", [sys.executable, "eval/exp4_limiares.py"]),
    ("EXP5 (Resiliência RPA)", [sys.executable, "eval/exp5_rpa.py"]),
    ("EXP6 (Auditoria Injeção)", [sys.executable, "eval/exp6_injection.py"]),
    ("EXP7 (Custos e Latência)", [sys.executable, "eval/exp7_custos.py"]),
    ("Consolidação Tabelas T1-T6", [sys.executable, "eval/charts.py"]),
]


def main() -> None:
    print("\n" + "=" * 70)
    print(" INICIANDO BATERIA COMPLETA DE EXPERIMENTOS DA FASE 11 (TCC-IPA)")
    print("=" * 70)

    inicio_geral = time.perf_counter()

    for nome, cmd in PASSOS_EXPERIMENTAIS:
        print(f"\n[INICIANDO] Executando: {nome}...")
        res = subprocess.run(cmd, cwd=str(raiz_projeto))
        if res.returncode != 0:
            print(f"[FALHA] Erro na execução de {nome} (Código de saída: {res.returncode})")
            sys.exit(res.returncode)

    duracao_total = time.perf_counter() - inicio_geral
    print("\n" + "=" * 70)
    print(f"[OK] BATERIA DE EXPERIMENTOS CONCLUÍDA EM {duracao_total:.2f}s!")
    print(f"• Dados brutos: results/raw/*.csv")
    print(f"• Tabelas T1-T6: results/tables/*.md")
    print(f"• Relatório analítico: results/RESULTADOS.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
