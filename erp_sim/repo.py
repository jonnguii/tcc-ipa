from erp_sim.db import supabase

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
