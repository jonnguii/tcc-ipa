from pathlib import Path
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
    """
    
    conteudo = [prompt]
    arquivo_upload = None
    
    # Roteamento baseado na extensão do arquivo
    if path.suffix.lower() == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            texto = f.read()
        conteudo.append(f"\nMENSAGEM:\n{texto}")
    else:
        # É arquivo binário (PDF ou PNG)
        print(f"Fazendo upload temporário do {path.suffix.upper()} para o Gemini...")
        arquivo_upload = client.files.upload(file=str(path))
        conteudo.append(arquivo_upload)

    try:
        # Envia para a IA
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=conteudo,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PedidoExtraido,
            ),
        )
        
        resultado = PedidoExtraido.model_validate_json(response.text)
        
        # 2. Salva no cache para a próxima vez
        save_to_cache(caminho_arquivo, resultado)
        return resultado
        
    finally:
        # Limpeza: Sempre deletar arquivos do servidor do Google depois de usados!
        if arquivo_upload:
            client.files.delete(name=arquivo_upload.name)
            print("Arquivo apagado do servidor do Google.")
