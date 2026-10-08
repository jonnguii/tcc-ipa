import random
import unicodedata

def remover_acentos(txt: str) -> str:
    nfkd = unicodedata.normalize('NFKD', txt)
    return u"".join([c for c in nfkd if not unicodedata.combining(c)])

def aplicar_typos(txt: str) -> str:
    # Simula erros de digitação humanos aleatórios (trocar uma letra por outra)
    letras = list(txt)
    # 1 erro a cada 40 letras (bem grosseiro)
    num_erros = max(1, len(txt) // 40)
    for _ in range(num_erros):
        idx = random.randint(0, len(letras) - 1)
        if letras[idx].isalpha():
            letras[idx] = random.choice('abcdefghijklmnopqrstuvwxyz')
    return "".join(letras)

def sujar_texto(txt: str, categoria: str) -> str:
    # Apenas sujamos se for da categoria RUIDOSO
    if categoria != "RUIDOSO":
        return txt
    
    # Simula cliente que escreve tudo minúsculo e sem acento
    txt = remover_acentos(txt)
    txt = txt.lower()
    
    # Aplica erros de digitação ("dedos gordos no teclado")
    txt = aplicar_typos(txt)
    
    return txt
