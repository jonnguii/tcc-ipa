import time
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
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


# ===== Endpoints da Fila de Revisão Humana (Fase 9) =====
from pathlib import Path
from src.ipa.review import fila as fila_review
from src.ipa.rules.resolver import obter_catalogo_produtos
from src.ipa.workflow.engine import OrquestradorIPA
from src.ipa.executor import StubExecutor, RpaExecutor
from src.ipa.schemas import PedidoExtraido, ItemPedido, ClienteInfo


@app.get("/revisoes", response_class=HTMLResponse)
def listar_revisoes(request: Request, status: str | None = None):
    todas = fila_review.listar_pendencias(status=None)
    total_todos = len(todas)
    total_pendentes = sum(1 for r in todas if r.get("status") == "pendente")
    total_resolvidas = sum(1 for r in todas if r.get("status") == "resolvida")
    total_rejeitadas = sum(1 for r in todas if r.get("status") == "rejeitada")

    revisoes_filtradas = [r for r in todas if r.get("status") == status] if status else todas

    itens_formatados = []
    for r in revisoes_filtradas:
        p = r.get("payload") or {}
        ped_orig = p.get("pedido_original") or p
        cli = ped_orig.get("cliente") or p.get("cliente") or {}
        nome_cliente = (
            cli.get("nome")
            if isinstance(cli, dict)
            else getattr(cli, "nome", "Não identificado")
        ) or "Não identificado"
        ref_id = p.get("ref_id") or ped_orig.get("ref_id") or f"REV-{r.get('id')}"
        motivos = [m.strip() for m in (r.get("motivo") or "").split(";") if m.strip()]

        itens_formatados.append({
            **r,
            "ref_id_view": ref_id,
            "cliente_nome_view": nome_cliente,
            "motivos_lista": motivos,
        })

    return templates.TemplateResponse(
        request=request,
        name="revisoes_lista.html",
        context={
            "revisoes": itens_formatados,
            "status_filtro": status,
            "total_todos": total_todos,
            "total_pendentes": total_pendentes,
            "total_resolvidas": total_resolvidas,
            "total_rejeitadas": total_rejeitadas,
        },
    )


@app.get("/revisoes/{revisao_id}", response_class=HTMLResponse)
def detalhe_revisao(request: Request, revisao_id: int):
    revisao = fila_review.obter_pendencia(revisao_id)
    if not revisao:
        return RedirectResponse(url="/revisoes", status_code=303)

    payload = revisao.get("payload") or {}
    pedido_original = payload.get("pedido_original") or payload
    itens_analisados = payload.get("itens_analisados") or []
    doc_path = payload.get("_caminho_doc") or payload.get("documento")
    doc_conteudo = payload.get("_conteudo_bruto")
    doc_nome = Path(doc_path).name if doc_path else f"revisao_{revisao_id}"

    # Detecção do tipo de mídia e existência do arquivo (com fallback para data/inbox)
    doc_tipo = "outro"
    doc_existe = False
    if doc_path:
        p = Path(doc_path)
        ext = p.suffix.lower()
        if ext == ".pdf":
            doc_tipo = "pdf"
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            doc_tipo = "imagem"
        elif ext in (".txt", ".csv", ".json"):
            doc_tipo = "texto"

        if p.exists() or (Path("data/inbox") / p.name).exists():
            doc_existe = True

        if doc_tipo == "texto" and not doc_conteudo:
            arquivo_leitura = p if p.exists() else (Path("data/inbox") / p.name)
            if arquivo_leitura.exists():
                try:
                    doc_conteudo = arquivo_leitura.read_text(encoding="utf-8")
                except Exception:
                    pass

    catalogo = obter_catalogo_produtos()

    itens_view = []
    if itens_analisados:
        for it in itens_analisados:
            itens_view.append({
                "descricao_original": it.get("descricao_original") or it.get("descricao_bruta", ""),
                "codigo_resolvido": it.get("codigo_resolvido") or it.get("codigo_sugerido", ""),
                "score_fuzzy": it.get("score_similaridade") or it.get("confianca", 100.0),
                "quantidade": it.get("quantidade", 1),
                "preco_unitario": it.get("preco_unitario", 0.0),
            })
    else:
        for it in pedido_original.get("itens", []):
            itens_view.append({
                "descricao_original": it.get("descricao_bruta") or it.get("descricao", ""),
                "codigo_resolvido": it.get("codigo_produto", ""),
                "score_fuzzy": 100.0,
                "quantidade": it.get("quantidade", 1),
                "preco_unitario": it.get("preco_unitario", 0.0),
            })

    return templates.TemplateResponse(
        request=request,
        name="revisoes_detalhe.html",
        context={
            "revisao": revisao,
            "payload": payload,
            "pedido_original": pedido_original,
            "itens": itens_view,
            "catalogo": catalogo,
            "doc_nome": doc_nome,
            "doc_path": doc_path,
            "doc_conteudo": doc_conteudo,
            "doc_tipo": doc_tipo,
            "doc_existe": doc_existe,
        },
    )


@app.get("/revisoes/{revisao_id}/arquivo")
def obter_arquivo_revisao(revisao_id: int):
    """Serve o arquivo original anexado ao pedido para visualização na UI (PDF, imagem, texto)."""
    revisao = fila_review.obter_pendencia(revisao_id)
    if not revisao:
        raise HTTPException(status_code=404, detail="Revisão não encontrada")

    payload = revisao.get("payload") or {}
    doc_path = payload.get("_caminho_doc") or payload.get("documento")
    if not doc_path:
        raise HTTPException(status_code=404, detail="Nenhum arquivo associado a esta revisão")

    p = Path(doc_path)
    if not p.exists():
        # Fallback para o repositório em data/inbox caso tenha rodado em pasta temporária
        fallback = Path("data/inbox") / p.name
        if fallback.exists():
            p = fallback
        else:
            raise HTTPException(status_code=404, detail=f"Arquivo '{p.name}' não encontrado no disco")

    suffix = p.suffix.lower()
    media_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".txt": "text/plain; charset=utf-8",
        ".json": "application/json",
    }
    media_type = media_map.get(suffix, "application/octet-stream")
    return FileResponse(path=p, media_type=media_type, filename=p.name)


@app.post("/revisoes/{revisao_id}/decisao")
async def decisao_revisao(request: Request, revisao_id: int):
    form_data = await request.form()
    acao = str(form_data.get("acao", "aprovar")).lower()
    tempo_s_raw = form_data.get("tempo_revisao_s", "0")
    try:
        tempo_revisao_s = float(tempo_s_raw)
    except (ValueError, TypeError):
        tempo_revisao_s = 0.0

    if acao == "rejeitar":
        orquestrador = OrquestradorIPA(executor=StubExecutor())
        orquestrador.retomar_apos_revisao(
            revisao_id=revisao_id,
            acao="rejeitar",
            tempo_revisao_s=tempo_revisao_s,
        )
        return RedirectResponse(url=f"/revisoes/{revisao_id}", status_code=303)

    ref_id = str(form_data.get("ref_id", f"REV-{revisao_id}"))
    cliente_nome = str(form_data.get("cliente_nome", ""))
    cliente_doc = str(form_data.get("cliente_documento", ""))
    data_entrega = str(form_data.get("data_entrega", ""))

    itens_corrigidos = []
    idx = 0
    while f"item_codigo_{idx}" in form_data:
        cod = str(form_data.get(f"item_codigo_{idx}"))
        qtd = float(form_data.get(f"item_qtd_{idx}", 1))
        itens_corrigidos.append(
            ItemPedido(
                codigo=cod,
                quantidade=qtd,
            )
        )
        idx += 1

    pedido_corrigido = PedidoExtraido(
        ref_id=ref_id,
        cliente=ClienteInfo(nome=cliente_nome, cnpj_cpf=cliente_doc),
        data_entrega=data_entrega,
        itens=itens_corrigidos,
    )

    executor = RpaExecutor() if settings.executor == "rpa" else StubExecutor()
    orquestrador = OrquestradorIPA(executor=executor)
    orquestrador.retomar_apos_revisao(
        revisao_id=revisao_id,
        acao="aprovar",
        pedido_corrigido=pedido_corrigido,
        tempo_revisao_s=tempo_revisao_s,
    )

    return RedirectResponse(url=f"/revisoes/{revisao_id}", status_code=303)

