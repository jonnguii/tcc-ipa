"""Script para gerar os arquivos físicos na pasta data/inbox/
a partir dos gabaritos estruturados em data/gold/.
Suporta arquivos .txt, .pdf e .png, aplicando ruídos e padrões de negócio.
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path
from fpdf import FPDF
from PIL import Image, ImageDraw

# Adiciona a raiz do projeto ao path
raiz_projeto = Path(__file__).resolve().parents[2]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

from erp_sim.seed_data import CLIENTES, PRODUTOS
from data.generator.ruido import sujar_texto
from data.generator.templates import get_template_by_flag
from data.generator.verdade import PRODUTOS_FORA_CATALOGO

# Dicionários de busca rápida
DICT_CLIENTES = {i + 1: c for i, c in enumerate(CLIENTES)}
DICT_PRODUTOS = {p["codigo"]: p for p in PRODUTOS}
for p in PRODUTOS_FORA_CATALOGO:
    DICT_PRODUTOS[p["codigo"]] = p


def gerar_texto_bruto(gold_data: dict, doc_id: str) -> str:
    categoria = gold_data.get("categoria", "limpo")
    pedido = gold_data.get("pedido_verdade", {})
    flags = gold_data.get("flags", [])
    primary_flag = flags[0] if flags else "padrao"

    # 1. Busca o template correspondente à flag e categoria
    template = get_template_by_flag(categoria, primary_flag)

    # 2. Dados do cliente
    cli_id = pedido.get("cliente", {}).get("id")
    cli_dados = DICT_CLIENTES.get(cli_id, {}) if cli_id else {}
    cliente_nome = pedido.get("cliente", {}).get("nome") or cli_dados.get("nome", "Cliente Sem Cadastro")
    cliente_cnpj = pedido.get("cliente", {}).get("cnpj_cpf") or cli_dados.get("cnpj_cpf", "")

    # 3. Formata itens
    itens_str = ""
    for item in pedido.get("itens", []):
        codigo = item.get("codigo")
        qtd = item.get("quantidade")
        prod_nome = DICT_PRODUTOS.get(codigo, {}).get("descricao", codigo)
        itens_str += f"- {qtd}x {prod_nome} ({codigo})\n"

    data_entrega = pedido.get("data_entrega", "2026-11-20")

    # 4. Interpolação no template
    texto = template.format(
        cliente=cliente_nome,
        cnpj=cliente_cnpj if cliente_cnpj else "Não informado",
        itens=itens_str,
        data=data_entrega,
        ref=doc_id,
    )

    # 5. Aplica ruído fonético/teclado apenas nos casos ruidosos padrão
    if categoria.lower() == "ruidoso" and primary_flag == "padrao":
        texto = sujar_texto(texto, "RUIDOSO")

    return texto


def salvar_txt(caminho: Path, texto: str) -> None:
    caminho.write_text(texto, encoding="utf-8")


def salvar_pdf(caminho: Path, texto: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    texto_limpo = texto.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 10, texto_limpo)
    pdf.output(str(caminho))


def salvar_png(caminho: Path, texto: str) -> None:
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), texto, fill=(0, 0, 0))
    img.save(caminho)


def main() -> None:
    random.seed(42)

    gold_dir = Path("data/gold")
    inbox_dir = Path("data/inbox")
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Limpa arquivos antigos da inbox para evitar extensões obsoletas
    for antigo in inbox_dir.glob("DOC-*.*"):
        antigo.unlink()

    arquivos_gold = sorted(gold_dir.glob("DOC-*.json"))
    if not arquivos_gold:
        print("[AVISO] Nenhum gabarito encontrado em data/gold/. Execute verdade.py primeiro.")
        return

    print(f"Fabricando {len(arquivos_gold)} documentos físicos para data/inbox/...")

    for arquivo in arquivos_gold:
        gold_data = json.loads(arquivo.read_text(encoding="utf-8"))
        doc_id = arquivo.stem
        texto = gerar_texto_bruto(gold_data, doc_id)
        tipo = gold_data.get("tipo_arquivo", "txt").lower()

        if tipo == "txt":
            salvar_txt(inbox_dir / f"{doc_id}.txt", texto)
        elif tipo == "pdf":
            salvar_pdf(inbox_dir / f"{doc_id}.pdf", texto)
        elif tipo == "png":
            salvar_png(inbox_dir / f"{doc_id}.png", texto)

    print(f"[OK] Sucesso! Documentos fabricados na pasta {inbox_dir.resolve()}")


if __name__ == "__main__":
    main()
