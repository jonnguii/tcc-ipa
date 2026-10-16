"""Script de suporte e protocolo para o Experimento 1 (EXP1 - Linha de Base Manual).
Conforme o Apêndice G do TCC:
- Seleciona 30 documentos do TESTE estratificados por categoria (sem prompt injection).
- Guia o participante no preenchimento manual do ERP (http://localhost:8000/pedidos/novo).
- Cronometra a operação com alta precisão e registra em results/raw/exp1_manual.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

raiz_projeto = Path(__file__).resolve().parents[1]
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))


def selecionar_documentos_exp1() -> list[str]:
    """Retorna os 30 documentos do conjunto TESTE para o EXP1 (estratificados, sem injeção)."""
    caminho_splits = raiz_projeto / "data" / "splits.json"
    if not caminho_splits.exists():
        raise FileNotFoundError("data/splits.json não encontrado.")

    splits_data = json.loads(caminho_splits.read_text(encoding="utf-8"))
    docs_teste = splits_data.get("teste", [])

    selecionados: list[str] = []
    for doc_id in docs_teste:
        gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
        if not gold_path.exists():
            continue
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        # Exclui ataques de prompt injection para medição de atendimento humano legítimo
        if "prompt_injection" in gold.get("flags", []):
            continue
        selecionados.append(doc_id)
        if len(selecionados) >= 30:
            break

    return selecionados


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta interativa de tempo manual para o EXP1")
    parser.add_argument("--participante", "-p", type=str, default="Participante 1", help="Nome ou identificador do operador.")
    parser.add_argument("--lote", "-l", type=int, choices=[1, 2, 3], default=1, help="Lote de 10 documentos (1: docs 1-10, 2: docs 11-20, 3: docs 21-30).")
    parser.add_argument("--simular", action="store_true", help="Gera dados sintéticos realistas para preenchimento de teste manual de base.")
    parser.add_argument("--reset", action="store_true", help="Zera o arquivo de resultados para iniciar uma nova coleta do zero.")
    args = parser.parse_args()

    todos_docs = selecionar_documentos_exp1()
    inicio = (args.lote - 1) * 10
    docs_lote = todos_docs[inicio : inicio + 10]

    csv_path = raiz_projeto / "results" / "raw" / "exp1_manual.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if args.reset and csv_path.exists():
        csv_path.unlink()
        print(f"🗑️ Arquivo {csv_path.name} resetado com sucesso para nova coleta!")

    # Se o arquivo atual contiver dados da simulação prévia ("Participante 1") e um operador real
    # estiver iniciando a coleta, salva backup do simulado e inicia o CSV limpo para a pessoa.
    if not args.simular and csv_path.exists() and csv_path.stat().st_size > 0:
        with open(csv_path, "r", encoding="utf-8") as f:
            linhas = [l for l in f.readlines() if l.strip()]
        if len(linhas) > 1 and "Participante 1" in linhas[1] and args.participante != "Participante 1":
            simulado_path = raiz_projeto / "results" / "raw" / "exp1_manual_simulado.csv"
            if not simulado_path.exists():
                import shutil
                shutil.copy2(csv_path, simulado_path)
            csv_path.unlink()
            print(f"ℹ️ Detectada coleta de operador real ('{args.participante}').")
            print(f"   Backup do baseline simulado preservado em: {simulado_path.name}")
            print(f"   Iniciando registro de dados empíricos reais limpos!\n")

    # Identifica documentos que já foram registrados pelo operador para permitir retomar de onde parou (sem duplicar)
    docs_ja_registrados: set[str] = set()
    if csv_path.exists() and csv_path.stat().st_size > 0:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    docs_ja_registrados.add(row[1].strip())

    arquivo_existe = csv_path.exists()

    if args.simular:
        import random
        random.seed(42 + args.lote)
        print(f"\n[EXP1] Gerando baseline manual simulado para {len(docs_lote)} documentos...")
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not arquivo_existe or csv_path.stat().st_size == 0:
                writer.writerow(["participante", "doc_id", "categoria", "tipo_arquivo", "tempo_s", "erros"])
            for doc_id in docs_lote:
                gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
                gold = json.loads(gold_path.read_text(encoding="utf-8"))
                cat = gold.get("categoria", "limpo")
                tipo = gold.get("tipo_arquivo", "txt")
                
                # Tempo manual realista em segundos (distribuição log-normal em torno de 45s a 110s)
                tempo_base = 45.0 if cat == "limpo" else (70.0 if cat == "ruidoso" else 95.0)
                if tipo in ("pdf", "png"):
                    tempo_base += 15.0
                tempo_s = round(tempo_base + random.uniform(-10.0, 25.0), 3)
                erros = 1 if (cat != "limpo" and random.random() < 0.20) else 0

                writer.writerow([args.participante, doc_id, cat, tipo, tempo_s, erros])
        print(f"✅ Baseline manual salvo em {csv_path.resolve()}\n")
        return

    print("\n" + "=" * 65)
    print(" EXP1: COLETA DE TEMPO MANUAL (LINHA DE BASE DO TCC)")
    print(f" Operador:      {args.participante}")
    print(f" Lote:          {args.lote} de 3 (Documentos {inicio + 1} a {inicio + 10} do conjunto TESTE)")
    print(" URL do ERP:    http://localhost:8000/pedidos/novo")
    print("=" * 65)
    print("Instruções para o Operador:")
    print("1. Abra a tela de 'Novo Pedido' no ERP.")
    print("2. A cada documento exibido, leia o pedido mostrado na tela ou abra o arquivo.")
    print("3. Pressione [ENTER] no terminal no momento em que começar a digitar.")
    print("4. Digite os dados na tela do ERP e clique em 'Salvar Pedido'.")
    print("5. Assim que o ERP salvar com sucesso, pressione [ENTER] no terminal.\n")

    input("Pressione [ENTER] quando estiver com o ERP aberto para começar...")

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not arquivo_existe or csv_path.stat().st_size == 0:
            writer.writerow(["participante", "doc_id", "categoria", "tipo_arquivo", "tempo_s", "erros"])

        for idx, doc_id in enumerate(docs_lote, start=1):
            if doc_id in docs_ja_registrados:
                print(f"[{idx}/10] ⏩ Documento {doc_id} já registrado anteriormente. Pulando...")
                continue

            gold_path = raiz_projeto / "data" / "gold" / f"{doc_id}.json"
            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            cat = gold.get("categoria", "limpo")
            tipo = gold.get("tipo_arquivo", "txt")
            caminho_doc = raiz_projeto / "data" / "inbox" / f"{doc_id}.{tipo}"

            print("\n" + "-" * 65)
            print(f"[{idx}/10] Documento do Teste: {doc_id} ({caminho_doc.name})")
            print(f"Arquivo: {caminho_doc}")

            if tipo == "txt" and caminho_doc.exists():
                conteudo_txt = caminho_doc.read_text(encoding="utf-8").strip()
                print("┌── [ CONTEÚDO DO PEDIDO ] ──────────────────────────────")
                for linha in conteudo_txt.splitlines():
                    print(f"│  {linha}")
                print("└────────────────────────────────────────────────────────")

            input("-> Pressione [ENTER] para INICIAR a cronometragem...")
            t_inicio = time.perf_counter()

            input("-> Digitando no ERP... Pressione [ENTER] assim que clicar em 'Salvar'...")
            duracao_s = round(time.perf_counter() - t_inicio, 3)

            print(f"✓ Concluído em {duracao_s:.2f} segundos!")
            erros_str = input("Houve algum erro/dúvida de digitação? (0 = Não, 1 = Sim) [default: 0]: ").strip()
            erros = 1 if erros_str == "1" else 0

            writer.writerow([args.participante, doc_id, cat, tipo, duracao_s, erros])
            f.flush()
            docs_ja_registrados.add(doc_id)

    print("\n" + "=" * 65)
    print(f"✅ Coleta do lote {args.lote} finalizada!")
    print(f"Dados registrados em: {csv_path.resolve()}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
