from erp_sim.db import supabase

def get_produtos():
    return supabase.table("erp_produtos").select("*").order("id").execute().data

def get_produto_by_id(produto_id):
    res = supabase.table("erp_produtos").select("*").eq("id", produto_id).execute().data
    return res[0] if res else None

def criar_produto(codigo, descricao, unidade, preco):
    res = supabase.table("erp_produtos").insert({
        "codigo": codigo,
        "descricao": descricao,
        "unidade": unidade,
        "preco": preco
    }).execute()
    return res.data[0]

def atualizar_produto(produto_id, codigo, descricao, unidade, preco):
    res = supabase.table("erp_produtos").update({
        "codigo": codigo,
        "descricao": descricao,
        "unidade": unidade,
        "preco": preco
    }).eq("id", produto_id).execute()
    return res.data[0] if res.data else None

def excluir_produto(produto_id):
    res = supabase.table("erp_produtos").delete().eq("id", produto_id).execute()
    return res.data

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

def get_cliente_by_id(cliente_id):
    res = supabase.table("erp_clientes").select("*").eq("id", cliente_id).execute().data
    return res[0] if res else None

def atualizar_cliente(cliente_id, nome, cnpj_cpf, email):
    res = supabase.table("erp_clientes").update({
        "nome": nome,
        "cnpj_cpf": cnpj_cpf,
        "email": email
    }).eq("id", cliente_id).execute()
    return res.data[0] if res.data else None

def excluir_cliente(cliente_id):
    res = supabase.table("erp_clientes").delete().eq("id", cliente_id).execute()
    return res.data

def criar_pedido(cliente_id, data_entrega, observacoes, ref_externa, itens):
    res = supabase.rpc("erp_criar_pedido", {
        "p_cliente_id": cliente_id,
        "p_data_entrega": data_entrega,
        "p_observacoes": observacoes,
        "p_ref_externa": ref_externa,
        "p_itens": itens
    }).execute()
    return res.data

def get_pedido_detalhes(pedido_id):
    pedido = supabase.table("erp_pedidos").select("*, erp_clientes(*)").eq("id", pedido_id).execute().data
    if not pedido:
        return None

    pedido = pedido[0]
    itens = supabase.table("erp_pedido_itens").select("*, erp_produtos(*)").eq("pedido_id", pedido_id).execute().data
    pedido["itens"] = itens
    return pedido
