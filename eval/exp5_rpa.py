"""Script para o Experimento 5 (EXP5 - Resiliência e Idempotência do Robô RPA).
Avalia o comportamento do executor do robô RPA sob condições normais e
re-execuções de idempotência, gerando results/raw/exp5_rpa.csv.
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

from src.ipa.contracts import ExecutorPedido
from src.ipa.executor import obter_executor


def main() -> None:
    csv_path = raiz_projeto / "results" / "raw" / "exp5_rpa.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f" EXP5: AUDITORIA DE RESILIÊNCIA E IDEMPOTÊNCIA DO RPA")
    print("=" * 65)

    executor = obter_executor(tipo="stub")

    # Amostra de 10 pedidos válidos para teste de disparo e idempotência
    pedidos_teste = [
        {
            "ref_id": f"DOC-TEST-RPA-{i:03d}",
            "cliente": {"id": 1, "novo": False, "nome": "Cliente Teste", "cnpj_cpf": "12345678000195"},
            "data_entrega": "2026-11-25",
            "observacoes": "Teste de resiliência e idempotência",
            "itens": [{"codigo": "P-001", "quantidade": 10.0}],
        }
        for i in range(1, 11)
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rodada",
            "ref_id",
            "status_retornado",
            "tempo_execucao_s",
            "eh_idempotente",
            "mensagem",
        ])

        # Rodada 1: Primeira inserção (esperado: status=sucesso)
        print("\n[Rodada 1] Executando inserções iniciais...")
        for p in pedidos_teste:
            t0 = time.perf_counter()
            res = executor.executar(p)
            dt = round(time.perf_counter() - t0, 4)

            status = res.get("status")
            writer.writerow([1, p["ref_id"], status, dt, int(status == "sucesso"), res.get("mensagem", "")])
            print(f"• {p['ref_id']}: Status={status} ({dt:.3f}s)")

        # Rodada 2: Re-execução imediata dos mesmos IDs (esperado: status=duplicado, ZERO duplicação)
        print("\n[Rodada 2] Re-executando mesmos pedidos (Teste de Idempotência)...")
        for p in pedidos_teste:
            t0 = time.perf_counter()
            res = executor.executar(p)
            dt = round(time.perf_counter() - t0, 4)

            status = res.get("status")
            idempotente = (status == "duplicado")
            writer.writerow([2, p["ref_id"], status, dt, int(idempotente), res.get("mensagem", "")])
            print(f"• {p['ref_id']}: Status={status} ({dt:.3f}s) -> {'🛡️ Idempotência Confirmada' if idempotente else 'Falha'}")

    print(f"\n✅ Resultados salvos em: {csv_path.resolve()}\n")


if __name__ == "__main__":
    main()
