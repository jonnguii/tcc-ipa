import time
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from erp_sim import repo
from src.ipa.config import settings

app = FastAPI()
app.mount("/static", StaticFiles(directory="erp_sim/static"), name="static")
templates = Jinja2Templates(directory="erp_sim/templates")


def formato_moeda(valor):
    try:
        num = float(valor)
        # Formata com separador de milhar e decimal no padrão pt-BR
        return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


templates.env.filters["moeda"] = formato_moeda


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse(url="/pedidos", status_code=303)


@app.middleware("http")
async def sabotage_middleware(request: Request, call_next):
    if settings.erp_sabotage == "slow" and request.method == "POST":
        time.sleep(3)
    response = await call_next(request)
    return response

@app.get("/produtos", response_class=HTMLResponse)
def listar_produtos(request: Request):
    return templates.TemplateResponse(request=request, name="produtos.html", context={"produtos": repo.get_produtos()})

@app.get("/produtos/novo", response_class=HTMLResponse)
def form_produto_novo(request: Request):
    return templates.TemplateResponse(request=request, name="produtos_novo.html")

@app.post("/produtos/novo")
def criar_produto(codigo: str = Form(...), descricao: str = Form(...), unidade: str = Form(...), preco: str = Form(...)):
    try:
        preco_float = float(preco)
        repo.criar_produto(codigo, descricao, unidade, preco_float)
        return RedirectResponse(url="/produtos?msg=Produto+criado", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(request=request, name="produtos_novo.html", context={"error": str(e)})

@app.get("/produtos/{produto_id}/editar", response_class=HTMLResponse)
def form_produto_editar(request: Request, produto_id: int):
    produto = repo.get_produto_by_id(produto_id)
    if not produto:
        return RedirectResponse(url="/produtos?msg_erro=Produto+não+encontrado", status_code=303)
    return templates.TemplateResponse(request=request, name="produtos_editar.html", context={"produto": produto})

@app.post("/produtos/{produto_id}/editar")
def atualizar_produto(request: Request, produto_id: int, codigo: str = Form(...), descricao: str = Form(...), unidade: str = Form(...), preco: str = Form(...)):
    try:
        preco_float = float(preco)
        repo.atualizar_produto(produto_id, codigo, descricao, unidade, preco_float)
        return RedirectResponse(url="/produtos?msg=Produto+atualizado", status_code=303)
    except Exception as e:
        produto = repo.get_produto_by_id(produto_id)
        return templates.TemplateResponse(request=request, name="produtos_editar.html", context={"produto": produto, "error": str(e)})

@app.post("/produtos/{produto_id}/excluir")
def excluir_produto(produto_id: int):
    repo.excluir_produto(produto_id)
    return RedirectResponse(url="/produtos?msg=Produto+excluído", status_code=303)

@app.get("/clientes", response_class=HTMLResponse)
def listar_clientes(request: Request):
    return templates.TemplateResponse(request=request, name="clientes.html", context={"clientes": repo.get_clientes()})

@app.get("/clientes/novo", response_class=HTMLResponse)
def form_cliente(request: Request):
    return templates.TemplateResponse(request=request, name="clientes_novo.html")

@app.post("/clientes/novo")
def criar_cliente(nome: str = Form(...), cnpj_cpf: str = Form(...), email: str = Form(...)):
    repo.criar_cliente(nome, cnpj_cpf, email)
    return RedirectResponse(url="/clientes?msg=Cliente+criado", status_code=303)

@app.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
def form_cliente_editar(request: Request, cliente_id: int):
    cliente = repo.get_cliente_by_id(cliente_id)
    if not cliente:
        return RedirectResponse(url="/clientes?msg_erro=Cliente+não+encontrado", status_code=303)
    return templates.TemplateResponse(request=request, name="clientes_editar.html", context={"cliente": cliente})

@app.post("/clientes/{cliente_id}/editar")
def atualizar_cliente(request: Request, cliente_id: int, nome: str = Form(...), cnpj_cpf: str = Form(...), email: str = Form(...)):
    try:
        repo.atualizar_cliente(cliente_id, nome, cnpj_cpf, email)
        return RedirectResponse(url="/clientes?msg=Cliente+atualizado", status_code=303)
    except Exception as e:
        cliente = repo.get_cliente_by_id(cliente_id)
        return templates.TemplateResponse(request=request, name="clientes_editar.html", context={"cliente": cliente, "error": str(e)})

@app.post("/clientes/{cliente_id}/excluir")
def excluir_cliente(cliente_id: int):
    repo.excluir_cliente(cliente_id)
    return RedirectResponse(url="/clientes?msg=Cliente+excluído", status_code=303)

@app.get("/pedidos", response_class=HTMLResponse)
def listar_pedidos(request: Request, ref: str = None):
    return templates.TemplateResponse(request=request, name="pedidos.html", context={"pedidos": repo.get_pedidos(ref)})

@app.get("/pedidos/novo", response_class=HTMLResponse)
def form_pedido(request: Request):
    return templates.TemplateResponse(request=request, name="pedidos_novo.html", context={"clientes": repo.get_clientes(), "produtos": repo.get_produtos()})

@app.get("/pedidos/{pedido_id}", response_class=HTMLResponse)
def ver_pedido_detalhes(request: Request, pedido_id: int):
    pedido = repo.get_pedido_detalhes(pedido_id)
    if not pedido:
        return templates.TemplateResponse(request=request, name="pedidos.html", context={"pedidos": repo.get_pedidos(), "error": "Pedido não encontrado"})
    return templates.TemplateResponse(request=request, name="pedidos_detalhes.html", context={"pedido": pedido})

@app.post("/pedidos/novo")
async def post_pedido(request: Request):
    form_data = await request.form()
    cliente_id = int(form_data.get("cliente_id"))
    data_entrega = form_data.get("data_entrega")
    observacoes = form_data.get("observacoes")
    ref_externa = form_data.get("ref_externa")
    
    itens = []
    for i in range(1, 7):
        prod_id = form_data.get(f"produto_id_{i}")
        qtd = form_data.get(f"quantidade_{i}")
        if prod_id and qtd:
            itens.append({"produto_id": int(prod_id), "quantidade": float(qtd)})
            
    if not itens:
        return templates.TemplateResponse(request=request, name="pedidos_novo.html", context={"error": "Adicione pelo menos 1 item.", "clientes": repo.get_clientes(), "produtos": repo.get_produtos()})
        
    try:
        pedido_id = repo.criar_pedido(cliente_id, data_entrega, observacoes, ref_externa, itens)
        return RedirectResponse(url=f"/pedidos/novo?msg_sucesso=Pedido+nº+{pedido_id}+criado", status_code=303)
    except Exception as e:
        err = str(e)
        if "erp_pedidos_ref_externa_key" in err or "duplicate key" in err:
            return RedirectResponse(url=f"/pedidos/novo?msg_duplicado=Pedido+duplicado:+{ref_externa}", status_code=303)
        return templates.TemplateResponse(request=request, name="pedidos_novo.html", context={"error": str(e), "clientes": repo.get_clientes(), "produtos": repo.get_produtos()})
