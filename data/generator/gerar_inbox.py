import sys
import json
import os
import random
from pathlib import Path
from fpdf import FPDF
from PIL import Image, ImageDraw

# Adiciona a raiz do projeto no PATH para conseguir importar o seed_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from erp_sim.seed_data import CLIENTES, PRODUTOS

from data.generator.templates import get_template
from data.generator.ruido import sujar_texto

# Cria dicionários para busca rápida pelo ID/Código
DICT_CLIENTES = {i+1: c for i, c in enumerate(CLIENTES)}
DICT_PRODUTOS = {p["codigo"]: p for p in PRODUTOS}

def gerar_texto_bruto(gold_data: dict, doc_id: str) -> str:
    categoria = gold_data.get("categoria", "LIMPO")
    pedido = gold_data.get("pedido_verdade", {})
    
    template = get_template(categoria)
    
    # 1. Busca os dados reais do cliente a partir do ID
    cli_id = pedido.get("cliente", {}).get("id")
    cli_dados = DICT_CLIENTES.get(cli_id, {})
    cliente_nome = cli_dados.get("nome", "Desconhecido")
    cliente_cnpj = cli_dados.get("cnpj_cpf", "00000000000000")
    
    # 2. Busca os nomes dos produtos e formata a lista de itens
    itens_str = ""
    for item in pedido.get("itens", []):
        codigo = item.get("codigo")
        qtd = item.get("quantidade")
        prod_nome = DICT_PRODUTOS.get(codigo, {}).get("descricao", codigo)
        itens_str += f"- {qtd}x {prod_nome} ({codigo})\n"
        
    data_entrega = pedido.get("data_entrega", "")
    
    # 3. Joga no template
    texto = template.format(
        cliente=cliente_nome,
        cnpj=cliente_cnpj,
        itens=itens_str,
        data=data_entrega,
        ref=doc_id # Usamos o próprio DOC-XXXX como referência de pedido do cliente
    )
    
    return sujar_texto(texto, categoria)

def salvar_txt(caminho: Path, texto: str):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)

def salvar_pdf(caminho: Path, texto: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12) # Corrigido warning do Arial
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, texto_limpo)
    pdf.output(str(caminho))

def salvar_png(caminho: Path, texto: str):
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), texto, fill=(0, 0, 0))
    img.save(caminho)

def main():
    random.seed(42)
    
    gold_dir = Path("data/gold")
    inbox_dir = Path("data/inbox")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    print("Fabricando as mensagens sujas...")
    
    for arquivo in gold_dir.glob("*.json"):
        with open(arquivo, "r", encoding="utf-8") as f:
            gold_data = json.load(f)
            
        doc_id = arquivo.stem # Pega o DOC-XXXX
        texto = gerar_texto_bruto(gold_data, doc_id)
        tipo = gold_data.get("tipo_arquivo", "txt")
        
        if tipo == "txt":
            salvar_txt(inbox_dir / f"{doc_id}.txt", texto)
        elif tipo == "pdf":
            salvar_pdf(inbox_dir / f"{doc_id}.pdf", texto)
        elif tipo == "png":
            salvar_png(inbox_dir / f"{doc_id}.png", texto)
            
    print(f"✅ Sucesso! Olhe os textos fabricados na pasta {inbox_dir.resolve()}")

if __name__ == "__main__":
    main()
