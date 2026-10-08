import json
import random
from pathlib import Path
import sys

# Adiciona raiz ao path para importar a seed
sys.path.append(str(Path(__file__).parent.parent.parent))
from erp_sim.seed_data import PRODUTOS, CLIENTES

random.seed(42)  # Importante: fixa o sorteio para reprodutibilidade

def gerar_pedidos_verdade(qtd=80):
    Path("data/gold").mkdir(parents=True, exist_ok=True)
    
    categorias = ["limpo"]*32 + ["ruidoso"]*32 + ["adversarial"]*16
    random.shuffle(categorias)
    
    for i in range(1, qtd + 1):
        cliente = random.choice(CLIENTES)
        n_itens = random.randint(1, 6)
        itens_escolhidos = random.sample(PRODUTOS, n_itens)
        
        itens = [
            {"codigo": p["codigo"], "quantidade": random.randint(1, 100)}
            for p in itens_escolhidos
        ]
        
        # O Pedido perfeito esperado
        pedido_verdade = {
            "cliente": {"id": CLIENTES.index(cliente) + 1},
            "data_entrega": f"2026-11-{random.randint(1,30):02d}",
            "itens": itens,
            "observacoes": ""
        }
        
        gabarito = {
            "id": f"DOC-{i:04d}",
            "categoria": categorias[i-1],
            "tipo_arquivo": random.choice(["txt", "pdf", "png"]),
            "pedido_verdade": pedido_verdade,
            "rota_esperada": "AUTOMATICO",
            "flags": []
        }
        
        arquivo = Path(f"data/gold/DOC-{i:04d}.json")
        arquivo.write_text(json.dumps(gabarito, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    gerar_pedidos_verdade()
    print("80 gabaritos gerados em data/gold/")
