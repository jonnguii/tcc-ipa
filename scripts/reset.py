"""Script utilitário para resetar o ambiente de testes do TCC-IPA.
Permite limpar pedidos do ERP, fila de revisões, prints do robô e cache de IA.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Adiciona a raiz ao path
raiz_projeto = Path(__file__).resolve().parents[1]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from erp_sim.db import supabase


def limpar_pedidos_banco():
    print("[LIMPEZA] Limpando pedidos e itens no Supabase...")
    try:
        res = supabase.table("erp_pedidos").delete().neq("id", 0).execute()
        print(f"   [OK] {len(res.data)} pedidos apagados (itens removidos em cascata).")
    except Exception as e:
        print(f"   [FALHA] Erro ao limpar erp_pedidos: {e}")


def limpar_revisoes():
    print("[LIMPEZA] Limpando fila de revisões...")
    # Remoto
    try:
        res = supabase.table("ipa_revisoes").delete().neq("id", 0).execute()
        print(f"   [OK] {len(res.data)} revisões remotas apagadas.")
    except Exception:
        pass
    # Local
    caminho_local = raiz_projeto / "data" / "revisoes_local.json"
    if caminho_local.exists():
        caminho_local.write_text("[]\n", encoding="utf-8")
        print("   [OK] data/revisoes_local.json zerado.")


def limpar_evidencias():
    print("[LIMPEZA] Limpando evidências visuais do robô...")
    pasta_evidencias = raiz_projeto / "rpa" / "evidencias"
    if pasta_evidencias.exists():
        removidos = 0
        for img in pasta_evidencias.glob("*.png"):
            img.unlink()
            removidos += 1
        print(f"   [OK] {removidos} screenshots removidos em rpa/evidencias/.")


def limpar_cache_ia():
    print("[LIMPEZA] Limpando cache do Gemini (.ai_cache.json)...")
    cache_file = raiz_projeto / ".ai_cache.json"
    cache_file.write_text("{}\n", encoding="utf-8")
    print("   [OK] .ai_cache.json zerado.")


def main():
    parser = argparse.ArgumentParser(description="Reset do ambiente do TCC-IPA")
    parser.add_argument(
        "--tudo",
        "-t",
        action="store_true",
        help="Limpa tudo: pedidos, revisões, evidências e cache de IA.",
    )
    parser.add_argument(
        "--pedidos",
        "-p",
        action="store_true",
        help="Limpa apenas pedidos, revisões e evidências (mantém o cache de IA).",
    )
    args = parser.parse_args()

    # Se nenhum argumento for passado, pergunta interativamente
    modo = None
    if args.tudo:
        modo = "2"
    elif args.pedidos:
        modo = "1"
    else:
        print("\n=== UTILITÁRIO DE RESET (TCC-IPA) ===")
        print("1. Limpar apenas Pedidos no ERP + Revisões + Prints (MANTÉM cache da IA)")
        print("2. Limpar TUDO (Pedidos + Revisões + Prints + Cache da IA)")
        print("0. Cancelar")
        escolha = input("\nEscolha uma opção (1/2/0): ").strip()
        if escolha in ("1", "2"):
            modo = escolha
        else:
            print("Operação cancelada.")
            return

    print()
    limpar_pedidos_banco()
    limpar_revisoes()
    limpar_evidencias()

    if modo == "2":
        limpar_cache_ia()

    print("\n[OK] Ambiente pronto para novos testes!\n")


if __name__ == "__main__":
    main()
