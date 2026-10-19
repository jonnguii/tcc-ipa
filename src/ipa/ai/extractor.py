from pathlib import Path
import time
from google import genai
from google.genai import types
from src.ipa.config import settings
from src.ipa.schemas import PedidoExtraido
from src.ipa.ai.cache import check_cache, save_to_cache

# Inicia o cliente puxando a chave do seu .env
client = genai.Client(api_key=settings.gemini_api_key)

def processar_documento(caminho_arquivo: str) -> PedidoExtraido:
    """
    Identifica se é TXT, PDF ou PNG.
    - Se for TXT: lê o texto local e manda no prompt.
    - Se for PDF/PNG: faz upload do arquivo para o Gemini usar a "Visão", processa e depois apaga.
    """
    
    # 1. Verifica no cache primeiro!
    cache_result = check_cache(caminho_arquivo)
    if cache_result:
        return cache_result
        
    path = Path(caminho_arquivo)
    
    prompt = """
    Você é um agente de Intelligent Process Automation (IPA) de uma distribuidora.
    Leia a mensagem ou documento do cliente anexo.
    Extraia os dados solicitados e retorne estritamente o JSON estruturado.
    Atenção: No campo 'observacoes', transcreva fielmente quaisquer observações, notas de rodapé, avisos ou instruções presentes no documento original.
    """
    
    conteudo = [prompt]
    
    # Roteamento baseado na extensão do arquivo
    if path.suffix.lower() == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            texto = f.read()
        conteudo.append(f"\nMENSAGEM:\n{texto}")
    else:
        # Arquivo binário: envia inline via bytes sem passar pela Files API lenta
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".pdf": "application/pdf",
        }
        mime = mime_map.get(path.suffix.lower(), "application/octet-stream")
        with open(path, "rb") as f:
            dados_binarios = f.read()
        parte_binaria = types.Part.from_bytes(data=dados_binarios, mime_type=mime)
        conteudo.append(parte_binaria)

    # Envia para a IA com retry em caso de 503 (alta demanda) ou 429 (limite de taxa)
    modelos_para_tentar = [settings.gemini_model]
    if "flash-lite" not in settings.gemini_model:
        modelos_para_tentar.append("gemini-3.5-flash-lite")

    response = None
    ultimo_erro = None

    for modelo_atual in modelos_para_tentar:
        for tentativa in range(3):
            try:
                response = client.models.generate_content(
                    model=modelo_atual,
                    contents=conteudo,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PedidoExtraido,
                        temperature=0.1,
                    ),
                )
                if response and response.text:
                    break
            except Exception as e:
                ultimo_erro = e
                msg = str(e)
                if ("503" in msg or "429" in msg or "UNAVAILABLE" in msg) and tentativa < 2:
                    espera = (tentativa + 1) * 2
                    print(f"[AVISO] Gemini ocupado ({modelo_atual}). Aguardando {espera}s (tentativa {tentativa+1}/3)...")
                    time.sleep(espera)
                else:
                    break
        if response and response.text:
            break

    if not response or not response.text:
        raise ultimo_erro or RuntimeError("Resposta vazia da API do Gemini")
    
    resultado = PedidoExtraido.model_validate_json(response.text)
    
    # 2. Salva no cache para a próxima vez
    save_to_cache(caminho_arquivo, resultado)
    return resultado
