import time
from playwright.sync_api import sync_playwright

def executar(pedido: dict) -> dict:
    """
    Recebe um dicionário 'pedido' padronizado e insere no ERP via tela.
    Retorna o status, tempo gasto, tentativas e caminho do screenshot.
    """
    inicio = time.perf_counter()
    tentativas = 1
    status = "erro"
    mensagem = None
    numero_pedido = None
    screenshot_path = f"rpa/evidencias/{pedido.get('ref_id', 'sem_ref')}.png"

    try:
        with sync_playwright() as p:
            # 1. Abre o navegador (headless=False para você ver o robô trabalhando)
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # 2. Checa Duplicidade
            ref_id = pedido.get("ref_id")
            page.goto(f"http://localhost:8000/pedidos?ref={ref_id}")
            # DICA: Verifique se a linha do pedido aparece na tabela. Se sim, é duplicado.

            # 3. Cadastra o Cliente se for novo
            cliente = pedido.get("cliente", {})
            if "novo" in cliente:
                # Navegue para http://localhost:8000/clientes/novo e cadastre
                pass

            # 4. Vai para a tela de novo pedido e preenche
            page.goto("http://localhost:8000/pedidos/novo")
            
            # --- COLE AQUI O CÓDIGO GERADO PELO PLAYWRIGHT CODEGEN ---
            # Exemplo:
            # page.get_by_test_id("ped-cliente").select_option("1")
            # page.get_by_test_id("ped-data").fill("2026-10-01")
            # ...
            # page.get_by_test_id("ped-salvar").click()
            # ---------------------------------------------------------

            # 5. Lê a mensagem de resultado na tela
            # if page.locator(".msg-sucesso").is_visible(): ...

            # 6. Tira screenshot final
            page.screenshot(path=screenshot_path)

            status = "sucesso" # Mude conforme a mensagem lida
            
            browser.close()

    except Exception as e:
        status = "erro"
        mensagem = str(e)
        # Tira screenshot do erro se a página estiver aberta
        
    fim = time.perf_counter()
    duracao_s = fim - inicio

    return {
        "ref_id": pedido.get("ref_id"),
        "status": status,
        "numero_pedido": numero_pedido,
        "duracao_s": duracao_s,
        "tentativas": tentativas,
        "screenshot": screenshot_path,
        "erro": mensagem
    }

if __name__ == "__main__":
    # Teste rápido local
    pedido_teste = {
        "ref_id": "PED-123",
        "cliente": {"id": 1},
        "data_entrega": "2026-12-01",
        "observacoes": "Teste de robô",
        "itens": [
            {"codigo": "P-001", "quantidade": 5.0}
        ]
    }
    resultado = executar(pedido_teste)
    print("Resultado:", resultado)
