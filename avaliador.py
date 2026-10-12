import json
import glob
import time
from pathlib import Path
from src.ipa.ai.extractor import processar_documento

def rodar_avaliacao():
    # Pega os 30 primeiros JSONs da pasta gold
    arquivos_gold = sorted(glob.glob("data/gold/*.json"))[:30]
    
    total = 0
    acertos = 0
    
    print("Iniciando avaliação do Gemini em 30 documentos (Vai devagar por causa da cota gratuita)...\n")
    
    for caminho_gold in arquivos_gold:
        path_g = Path(caminho_gold)
        doc_id = path_g.stem # DOC-0001
        
        # Encontra qual é o arquivo correspondente na inbox (.txt, .pdf ou .png)
        arquivo_inbox = glob.glob(f"data/inbox/{doc_id}.*")[0]
        
        # Abre o gabarito
        with open(caminho_gold, "r", encoding="utf-8") as f:
            gold_data = json.load(f)
            
        gabarito_itens = gold_data.get("pedido_verdade", {}).get("itens", [])
        gabarito_data = gold_data.get("pedido_verdade", {}).get("data_entrega", "")
        
        try:
            # Chama a IA
            resultado = processar_documento(arquivo_inbox)
            
            # Vamos testar de forma simples: A data bate? A quantidade de itens bate?
            data_ok = (resultado.data_entrega == gabarito_data)
            itens_ok = (len(resultado.itens) == len(gabarito_itens))
            
            if data_ok and itens_ok:
                print(f"[OK] {doc_id} -> IA extraiu com precisao")
                acertos += 1
            else:
                print(f"[ERRO] {doc_id} -> Erro de extracao. Data OK? {data_ok} | Itens OK? {itens_ok}")
                
        except Exception as e:
            print(f"[FALHA] {doc_id} -> Erro critico na IA: {e}")
            
        total += 1
        
        # Segredo para não tomar bloqueio na API gratuita: Pausa de 4 segundos
        time.sleep(4)
        
    taxa = (acertos / total) * 100
    print("\n" + "="*40)
    print(f"RESULTADO FINAL: {acertos}/{total} acertos ({taxa:.1f}% de Acurácia)")
    print("="*40)

if __name__ == "__main__":
    rodar_avaliacao()
