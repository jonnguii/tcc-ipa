import glob
from src.ipa.ai.extractor import processar_documento


# from src.ipa.ai.extractor import extrair_pedido_do_texto
# # Vamos ler o arquivo ruidoso que você gerou!
# caminho = "data/inbox/DOC-0008.txt"

# with open(caminho, "r", encoding="utf-8") as f:
#     texto = f.read()

# print(f"Lendo mensagem:\n{texto}\n")
# print("Enviando para o Gemini pensar...\n")

# resultado = extrair_pedido_do_texto(texto)

# print("SUCESSO! Objeto Pydantic extraído:")
# print(resultado.model_dump_json(indent=2))


# Procura o primeiro PDF que tiver lá na pasta
lista_pdfs = glob.glob("data/inbox/*.pdf")
caminho = lista_pdfs[0]
print(f"Enviando o documento {caminho} para o Gemini ver...")
resultado = processar_documento(caminho)
print("\nSUCESSO! Objeto Pydantic extraído a partir de um PDF:")
print(resultado.model_dump_json(indent=2))