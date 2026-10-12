"""
Script para testar o robô RPA contra o ERP Simulado.
Certifique-se de que o ERP está rodando em outro terminal:
    uv run uvicorn erp_sim.main:app --port 8000
"""
import json
import time
from rpa.bot import executar

def main():
    # Geramos uma referência única por timestamp para testar inserção nova
    timestamp = int(time.time())
    ref_id = f"TESTE-RPA-{timestamp}"

    pedido = {
        "ref_id": ref_id,
        "cliente": {
            # Você pode passar o ID de um cliente existente:
            "id": 9
            # Ou testar cliente novo descomentando abaixo:
            # "novo": True,
            # "nome": "Cliente Novo Teste",
            # "cnpj_cpf": "12345678000195",
            # "email": "novo@empresa.com",
        },
        "data_entrega": "2026-10-09",
        "observacoes": "Pedido gerado via teste de RPA",
        "itens": [
            {"codigo": "P-001", "quantidade": 3},
            {"codigo": "P-002", "quantidade": 5},
        ],
    }

    print(f"\n[1] Executando o robô para criar o pedido '{ref_id}'...")
    resultado = executar(pedido)
    print("Resultado da criação:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    print("\n[2] Testando proteção anti-duplicidade (re-executando com a mesma ref)...")
    resultado_duplicado = executar(pedido)
    print("Resultado da tentativa duplicada:")
    print(json.dumps(resultado_duplicado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
