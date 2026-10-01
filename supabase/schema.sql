-- ===== ERP SIMULADO ("legado") =====
create table if not exists erp_clientes (
  id bigint generated always as identity primary key,
  nome text not null,
  cnpj_cpf text,
  email text,
  criado_em timestamptz not null default now()
);
create unique index if not exists erp_clientes_doc_uq
  on erp_clientes (cnpj_cpf) where cnpj_cpf is not null;

create table if not exists erp_produtos (
  id bigint generated always as identity primary key,
  codigo text not null unique,
  descricao text not null,
  unidade text not null default 'UN',
  preco numeric(12,2) not null check (preco >= 0)
);

create table if not exists erp_pedidos (
  id bigint generated always as identity primary key,   -- nº do pedido
  cliente_id bigint not null references erp_clientes(id),
  data_entrega date not null,
  observacoes text,
  ref_externa text unique,                               -- idempotência
  total numeric(12,2) not null default 0,
  criado_em timestamptz not null default now()
);

create table if not exists erp_pedido_itens (
  id bigint generated always as identity primary key,
  pedido_id bigint not null references erp_pedidos(id) on delete cascade,
  produto_id bigint not null references erp_produtos(id),
  quantidade numeric(12,3) not null check (quantidade > 0),
  preco_unit numeric(12,2) not null
);

-- Criação atômica do pedido (cabeçalho + itens + total)
create or replace function erp_criar_pedido(
  p_cliente_id bigint, p_data_entrega date, p_observacoes text,
  p_ref_externa text, p_itens jsonb
) returns bigint
language plpgsql
as $$
declare
  v_pedido_id bigint;
  v_total numeric(12,2) := 0;
  v_item jsonb;
  v_preco numeric(12,2);
  v_qtd numeric(12,3);
begin
  insert into erp_pedidos (cliente_id, data_entrega, observacoes, ref_externa)
  values (p_cliente_id, p_data_entrega, p_observacoes, p_ref_externa)
  returning id into v_pedido_id;

  for v_item in select * from jsonb_array_elements(p_itens) loop
    v_qtd := (v_item->>'quantidade')::numeric;
    select preco into v_preco from erp_produtos
      where id = (v_item->>'produto_id')::bigint;
    insert into erp_pedido_itens (pedido_id, produto_id, quantidade, preco_unit)
    values (v_pedido_id, (v_item->>'produto_id')::bigint, v_qtd, v_preco);
    v_total := v_total + v_preco * v_qtd;
  end loop;

  update erp_pedidos set total = v_total where id = v_pedido_id;
  return v_pedido_id;
end;
$$;

-- ===== IPA (orquestrador e métricas) =====
create table if not exists ipa_execucoes (
  id bigint generated always as identity primary key,
  run_id text not null,
  doc_id text not null,
  correlation_id text not null,
  split text,                 -- dev | teste
  categoria text,             -- limpo | ruidoso | adversarial
  classe text,
  rota text,                  -- AUTOMATICO | REVISAO | APROVACAO | REJEITAR
  status_final text,          -- sucesso | erro | duplicado | rejeitado
  ref_id text,
  numero_pedido bigint,
  limiar numeric(4,2),
  versao_prompt text,
  modelo text,
  executor text,              -- stub | rpa
  tempo_total_s numeric(10,3),
  criado_em timestamptz not null default now()
);

create table if not exists ipa_eventos (
  id bigint generated always as identity primary key,
  execucao_id bigint not null references ipa_execucoes(id) on delete cascade,
  etapa text not null,
  duracao_s numeric(10,3),
  resultado text,
  tokens_in integer,
  tokens_out integer,
  custo_equiv_usd numeric(12,6),
  tentativas integer,
  detalhe jsonb
);

create table if not exists ipa_extracoes (
  execucao_id bigint primary key references ipa_execucoes(id) on delete cascade,
  json_extraido jsonb not null,
  confianca jsonb,
  resolucao jsonb             -- etapa que resolveu cada item
);

create table if not exists ipa_revisoes (
  id bigint generated always as identity primary key,
  execucao_id bigint references ipa_execucoes(id) on delete cascade,
  tipo text not null,         -- REVISAO | APROVACAO
  motivo text,
  payload jsonb,
  status text not null default 'pendente',   -- pendente | resolvida
  correcao jsonb,
  simulada boolean not null default false,
  tempo_revisao_s numeric(10,3),
  criado_em timestamptz not null default now()
);

-- ===== SEGURANÇA: RLS ligado em tudo, sem políticas =====
alter table erp_clientes     enable row level security;
alter table erp_produtos     enable row level security;
alter table erp_pedidos      enable row level security;
alter table erp_pedido_itens enable row level security;
alter table ipa_execucoes    enable row level security;
alter table ipa_eventos      enable row level security;
alter table ipa_extracoes    enable row level security;
alter table ipa_revisoes     enable row level security;

-- Função não deve ser chamável por chaves públicas
revoke execute on function erp_criar_pedido(bigint, date, text, text, jsonb)
  from public, anon, authenticated;
grant execute on function erp_criar_pedido(bigint, date, text, text, jsonb)
  to service_role;
