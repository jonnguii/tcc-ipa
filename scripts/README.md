# Scripts Utilitários do Projeto (`scripts/`)

Este diretório contém ferramentas auxiliares de manutenção, limpeza de ambiente e suporte operacional ao desenvolvimento do TCC-IPA.

---

## 1. Utilitário de Reset (`scripts/reset.py`)

O script [`scripts/reset.py`](file:///home/joaoguilherme/Desktop/projetos/tcc-ipa/scripts/reset.py) permite reiniciar o estado operacional do ambiente de testes de forma segura e controlada.

### Modos de Execução:

1. **Limpeza Completa (`--tudo` ou `-t`):**
   - Apaga todos os pedidos cadastrados no banco Supabase (`erp_pedidos` e itens em cascata).
   - Limpa a fila remota de revisões humanas (`ipa_revisoes`) e o arquivo local (`data/revisoes_local.json`).
   - Remove todos os screenshots de auditoria salvos pelo robô em `rpa/evidencias/`.
   - Zera o arquivo de cache de inteligência artificial (`.ai_cache.json`).
   ```bash
   uv run python scripts/reset.py --tudo
   ```

2. **Limpeza Operacional Preservando Cache (`--pedidos` ou `-p`):**
   - Apaga pedidos, revisões e evidências visuais no ERP, mas **mantém** o arquivo `.ai_cache.json` intacto.
   - Ideal para re-testar o robô RPA ou a tela de revisão humana sem gastar cota da API do Gemini.
   ```bash
   uv run python scripts/reset.py --pedidos
   ```

3. **Modo Interativo (Menu):**
   - Executar sem parâmetros exibe um menu interativo no terminal:
   ```bash
   uv run python scripts/reset.py
   ```
