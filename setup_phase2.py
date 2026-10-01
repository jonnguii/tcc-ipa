import os
from pathlib import Path

def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

write_file('src/ipa/config.py', '''from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    gemini_api_key: str = ""
    gemini_model: str = ""
    ai_mode: str = "record"
    executor: str = "stub"
    erp_base_url: str = "http://localhost:8000"
    erp_sabotage: str = "none"
    rpa_headless: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
''')

write_file('erp_sim/config.py', '''from src.ipa.config import settings
''')

write_file('erp_sim/db.py', '''from supabase import create_client, Client
from src.ipa.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
''')

write_file('erp_sim/seed_data.py', '''PRODUTOS = [
    {"codigo": f"P-{i:03d}", "descricao": f"Produto {i}", "unidade": "UN", "preco": i * 1.5} for i in range(1, 41)
]

CLIENTES = [
    {"nome": f"Cliente {i}", "cnpj_cpf": f"{i*11111111111111:014d}", "email": f"cliente{i}@example.com"} for i in range(1, 21)
]
''')

write_file('erp_sim/seed.py', '''from erp_sim.db import supabase
from erp_sim.seed_data import PRODUTOS, CLIENTES

def run_seed():
    print("Inserindo produtos...")
    for p in PRODUTOS:
        supabase.table("erp_produtos").upsert(p, on_conflict="codigo").execute()
    print("Inserindo clientes...")
    for c in CLIENTES:
        supabase.table("erp_clientes").upsert(c, on_conflict="cnpj_cpf").execute()
    print("Seed concluído!")

if __name__ == "__main__":
    run_seed()
''')

write_file('erp_sim/repo.py', '''from erp_sim.db import supabase

def get_produtos():
    return supabase.table("erp_produtos").select("*").order("id").execute().data

def get_clientes():
    return supabase.table("erp_clientes").select("*").order("id").execute().data

def get_cliente_by_cnpj(cnpj):
    res = supabase.table("erp_clientes").select("*").eq("cnpj_cpf", cnpj).execute().data
    return res[0] if res else None

def get_pedidos(ref=None):
    q = supabase.table("erp_pedidos").select("*, erp_clientes(nome)")
    if ref:
        q = q.eq("ref_externa", ref)
    return q.order("id").execute().data

def criar_cliente(nome, cnpj_cpf, email):
    res = supabase.table("erp_clientes").insert({"nome": nome, "cnpj_cpf": cnpj_cpf, "email": email}).execute()
    return res.data[0]

def criar_pedido(cliente_id, data_entrega, observacoes, ref_externa, itens):
    res = supabase.rpc("erp_criar_pedido", {
        "p_cliente_id": cliente_id,
        "p_data_entrega": data_entrega,
        "p_observacoes": observacoes,
        "p_ref_externa": ref_externa,
        "p_itens": itens
    }).execute()
    return res.data
''')

write_file('erp_sim/main.py', '''import time
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
''')

write_file('erp_sim/templates/base.html', '''<!DOCTYPE html>
<html>
<head>
<title>ERP Simulado</title>
<style>
body { font-family: sans-serif; padding: 20px; }
table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
.btn { padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
.msg-sucesso { color: green; font-weight: bold; margin-bottom: 10px; }
.msg-erro { color: red; font-weight: bold; margin-bottom: 10px; }
.msg-duplicado { color: orange; font-weight: bold; margin-bottom: 10px; }
</style>
</head>
<body>
<nav>
  <a href="/produtos">Produtos</a> | 
  <a href="/clientes">Clientes</a> | 
  <a href="/pedidos">Pedidos</a> | 
  <a href="/pedidos/novo">Novo Pedido</a>
</nav>
<hr>
{% block content %}{% endblock %}
</body>
</html>
''')

write_file('erp_sim/templates/produtos.html', '''{% extends "base.html" %}
{% block content %}
<h2>Produtos</h2>
<table>
  <tr><th>ID</th><th>Código</th><th>Descrição</th><th>Unidade</th><th>Preço</th></tr>
  {% for p in produtos %}
  <tr><td>{{ p.id }}</td><td>{{ p.codigo }}</td><td>{{ p.descricao }}</td><td>{{ p.unidade }}</td><td>{{ p.preco }}</td></tr>
  {% endfor %}
</table>
{% endblock %}
''')

write_file('erp_sim/templates/clientes.html', '''{% extends "base.html" %}
{% block content %}
<h2>Clientes</h2>
<a href="/clientes/novo" class="btn">Novo Cliente</a><br><br>
<table data-testid="tabela-clientes">
  <tr><th>ID</th><th>Nome</th><th>CNPJ/CPF</th><th>Email</th></tr>
  {% for c in clientes %}
  <tr><td>{{ c.id }}</td><td>{{ c.nome }}</td><td>{{ c.cnpj_cpf }}</td><td>{{ c.email }}</td></tr>
  {% endfor %}
</table>
{% endblock %}
''')

write_file('erp_sim/templates/clientes_novo.html', '''{% extends "base.html" %}
{% block content %}
<h2>Novo Cliente</h2>
<form method="POST" action="/clientes/novo">
  <label>Nome:</label><br>
  <input type="text" name="nome" data-testid="cli-nome" required><br><br>
  <label>CNPJ/CPF:</label><br>
  <input type="text" name="cnpj_cpf" data-testid="cli-cnpj"><br><br>
  <label>Email:</label><br>
  <input type="email" name="email" data-testid="cli-email"><br><br>
  <button type="submit" class="btn" data-testid="cli-salvar">Salvar</button>
</form>
{% endblock %}
''')

write_file('erp_sim/templates/pedidos.html', '''{% extends "base.html" %}
{% block content %}
<h2>Pedidos</h2>
<table data-testid="tabela-pedidos">
  <tr><th>Nº</th><th>Cliente</th><th>Data Entrega</th><th>Total</th><th>Ref Externa</th></tr>
  {% for p in pedidos %}
  <tr data-testid="linha-pedido-{{ p.id }}"><td>{{ p.id }}</td><td>{{ p.erp_clientes.nome }}</td><td>{{ p.data_entrega }}</td><td>{{ p.total }}</td><td>{{ p.ref_externa }}</td></tr>
  {% endfor %}
</table>
{% endblock %}
''')

write_file('erp_sim/templates/pedidos_novo.html', '''{% extends "base.html" %}
{% block content %}
<h2>Novo Pedido de Venda</h2>

{% if request.query_params.get("msg_sucesso") %}
<div class="msg-sucesso" data-testid="msg-sucesso">{{ request.query_params.get("msg_sucesso") }}</div>
{% endif %}
{% if request.query_params.get("msg_duplicado") %}
<div class="msg-duplicado" data-testid="msg-duplicado">{{ request.query_params.get("msg_duplicado") }}</div>
{% endif %}
{% if error %}
<div class="msg-erro" data-testid="msg-erro">{{ error }}</div>
{% endif %}

<form method="POST" action="/pedidos/novo">
  <label>Cliente:</label><br>
  <select name="cliente_id" data-testid="ped-cliente" required>
    <option value="">Selecione...</option>
    {% for c in clientes %}
    <option value="{{ c.id }}">{{ c.nome }} ({{ c.cnpj_cpf }})</option>
    {% endfor %}
  </select><br><br>

  <label>Data Entrega:</label><br>
  <input type="date" name="data_entrega" data-testid="ped-data" required><br><br>

  <label>Ref Externa:</label><br>
  <input type="text" name="ref_externa" data-testid="ped-ref"><br><br>

  <h3>Itens</h3>
  <table>
    <tr><th>Produto</th><th>Quantidade</th></tr>
    {% for i in range(1, 7) %}
    <tr>
      <td>
        <select name="produto_id_{{ i }}" data-testid="ped-linha-{{ i }}-produto">
          <option value="">Selecione...</option>
          {% for p in produtos %}
          <option value="{{ p.id }}">{{ p.codigo }} - {{ p.descricao }}</option>
          {% endfor %}
        </select>
      </td>
      <td>
        <input type="number" step="0.01" name="quantidade_{{ i }}" data-testid="ped-linha-{{ i }}-qtd">
      </td>
    </tr>
    {% endfor %}
  </table>

  <label>Observações:</label><br>
  <textarea name="observacoes" data-testid="ped-obs" rows="3" cols="40"></textarea><br><br>

  <button type="submit" class="btn" data-testid="ped-salvar">Salvar Pedido</button>
</form>
{% endblock %}
''')
print("Arquivos da Fase 2 criados com sucesso!")
