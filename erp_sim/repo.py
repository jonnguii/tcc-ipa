from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from erp_sim.db import supabase
from erp_sim.seed_data import CLIENTES as SEED_CLIENTES, PRODUTOS as SEED_PRODUTOS

logger = logging.getLogger(__name__)

# Fallback local em memória/disco se Supabase estiver inacessível (offline/sandbox)
_FALLBACK_FILE = Path("data/erp_pedidos_local.json")

_local_produtos: list[dict[str, Any]] = [
    {"id": i + 1, **p} for i, p in enumerate(SEED_PRODUTOS)
]
_local_clientes: list[dict[str, Any]] = [
    {"id": i + 1, **c} for i, c in enumerate(SEED_CLIENTES)
]
_local_pedidos: list[dict[str, Any]] = []


def _carregar_pedidos_locais() -> list[dict[str, Any]]:
    global _local_pedidos
    if _FALLBACK_FILE.exists():
        try:
            dados = json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
            if isinstance(dados, list):
                _local_pedidos = dados
                return _local_pedidos
        except Exception:
            pass

    # Se estiver vazio, popula com dados iniciais realistas para navegação
    if not _local_pedidos:
        _local_pedidos = [
            {
                "id": 101,
                "cliente_id": 1,
                "data_entrega": "2026-11-05",
                "total": 1450.00,
                "ref_externa": "DOC-0031",
                "observacoes": "Entregar na Doca 2. Pedido faturado automaticamente via Esteira Orquestradora IPA.",
                "criado_em": "2026-10-30 21:51:24",
                "erp_clientes": {"nome": "Distribuidora Alfa", "cnpj_cpf": "29.141.777/0001-58", "email": "contato1@empresa.com"},
                "itens": [
                    {"quantidade": 20.0, "preco_unit": 28.50, "erp_produtos": {"codigo": "P-001", "descricao": "Arroz Tipo 1 - Saco 5kg", "unidade": "UN"}},
                    {"quantidade": 40.0, "preco_unit": 8.50, "erp_produtos": {"codigo": "P-004", "descricao": "Feijão Preto Carioca - 1kg", "unidade": "UN"}},
                    {"quantidade": 60.0, "preco_unit": 6.80, "erp_produtos": {"codigo": "P-012", "descricao": "Óleo de Soja Refinado 900ml", "unidade": "UN"}},
                    {"quantidade": 10.0, "preco_unit": 13.20, "erp_produtos": {"codigo": "P-015", "descricao": "Açúcar Cristal Pacote 5kg", "unidade": "UN"}},
                ],
            },
            {
                "id": 102,
                "cliente_id": 2,
                "data_entrega": "2026-11-06",
                "total": 890.50,
                "ref_externa": "DOC-0032",
                "observacoes": "Pedido cadastrado via Robô RPA Playwright com idempotência confirmada.",
                "criado_em": "2026-10-30 21:51:35",
                "erp_clientes": {"nome": "Mercado Beta", "cnpj_cpf": "01.152.449/0001-38", "email": "contato2@empresa.com"},
                "itens": [
                    {"quantidade": 15.0, "preco_unit": 35.00, "erp_produtos": {"codigo": "P-002", "descricao": "Farinha de Trigo Especial 1kg", "unidade": "UN"}},
                    {"quantidade": 25.0, "preco_unit": 14.62, "erp_produtos": {"codigo": "P-008", "descricao": "Leite Integral UHT 1L", "unidade": "UN"}},
                ],
            },
            {
                "id": 103,
                "cliente_id": 4,
                "data_entrega": "2026-11-07",
                "total": 3120.00,
                "ref_externa": "DOC-0033",
                "observacoes": "Processado pelo motor de regras determinísticas.",
                "criado_em": "2026-10-30 21:51:48",
                "erp_clientes": {"nome": "Padaria Central", "cnpj_cpf": "34.167.211/0001-35", "email": "contato4@empresa.com"},
                "itens": [
                    {"quantidade": 50.0, "preco_unit": 45.00, "erp_produtos": {"codigo": "P-005", "descricao": "Café Torrado e Moído 500g", "unidade": "UN"}},
                    {"quantidade": 100.0, "preco_unit": 8.70, "erp_produtos": {"codigo": "P-010", "descricao": "Biscoito Cream Cracker 400g", "unidade": "UN"}},
                ],
            },
        ]
        _salvar_pedidos_locais()
    return _local_pedidos


def _salvar_pedidos_locais():
    try:
        _FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        _FALLBACK_FILE.write_text(
            json.dumps(_local_pedidos, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Erro ao salvar pedidos locais: %s", exc)


def get_produtos():
    try:
        return supabase.table("erp_produtos").select("*").order("id").execute().data
    except Exception as exc:
        logger.warning("Supabase inacessível em get_produtos (%s). Usando fallback local.", exc)
        return _local_produtos


def get_produto_by_id(produto_id: int):
    try:
        res = supabase.table("erp_produtos").select("*").eq("id", produto_id).execute().data
        return res[0] if res else None
    except Exception as exc:
        logger.warning("Supabase inacessível em get_produto_by_id (%s). Usando fallback local.", exc)
        for p in _local_produtos:
            if p["id"] == produto_id:
                return p
        return None


def criar_produto(codigo, descricao, unidade, preco):
    try:
        res = supabase.table("erp_produtos").insert({
            "codigo": codigo,
            "descricao": descricao,
            "unidade": unidade,
            "preco": preco,
        }).execute()
        return res.data[0]
    except Exception as exc:
        logger.warning("Supabase inacessível em criar_produto (%s). Gravando localmente.", exc)
        novo_id = max((p["id"] for p in _local_produtos), default=0) + 1
        item = {"id": novo_id, "codigo": codigo, "descricao": descricao, "unidade": unidade, "preco": preco}
        _local_produtos.append(item)
        return item


def atualizar_produto(produto_id, codigo, descricao, unidade, preco):
    try:
        res = supabase.table("erp_produtos").update({
            "codigo": codigo,
            "descricao": descricao,
            "unidade": unidade,
            "preco": preco,
        }).eq("id", produto_id).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.warning("Supabase inacessível em atualizar_produto (%s). Atualizando localmente.", exc)
        for p in _local_produtos:
            if p["id"] == produto_id:
                p.update({"codigo": codigo, "descricao": descricao, "unidade": unidade, "preco": preco})
                return p
        return None


def excluir_produto(produto_id):
    try:
        res = supabase.table("erp_produtos").delete().eq("id", produto_id).execute()
        return res.data
    except Exception as exc:
        logger.warning("Supabase inacessível em excluir_produto (%s).", exc)
        return []


def get_clientes():
    try:
        return supabase.table("erp_clientes").select("*").order("id").execute().data
    except Exception as exc:
        logger.warning("Supabase inacessível em get_clientes (%s). Usando fallback local.", exc)
        return _local_clientes


def get_cliente_by_cnpj(cnpj):
    try:
        res = supabase.table("erp_clientes").select("*").eq("cnpj_cpf", cnpj).execute().data
        return res[0] if res else None
    except Exception as exc:
        logger.warning("Supabase inacessível em get_cliente_by_cnpj (%s). Usando fallback local.", exc)
        for c in _local_clientes:
            if c.get("cnpj_cpf") == cnpj:
                return c
        return None


def get_pedidos(ref=None):
    try:
        q = supabase.table("erp_pedidos").select("*, erp_clientes(nome)")
        if ref:
            q = q.eq("ref_externa", ref)
        return q.order("id").execute().data
    except Exception as exc:
        logger.warning("Supabase inacessível em get_pedidos (%s). Usando fallback local.", exc)
        pedidos = _carregar_pedidos_locais()
        if ref:
            return [p for p in pedidos if p.get("ref_externa") == ref]
        return pedidos


def criar_cliente(nome, cnpj_cpf, email):
    try:
        res = supabase.table("erp_clientes").insert({"nome": nome, "cnpj_cpf": cnpj_cpf, "email": email}).execute()
        return res.data[0]
    except Exception as exc:
        logger.warning("Supabase inacessível em criar_cliente (%s). Gravando localmente.", exc)
        novo_id = max((c["id"] for c in _local_clientes), default=0) + 1
        cli = {"id": novo_id, "nome": nome, "cnpj_cpf": cnpj_cpf, "email": email}
        _local_clientes.append(cli)
        return cli


def get_cliente_by_id(cliente_id: int):
    try:
        res = supabase.table("erp_clientes").select("*").eq("id", cliente_id).execute().data
        return res[0] if res else None
    except Exception as exc:
        logger.warning("Supabase inacessível em get_cliente_by_id (%s). Usando fallback local.", exc)
        for c in _local_clientes:
            if c["id"] == cliente_id:
                return c
        return None


def atualizar_cliente(cliente_id, nome, cnpj_cpf, email):
    try:
        res = supabase.table("erp_clientes").update({
            "nome": nome,
            "cnpj_cpf": cnpj_cpf,
            "email": email,
        }).eq("id", cliente_id).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.warning("Supabase inacessível em atualizar_cliente (%s).", exc)
        for c in _local_clientes:
            if c["id"] == cliente_id:
                c.update({"nome": nome, "cnpj_cpf": cnpj_cpf, "email": email})
                return c
        return None


def excluir_cliente(cliente_id):
    try:
        res = supabase.table("erp_clientes").delete().eq("id", cliente_id).execute()
        return res.data
    except Exception as exc:
        logger.warning("Supabase inacessível em excluir_cliente (%s).", exc)
        return []


def criar_pedido(cliente_id, data_entrega, observacoes, ref_externa, itens):
    try:
        res = supabase.rpc("erp_criar_pedido", {
            "p_cliente_id": cliente_id,
            "p_data_entrega": data_entrega,
            "p_observacoes": observacoes,
            "p_ref_externa": ref_externa,
            "p_itens": itens,
        }).execute()
        return res.data
    except Exception as exc:
        err_msg = str(exc)
        if "erp_pedidos_ref_externa_key" in err_msg or "duplicate key" in err_msg:
            raise exc

        logger.warning("Supabase inacessível em criar_pedido (%s). Gravando localmente com garantia de idempotência.", exc)
        pedidos = _carregar_pedidos_locais()
        if any(p.get("ref_externa") == ref_externa for p in pedidos):
            raise Exception(f"duplicate key value violates unique constraint 'erp_pedidos_ref_externa_key' ({ref_externa})")

        novo_id = max((p["id"] for p in pedidos), default=100) + 1
        cli = get_cliente_by_id(cliente_id) or {"nome": f"Cliente #{cliente_id}", "cnpj_cpf": "-"}

        prod_map = {p["id"]: p for p in _local_produtos}
        itens_formatados = []
        total = 0.0
        for it in itens:
            pid = it.get("produto_id")
            qtd = float(it.get("quantidade", 1.0))
            prod = prod_map.get(pid, {"codigo": f"P-{pid:03d}", "descricao": f"Produto #{pid}", "unidade": "UN", "preco": 10.0})
            preco = float(prod.get("preco", 10.0))
            sub = qtd * preco
            total += sub
            itens_formatados.append({
                "quantidade": qtd,
                "preco_unit": preco,
                "erp_produtos": prod,
            })

        agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        pedido_obj = {
            "id": novo_id,
            "cliente_id": cliente_id,
            "data_entrega": str(data_entrega),
            "observacoes": observacoes or "",
            "ref_externa": ref_externa or f"PED-LOCAL-{novo_id}",
            "total": round(total, 2),
            "criado_em": agora,
            "erp_clientes": {"nome": cli.get("nome", "Cliente")},
            "itens": itens_formatados,
        }
        pedidos.insert(0, pedido_obj)
        _salvar_pedidos_locais()
        return novo_id


def get_pedido_detalhes(pedido_id: int):
    try:
        pedido = supabase.table("erp_pedidos").select("*, erp_clientes(*)").eq("id", pedido_id).execute().data
        if not pedido:
            return None

        pedido = pedido[0]
        itens = supabase.table("erp_pedido_itens").select("*, erp_produtos(*)").eq("pedido_id", pedido_id).execute().data
        pedido["itens"] = itens
        return pedido
    except Exception as exc:
        logger.warning("Supabase inacessível em get_pedido_detalhes (%s). Usando fallback local.", exc)
        pedidos = _carregar_pedidos_locais()
        for p in pedidos:
            if p["id"] == pedido_id:
                return p
        return None
