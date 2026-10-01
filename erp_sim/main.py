import time
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from erp_sim import repo
from src.ipa.config import settings

app = FastAPI()
templates = Jinja2Templates(directory="erp_sim/templates")

@app.middleware("http")
async def sabotage_middleware(request: Request, call_next):
    if settings.erp_sabotage == "slow" and request.method == "POST":
        time.sleep(3)
    response = await call_next(request)
    return response

@app.get("/produtos", response_class=HTMLResponse)
def listar_produtos(request: Request):
    return templates.TemplateResponse("produtos.html", {"request": request, "produtos": repo.get_produtos()})

@app.get("/clientes", response_class=HTMLResponse)
def listar_clientes(request: Request):
    return templates.TemplateResponse("clientes.html", {"request": request, "clientes": repo.get_clientes()})

@app.get("/clientes/novo", response_class=HTMLResponse)
def form_cliente(request: Request):
    return templates.TemplateResponse("clientes_novo.html", {"request": request})

@app.post("/clientes/novo")
def criar_cliente(nome: str = Form(...), cnpj_cpf: str = Form(...), email: str = Form(...)):
    repo.criar_cliente(nome, cnpj_cpf, email)
    return RedirectResponse(url="/clientes?msg=Cliente+criado", status_code=303)

@app.get("/pedidos", response_class=HTMLResponse)
def listar_pedidos(request: Request, ref: str = None):
    return templates.TemplateResponse("pedidos.html", {"request": request, "pedidos": repo.get_pedidos(ref)})

@app.get("/pedidos/novo", response_class=HTMLResponse)
def form_pedido(request: Request):
    return templates.TemplateResponse("pedidos_novo.html", {"request": request, "clientes": repo.get_clientes(), "produtos": repo.get_produtos()})

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
        return templates.TemplateResponse("pedidos_novo.html", {"request": request, "error": "Adicione pelo menos 1 item.", "clientes": repo.get_clientes(), "produtos": repo.get_produtos()})
        
    try:
        pedido_id = repo.criar_pedido(cliente_id, data_entrega, observacoes, ref_externa, itens)
        return RedirectResponse(url=f"/pedidos/novo?msg_sucesso=Pedido+nº+{pedido_id}+criado", status_code=303)
    except Exception as e:
        err = str(e)
        if "erp_pedidos_ref_externa_key" in err or "duplicate key" in err:
            return RedirectResponse(url=f"/pedidos/novo?msg_duplicado=Pedido+duplicado:+{ref_externa}", status_code=303)
        return templates.TemplateResponse("pedidos_novo.html", {"request": request, "error": str(e), "clientes": repo.get_clientes(), "produtos": repo.get_produtos()})
