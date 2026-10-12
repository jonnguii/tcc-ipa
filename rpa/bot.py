import math
import re
import time
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

from src.ipa.config import settings

MAX_ITENS_PEDIDO = 6
import re
import time
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

from src.ipa.config import settings

MAX_ITENS_PEDIDO = 6
TIMEOUT_MS = 10_000


def _validar_pedido(pedido: Any) -> dict[str, Any]:
    if not isinstance(pedido, Mapping):
        raise ValueError("O pedido precisa ser um dicionário.")
    ref_id = pedido.get("ref_id")
    cliente = pedido.get("cliente")
    data_entrega = pedido.get("data_entrega")
    itens = pedido.get("itens")
    if not isinstance(ref_id, str) or not ref_id.strip():
        raise ValueError("Informe uma referência ref_id não vazia.")
    if not isinstance(cliente, Mapping):
        raise ValueError("O campo cliente precisa ser um dicionário.")
    cliente_id = cliente.get("id")
    if cliente_id is not None:
        if isinstance(cliente_id, bool) or not str(cliente_id).isdigit() or int(cliente_id) < 1:
            raise ValueError("O ID do cliente precisa ser um inteiro positivo.")
        cliente_ok: dict[str, Any] = {"id": int(cliente_id)}
    elif cliente.get("novo") is True:
        nome, email = cliente.get("nome"), cliente.get("email")
        documento = cliente.get("cnpj_cpf") or ""
        if not isinstance(nome, str) or len(nome.strip()) < 3:
            raise ValueError("Cliente novo precisa de nome com pelo menos 3 caracteres.")
        if not isinstance(email, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
            raise ValueError("Cliente novo precisa de e-mail válido.")
        if not isinstance(documento, str):
            raise ValueError("O CNPJ/CPF precisa ser texto.")
        cliente_ok = {"novo": True, "nome": nome.strip(), "cnpj_cpf": documento.strip(), "email": email.strip()}
    else:
        raise ValueError("Informe cliente.id ou cliente.novo=true com os dados cadastrais.")
    if not isinstance(data_entrega, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data_entrega):
        raise ValueError("A data precisa estar no formato YYYY-MM-DD.")
    try:
        date.fromisoformat(data_entrega)
    except ValueError as exc:
        raise ValueError("A data precisa estar no formato YYYY-MM-DD.") from exc
    observacoes = pedido.get("observacoes") or ""
    if not isinstance(observacoes, str):
        raise ValueError("As observações precisam ser texto.")
    if not isinstance(itens, list) or not 1 <= len(itens) <= MAX_ITENS_PEDIDO:
        raise ValueError(f"Informe de 1 a {MAX_ITENS_PEDIDO} itens.")
    itens_ok = []
    for indice, item in enumerate(itens, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"O item {indice} precisa ser um dicionário.")
        codigo, quantidade = item.get("codigo"), item.get("quantidade")
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError(f"O item {indice} precisa ter código de produto.")
        if isinstance(quantidade, bool):
            raise ValueError(f"A quantidade do item {indice} precisa ser positiva.")
        try:
            quantidade = float(quantidade)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"A quantidade do item {indice} precisa ser positiva.") from exc
        if not math.isfinite(quantidade) or quantidade <= 0:
            raise ValueError(f"A quantidade do item {indice} precisa ser positiva.")
        itens_ok.append({"codigo": codigo.strip(), "quantidade": quantidade})
    return {"ref_id": ref_id.strip(), "cliente": cliente_ok, "data_entrega": data_entrega,
            "observacoes": observacoes, "itens": itens_ok}


def _screenshot(page: Page, caminho: Path) -> str | None:
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(caminho), full_page=True)
        return str(caminho)
    except Exception:
        return None


def _buscar_pedido(page: Page, ref_id: str) -> Any | None:
    url = f"{settings.erp_base_url.rstrip('/')}/pedidos?{urlencode({'ref': ref_id})}"
    page.goto(url, wait_until="domcontentloaded")
    linhas = page.get_by_test_id("tabela-pedidos").locator("tbody tr")
    encontrados = []
    for indice in range(linhas.count()):
        linha = linhas.nth(indice)
        if linha.locator("td").nth(4).inner_text().strip() == ref_id:
            encontrados.append(linha)
    if len(encontrados) > 1:
        raise RuntimeError("O ERP retornou pedidos com referência duplicada.")
    return encontrados[0] if encontrados else None


def _numero_pedido(linha: Any) -> int | None:
    resultado = re.search(r"\d+", linha.locator("td").nth(0).inner_text())
    return int(resultado.group()) if resultado else None


def _id_cliente_existente(page: Page, cliente: Mapping[str, Any]) -> int | None:
    linhas = page.get_by_test_id("tabela-clientes").locator("tbody tr")
    documento = cliente.get("cnpj_cpf", "").strip()
    email = cliente.get("email", "").strip().casefold()
    encontrados = []
    for indice in range(linhas.count()):
        colunas = linhas.nth(indice).locator("td").all_inner_texts()
        if len(colunas) >= 4 and ((documento and colunas[2].strip() == documento)
                                  or (email and colunas[3].strip().casefold() == email)):
            encontrados.append(colunas[0].strip())
    if len(encontrados) > 1:
        raise RuntimeError("Não foi possível identificar um único cadastro de cliente.")
    resultado = re.search(r"\d+", encontrados[0]) if encontrados else None
    return int(resultado.group()) if resultado else None


def _resolver_cliente(page: Page, cliente: Mapping[str, Any]) -> int:
    if "id" in cliente:
        return int(cliente["id"])
    base_url = settings.erp_base_url.rstrip("/")
    page.goto(f"{base_url}/clientes", wait_until="domcontentloaded")
    cliente_id = _id_cliente_existente(page, cliente)
    if cliente_id is not None:
        return cliente_id
    page.goto(f"{base_url}/clientes/novo", wait_until="domcontentloaded")
    page.get_by_test_id("cli-nome").fill(cliente["nome"])
    if cliente["cnpj_cpf"]:
        page.get_by_test_id("cli-cnpj").fill(cliente["cnpj_cpf"])
    page.get_by_test_id("cli-email").fill(cliente["email"])
    page.get_by_test_id("cli-salvar").click()
    page.wait_for_url("**/clientes?*", timeout=TIMEOUT_MS)
    erro = page.get_by_test_id("msg-erro")
    if erro.count() and erro.is_visible():
        raise RuntimeError(f"O ERP recusou o cliente: {erro.inner_text().strip()}")
    cliente_id = _id_cliente_existente(page, cliente)
    if cliente_id is None:
        raise RuntimeError("O ERP não confirmou o cadastro do cliente.")
    return cliente_id


def _valor_produto(page: Page, indice: int, codigo: str) -> str:
    opcoes = page.get_by_test_id(f"ped-linha-{indice}-produto").locator("option")
    valores = []
    for posicao in range(opcoes.count()):
        opcao = opcoes.nth(posicao)
        if opcao.inner_text().strip().startswith(f"{codigo} - "):
            valor = opcao.get_attribute("value")
            if valor:
                valores.append(valor)
    if not valores:
        raise ValueError(f"Produto {codigo} não encontrado no ERP.")
    if len(valores) > 1:
        raise ValueError(f"Código de produto {codigo} duplicado no ERP.")
    return valores[0]


def executar(pedido: Mapping[str, Any]) -> dict[str, Any]:
    """Insere pela tela do ERP; não repete envios de resultado incerto."""
    inicio = time.perf_counter()
    ref_id = pedido.get("ref_id") if isinstance(pedido, Mapping) else None
    ref_id = ref_id.strip() if isinstance(ref_id, str) else None
    evidencia = None
    screenshot = None
    status, mensagem, numero = "erro", None, None
    page = browser = None
    try:
        pedido = _validar_pedido(pedido)
        ref_id = pedido["ref_id"]
        nome = re.sub(r"[^A-Za-z0-9._-]", "_", ref_id)[:100] or "sem_ref"
        evidencia = Path("rpa") / "evidencias" / f"{nome}.png"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=settings.rpa_headless)
            page = browser.new_page()
            page.set_default_timeout(TIMEOUT_MS)
            existente = _buscar_pedido(page, ref_id)
            if existente:
                status, numero = "duplicado", _numero_pedido(existente)
            else:
                base_url = settings.erp_base_url.rstrip("/")
                page.goto(f"{base_url}/pedidos/novo", wait_until="domcontentloaded")
                valores_produtos = [
                    _valor_produto(page, indice, item["codigo"])
                    for indice, item in enumerate(pedido["itens"], start=1)
                ]
                cliente_id = _resolver_cliente(page, pedido["cliente"])
                page.goto(f"{base_url}/pedidos/novo", wait_until="domcontentloaded")
                page.get_by_test_id("ped-cliente").select_option(value=str(cliente_id))
                page.get_by_test_id("ped-data").fill(pedido["data_entrega"])
                page.get_by_test_id("ped-ref").fill(ref_id)
                page.get_by_test_id("ped-obs").fill(pedido["observacoes"])
                for indice, (item, valor) in enumerate(zip(pedido["itens"], valores_produtos), start=1):
                    page.get_by_test_id(f"ped-linha-{indice}-produto").select_option(value=valor)
                    page.get_by_test_id(f"ped-linha-{indice}-qtd").fill(f"{item['quantidade']:g}")
                page.get_by_test_id("ped-salvar").click()
                sucesso = page.get_by_test_id("msg-sucesso")
                duplicado = page.get_by_test_id("msg-duplicado")
                if sucesso.count() and sucesso.is_visible():
                    status = "sucesso"
                    resultado = re.search(r"Pedido\s+n[ºo]\s*(\d+)", sucesso.inner_text())
                    numero = int(resultado.group(1)) if resultado else None
                else:
                    status = "duplicado" if duplicado.count() and duplicado.is_visible() else "erro"
                    erro = page.get_by_test_id("msg-erro")
                    if status == "erro" and erro.count() and erro.is_visible():
                        mensagem = erro.inner_text().strip()
                    confirmado = _buscar_pedido(page, ref_id)
                    if confirmado:
                        numero = _numero_pedido(confirmado)
                        if status != "duplicado":
                            status = "sucesso"
                    elif status == "erro":
                        mensagem = mensagem or "O ERP não confirmou a criação do pedido."
            screenshot = _screenshot(page, evidencia)
    except Exception as exc:
        mensagem = str(exc)
        if page is not None and evidencia is not None:
            screenshot = _screenshot(page, evidencia)
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
    return {"ref_id": ref_id, "status": status, "numero_pedido": numero,
            "duracao_s": round(time.perf_counter() - inicio, 3), "tentativas": 1,
            "screenshot": screenshot, "erro": mensagem}
