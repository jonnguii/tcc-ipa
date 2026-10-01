PRODUTOS = [
    {"codigo": f"P-{i:03d}", "descricao": f"Produto {i}", "unidade": "UN", "preco": i * 1.5} for i in range(1, 41)
]

CLIENTES = [
    {"nome": f"Cliente {i}", "cnpj_cpf": f"{i*11111111111111:014d}", "email": f"cliente{i}@example.com"} for i in range(1, 21)
]
