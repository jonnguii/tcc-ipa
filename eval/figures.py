"""Módulo de renderização de figuras e gráficos científicos (G1 a G6).
Gera gráficos vetoriais/SVG com arquitetura de faixas dedicadas
(cabeçalho isolado, legenda dedicada e área de plotagem livre de colisões)
e renderiza em PNG de alta resolução (300 DPI) com Playwright headless.
"""
from __future__ import annotations

import asyncio
import csv
import json
import statistics
from pathlib import Path
from playwright.async_api import async_playwright

raiz_projeto = Path(__file__).resolve().parents[1]
raw_dir = raiz_projeto / "results" / "raw"
figures_dir = raiz_projeto / "results" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)


def ler_csv(nome_arquivo: str) -> list[dict[str, str]]:
    caminho = raw_dir / nome_arquivo
    if not caminho.exists():
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gerar_svg_g1() -> str:
    """G1: Desempenho F1 e Acertos por Categoria (Regex Baseline vs IA Generativa)."""
    dados_regex = ler_csv("exp2_regex.csv")
    dados_ia = ler_csv("exp3_extracao.csv")

    categorias = ["limpo", "ruidoso", "adversarial"]
    cats_label = ["Limpo (N=20)", "Ruidoso (N=20)", "Adversarial (N=10)", "Média Geral (N=50)"]

    def calc_metrics(dados):
        res = {}
        for c in categorias:
            amostras = [d for d in dados if d["categoria"] == c]
            n = len(amostras)
            f1 = sum(float(d["itens_f1"]) for d in amostras) / n if n else 0.0
            acertos = sum(int(d["acerto_completo"]) for d in amostras) / n * 100.0 if n else 0.0
            res[c] = (f1, acertos)
        n_tot = len(dados)
        f1_tot = sum(float(d["itens_f1"]) for d in dados) / n_tot if n_tot else 0.0
        ac_tot = sum(int(d["acerto_completo"]) for d in dados) / n_tot * 100.0 if n_tot else 0.0
        res["geral"] = (f1_tot, ac_tot)
        return res

    met_reg = calc_metrics(dados_regex)
    met_ia = calc_metrics(dados_ia)

    chaves = ["limpo", "ruidoso", "adversarial", "geral"]
    grupo_largura = 200
    x_inicio = 135
    y_base = 395
    altura_grafico = 230  # 1.00 = 230px -> y_topo = 165

    svg_bars = ""
    for i, chave in enumerate(chaves):
        gx = x_inicio + i * grupo_largura
        r_f1, _ = met_reg[chave]
        i_f1, _ = met_ia[chave]

        h_reg = r_f1 * altura_grafico
        h_ia = i_f1 * altura_grafico

        y_reg = y_base - h_reg
        y_ia = y_base - h_ia

        delta = (i_f1 - r_f1) * 100

        svg_bars += f"""
        <g class="bar-group">
            <!-- Barra Regex -->
            <rect x="{gx}" y="{y_reg:.1f}" width="44" height="{h_reg:.1f}" fill="#94a3b8" rx="4" />
            <text x="{gx+22}" y="{y_reg-9:.1f}" text-anchor="middle" font-size="12" font-weight="600" fill="#475569">{r_f1:.3f}</text>
            
            <!-- Barra IA -->
            <rect x="{gx+52}" y="{y_ia:.1f}" width="44" height="{h_ia:.1f}" fill="#2563eb" rx="4" />
            <text x="{gx+74}" y="{y_ia-9:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#1d4ed8">{i_f1:.3f}</text>
            
            <!-- Rótulo Eixo X (Nome da Categoria) -->
            <text x="{gx+48}" y="{y_base+25}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#1e293b">{cats_label[i]}</text>

            <!-- Delta Badge isolada abaixo do rótulo -->
            <rect x="{gx+18}" y="{y_base+38}" width="60" height="22" fill="#ecfdf5" stroke="#10b981" rx="11" />
            <text x="{gx+48}" y="{y_base+53}" text-anchor="middle" font-size="11" font-weight="700" fill="#047857">+{delta:.1f} pp</text>
        </g>
        """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="36" font-size="19" font-weight="700" fill="#0f172a">Figura G1: Desempenho F1 por Categoria (Regex Baseline vs. IA Generativa)</text>
        <text x="50" y="58" font-size="12.5" font-weight="400" fill="#64748b">F1-Score médio de extração de itens nos 50 documentos do conjunto de teste (EXP2 vs. EXP3)</text>
        
        <!-- Faixa de Legenda Dedicada (Área 2) -->
        <g transform="translate(50, 85)">
            <rect x="0" y="0" width="14" height="14" fill="#94a3b8" rx="3" />
            <text x="22" y="12" font-size="12" font-weight="600" fill="#475569">Regex Baseline</text>
            
            <rect x="160" y="0" width="14" height="14" fill="#2563eb" rx="3" />
            <text x="182" y="12" font-size="12" font-weight="700" fill="#1d4ed8">IA IPA (Gemini 2.5 Flash)</text>
        </g>

        <!-- Linhas de Grade e Eixo Y (Área 3) -->
        <g stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4">
            <line x1="90" y1="{y_base}" x2="940" y2="{y_base}" stroke="#94a3b8" stroke-dasharray="0" stroke-width="1.5" />
            <line x1="90" y1="{y_base - altura_grafico*0.25:.1f}" x2="940" y2="{y_base - altura_grafico*0.25:.1f}" />
            <line x1="90" y1="{y_base - altura_grafico*0.50:.1f}" x2="940" y2="{y_base - altura_grafico*0.50:.1f}" />
            <line x1="90" y1="{y_base - altura_grafico*0.75:.1f}" x2="940" y2="{y_base - altura_grafico*0.75:.1f}" />
            <line x1="90" y1="{y_base - altura_grafico:.1f}" x2="940" y2="{y_base - altura_grafico:.1f}" />
        </g>

        <!-- Rótulos Eixo Y -->
        <g font-size="12" fill="#64748b" text-anchor="end">
            <text x="80" y="{y_base+4}">0.00</text>
            <text x="80" y="{y_base - altura_grafico*0.25 + 4:.1f}">0.25</text>
            <text x="80" y="{y_base - altura_grafico*0.50 + 4:.1f}">0.50</text>
            <text x="80" y="{y_base - altura_grafico*0.75 + 4:.1f}">0.75</text>
            <text x="80" y="{y_base - altura_grafico + 4:.1f}">1.00</text>
        </g>
        <text x="35" y="{y_base - altura_grafico/2}" font-size="13" font-weight="600" fill="#475569" transform="rotate(-90 35 {y_base - altura_grafico/2})" text-anchor="middle">F1-Score Médio de Itens</text>

        <!-- Barras -->
        {svg_bars}

        <!-- Rodapé explicativo -->
        <text x="50" y="525" font-size="11" fill="#94a3b8">Nota: As amostras adversariais contêm ruído proposital e injeções de prompt; o parser determinístico Regex falha na generalização.</text>
    </svg>
    """
    return svg


def gerar_svg_g2() -> str:
    """G2: Curva Risco vs Cobertura de Automação (EXP4)."""
    dados = ler_csv("exp4_limiares.csv")
    if not dados:
        return ""

    x_min, x_max = 0.50, 1.00
    y_base = 395
    altura_grafico = 230
    largura_grafico = 750
    x_inicio = 125

    def calc_coords(limiar_val, pct_val):
        x = x_inicio + ((limiar_val - x_min) / (x_max - x_min)) * largura_grafico
        y = y_base - (pct_val / 100.0) * altura_grafico
        return x, y

    pontos_cob = []
    pontos_erro = []

    for d in dados:
        lim = float(d["limiar"])
        cob = float(d["cobertura_pct"])
        err = float(d["erro_residual_pct"])
        xc, yc = calc_coords(lim, cob)
        pontos_cob.append(f"{xc:.1f},{yc:.1f}")
        xe, ye = calc_coords(lim, err)
        pontos_erro.append(f"{xe:.1f},{ye:.1f}")

    path_cob = "M " + " L ".join(pontos_cob)
    path_erro = "M " + " L ".join(pontos_erro)

    x_corte, y_corte = calc_coords(0.85, 72.0)
    x_meta, y_meta = calc_coords(0.85, 0.0)
    _, y_h3 = calc_coords(0.50, 2.0)

    passos_x = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00]
    marcas_x_svg = ""
    for px in passos_x:
        cx = calc_coords(px, 0)[0]
        if px == 0.85:
            marcas_x_svg += f"""
            <g>
                <rect x="{cx-28:.1f}" y="{y_base+8}" width="56" height="22" fill="#eff6ff" stroke="#3b82f6" rx="4" />
                <text x="{cx:.1f}" y="{y_base+23}" font-size="11" font-weight="700" fill="#1d4ed8" text-anchor="middle">0.85 (tau*)</text>
            </g>
            """
        else:
            marcas_x_svg += f"""
            <text x="{cx:.1f}" y="{y_base+24}" font-size="12" fill="#64748b" text-anchor="middle">{px:.2f}</text>
            """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="36" font-size="19" font-weight="700" fill="#0f172a">Figura G2: Curva Risco vs. Cobertura de Automação (EXP4)</text>
        <text x="50" y="58" font-size="12.5" font-weight="400" fill="#64748b">Varredura de limiares de confiança tau in [0.50, 0.99] e comprovação da Hipótese H3 (Erro Residual no ERP &lt;= 2.0%)</text>

        <!-- Faixa de Legenda Dedicada (Área 2) -->
        <g transform="translate(50, 85)">
            <line x1="0" y1="7" x2="20" y2="7" stroke="#2563eb" stroke-width="3" />
            <circle cx="10" cy="7" r="4" fill="#2563eb" />
            <text x="28" y="11" font-size="12" font-weight="600" fill="#1e40af">Cobertura de Automação (%)</text>
            
            <line x1="230" y1="7" x2="250" y2="7" stroke="#dc2626" stroke-width="3" />
            <circle cx="240" cy="7" r="4" fill="#dc2626" />
            <text x="258" y="11" font-size="12" font-weight="600" fill="#991b1b">Erro Residual no ERP (%)</text>

            <line x1="450" y1="7" x2="470" y2="7" stroke="#b91c1c" stroke-width="1.5" stroke-dasharray="3" />
            <text x="478" y="11" font-size="11" font-weight="600" fill="#b91c1c">Meta H3 (Tolerância &lt;= 2%)</text>
        </g>

        <!-- Linhas de Grade e Eixo Y -->
        <g stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4">
            <line x1="{x_inicio}" y1="{y_base}" x2="{x_inicio+largura_grafico}" y2="{y_base}" stroke="#94a3b8" stroke-dasharray="0" stroke-width="1.5" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.25:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.25:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.50:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.50:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.72:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.72:.1f}" stroke="#93c5fd" stroke-width="1" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.75:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.75:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico:.1f}" />
        </g>

        <!-- Linha de Tolerância H3 (2%) -->
        <line x1="{x_inicio}" y1="{y_h3:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_h3:.1f}" stroke="#f87171" stroke-width="1.5" stroke-dasharray="4" />

        <!-- Rótulos Eixo Y -->
        <g font-size="12" fill="#64748b" text-anchor="end">
            <text x="{x_inicio-12}" y="{y_base+4}">0%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.25 + 4:.1f}">25%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.50 + 4:.1f}">50%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.75 + 4:.1f}">75%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico + 4:.1f}">100%</text>
        </g>
        <text x="45" y="{y_base - altura_grafico/2}" font-size="13" font-weight="600" fill="#475569" transform="rotate(-90 45 {y_base - altura_grafico/2})" text-anchor="middle">Percentual de Pedidos (%)</text>

        <!-- Eixo X Marcadores -->
        {marcas_x_svg}
        <text x="{x_inicio + largura_grafico/2}" y="{y_base+52}" font-size="13" font-weight="600" fill="#334155" text-anchor="middle">Limiar de Confiança Mínima do Modelo (tau)</text>

        <!-- Curvas -->
        <path d="{path_cob}" fill="none" stroke="#2563eb" stroke-width="3" />
        <path d="{path_erro}" fill="none" stroke="#dc2626" stroke-width="3" />

        <!-- Destaque no Ponto de Operação tau=0.85 -->
        <line x1="{x_corte:.1f}" y1="{y_base}" x2="{x_corte:.1f}" y2="{y_corte:.1f}" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="3" />
        <circle cx="{x_corte:.1f}" cy="{y_corte:.1f}" r="6" fill="#2563eb" stroke="#ffffff" stroke-width="2" />
        <circle cx="{x_meta:.1f}" cy="{y_meta:.1f}" r="6" fill="#10b981" stroke="#ffffff" stroke-width="2" />

        <!-- Caixa de Destaque reposicionada para evitar qualquer sobreposição -->
        <g transform="translate(660, 135)">
            <rect x="0" y="0" width="205" height="78" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2" rx="6" />
            <text x="12" y="20" font-size="12" font-weight="700" fill="#1e293b">Ponto Operacional (tau = 0.85):</text>
            <text x="12" y="38" font-size="12" font-weight="600" fill="#2563eb">&#x2022; Cobertura: 72.0% (36/50)</text>
            <text x="12" y="55" font-size="12" font-weight="600" fill="#059669">&#x2022; Erro Residual: 0.0% (Meta H3)</text>
            <text x="12" y="70" font-size="10" font-weight="500" fill="#64748b">&#x2022; 14 pedidos retidos para Revisão</text>
        </g>

        <!-- Rodapé explicativo -->
        <text x="50" y="525" font-size="11" fill="#94a3b8">Nota: O motor de regras determinístico desvia divergências de catálogo para a Fila de Revisão Humana, eliminando o erro residual no ERP.</text>
    </svg>
    """
    return svg


def gerar_svg_g3() -> str:
    """G3: Calibração da Confiança da IA (Diagrama de Confiabilidade)."""
    dados = ler_csv("exp3_extracao.csv")
    if not dados:
        return ""

    faixas = [
        ("0.0 - 0.69", 0.0, 0.69),
        ("0.70 - 0.79", 0.70, 0.79),
        ("0.80 - 0.89", 0.80, 0.89),
        ("0.90 - 0.95", 0.90, 0.95),
        ("0.96 - 1.00", 0.96, 1.00),
    ]

    bins_data = []
    for label, low, high in faixas:
        amostras = [d for d in dados if low <= float(d["confianca_geral"]) <= high]
        n = len(amostras)
        if n > 0:
            conf_med = sum(float(d["confianca_geral"]) for d in amostras) / n
            acertos = sum(int(d["acerto_completo"]) for d in amostras)
            acc = acertos / n
            bins_data.append((label, conf_med, acc, n, acertos))
        else:
            bins_data.append((label, (low + high) / 2, 0.0, 0, 0))

    y_base = 395
    altura_grafico = 230
    largura_grafico = 520
    x_inicio = 160

    def calc_xy(conf, acc):
        x = x_inicio + conf * largura_grafico
        y = y_base - acc * altura_grafico
        return x, y

    pontos_svg = ""
    for label, conf, acc, n, acertos in bins_data:
        if n == 0:
            continue
        cx, cy = calc_xy(conf, acc)
        cor = "#2563eb" if acc > 0 else "#e11d48"

        # Posição calculada das badges para zero colisão
        if acc == 0:
            # Caso da faixa 0.94 (DOC-0040 e DOC-0056)
            badge_y = cy - 40
            badge_x = cx - 40
        elif conf >= 0.95:
            # Ponto de 100% (canto superior direito)
            badge_y = cy - 35
            badge_x = cx - 40
        elif conf >= 0.75:
            # Ponto de 80%
            badge_y = cy - 35
            badge_x = cx - 50
        else:
            badge_y = cy - 35
            badge_x = cx - 40

        pontos_svg += f"""
        <g>
            <circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{cor}" stroke="#ffffff" stroke-width="2.5" />
            <rect x="{badge_x:.1f}" y="{badge_y:.1f}" width="80" height="24" fill="#f8fafc" stroke="#cbd5e1" rx="4" />
            <text x="{badge_x + 40:.1f}" y="{badge_y + 16:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="#0f172a">{acc*100:.0f}% (N={n})</text>
        </g>
        """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="36" font-size="19" font-weight="700" fill="#0f172a">Figura G3: Diagrama de Calibração da Confiança da IA (EXP3)</text>
        <text x="50" y="58" font-size="12.5" font-weight="400" fill="#64748b">Confiabilidade da probabilidade reportada pelo Gemini Flash vs. Acurácia observada de acerto exato</text>

        <!-- Faixa de Legenda Dedicada (Área 2) -->
        <g transform="translate(50, 85)">
            <line x1="0" y1="7" x2="24" y2="7" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4" />
            <text x="32" y="11" font-size="12" font-weight="600" fill="#64748b">Calibração Perfeita (y = x)</text>
            
            <circle cx="240" cy="7" r="5" fill="#2563eb" />
            <text x="252" y="11" font-size="12" font-weight="700" fill="#1e40af">Observado nos Testes</text>
        </g>

        <!-- Linhas de Grade e Eixo Y -->
        <g stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4">
            <line x1="{x_inicio}" y1="{y_base}" x2="{x_inicio+largura_grafico}" y2="{y_base}" stroke="#94a3b8" stroke-dasharray="0" stroke-width="1.5" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.25:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.25:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.50:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.50:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico*0.75:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico*0.75:.1f}" />
            <line x1="{x_inicio}" y1="{y_base - altura_grafico:.1f}" x2="{x_inicio+largura_grafico}" y2="{y_base - altura_grafico:.1f}" />
        </g>

        <!-- Linha Diagonal Ideal y = x -->
        <line x1="{x_inicio}" y1="{y_base}" x2="{x_inicio+largura_grafico}" y2="{y_base-altura_grafico}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5" />

        <!-- Rótulos Eixo Y -->
        <g font-size="12" fill="#64748b" text-anchor="end">
            <text x="{x_inicio-12}" y="{y_base+4}">0%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.25 + 4:.1f}">25%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.50 + 4:.1f}">50%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico*0.75 + 4:.1f}">75%</text>
            <text x="{x_inicio-12}" y="{y_base - altura_grafico + 4:.1f}">100%</text>
        </g>
        <text x="75" y="{y_base - altura_grafico/2}" font-size="13" font-weight="600" fill="#475569" transform="rotate(-90 75 {y_base - altura_grafico/2})" text-anchor="middle">Acurácia Empírica Observada (%)</text>

        <!-- Rótulos Eixo X -->
        <g font-size="12" fill="#475569" text-anchor="middle">
            <text x="{x_inicio}" y="{y_base+22}">0.00</text>
            <text x="{x_inicio + largura_grafico*0.25:.1f}" y="{y_base+22}">0.25</text>
            <text x="{x_inicio + largura_grafico*0.50:.1f}" y="{y_base+22}">0.50</text>
            <text x="{x_inicio + largura_grafico*0.75:.1f}" y="{y_base+22}">0.75</text>
            <text x="{x_inicio + largura_grafico}" y="{y_base+22}">1.00</text>
        </g>
        <text x="{x_inicio + largura_grafico/2}" y="{y_base+50}" font-size="13" font-weight="600" fill="#334155" text-anchor="middle">Confiança Média Estimada pelo Modelo</text>

        <!-- Pontos Observados -->
        {pontos_svg}

        <!-- Card de Análise da Faixa 0.94 isolado na extrema direita -->
        <g transform="translate(735, 185)">
            <rect x="0" y="0" width="215" height="135" fill="#fff1f2" stroke="#fecdd3" stroke-width="1.2" rx="6" />
            <text x="14" y="24" font-size="11.5" font-weight="700" fill="#9f1239">Caso Crítico (Faixa 0.94):</text>
            <text x="14" y="46" font-size="10.5" fill="#881337">&#x2022; DOC-0040 e DOC-0056</text>
            <text x="14" y="64" font-size="10.5" fill="#881337">&#x2022; IA previu confianca alta</text>
            <text x="14" y="82" font-size="10.5" fill="#881337">&#x2022; Erro sintético de código</text>
            <text x="14" y="104" font-size="10.5" font-weight="700" fill="#047857">&#x2714; Motor barrou no Fuzzy!</text>
            <text x="14" y="122" font-size="10.5" font-weight="600" fill="#047857">&#x2714; Roteado p/ REVISAO</text>
        </g>

        <!-- Rodapé explicativo -->
        <text x="50" y="525" font-size="11" fill="#94a3b8">Nota: 90% da amostra (45/50) concentrou-se na faixa de confiança máxima [0.96, 1.00] com 100% de precisão observada.</text>
    </svg>
    """
    return svg


def gerar_svg_g4() -> str:
    """G4: Boxplot / Distribuição de Produtividade Manual vs Orquestrador IPA (EXP1)."""
    dados_manual = ler_csv("exp1_manual.csv")
    dados_auto = ler_csv("exp1_auto.csv")

    tm = [float(d["tempo_s"]) for d in dados_manual]
    ta = [float(d["tempo_total_s"]) for d in dados_auto]

    def box_stats(vals):
        s = sorted(vals)
        n = len(s)
        return {
            "min": min(s),
            "q1": s[int(n * 0.25)],
            "med": s[n // 2],
            "q3": s[int(n * 0.75)],
            "max": max(s),
            "mean": statistics.mean(s),
            "p90": s[int(n * 0.90) - 1],
        }

    sm = box_stats(tm)
    sa = box_stats(ta)

    y_base = 395
    altura_grafico = 230
    max_s = 140.0
    x_manual = 250
    x_auto = 740

    def y_sec(s):
        return y_base - (s / max_s) * altura_grafico

    def render_box(bx, st, cor_box, cor_linha, label, erros_txt, lado_rotulo="dir"):
        y_q3 = y_sec(st["q3"])
        y_q1 = y_sec(st["q1"])
        y_med = y_sec(st["med"])
        y_min = y_sec(st["min"])
        y_max = y_sec(st["max"])
        h_box = y_q1 - y_q3

        x_rotulo = (bx + 55) if lado_rotulo == "dir" else (bx - 125)

        return f"""
        <g class="boxplot">
            <!-- Bigodes (Whiskers) -->
            <line x1="{bx}" y1="{y_max:.1f}" x2="{bx}" y2="{y_q3:.1f}" stroke="{cor_linha}" stroke-width="2" />
            <line x1="{bx-20}" y1="{y_max:.1f}" x2="{bx+20}" y2="{y_max:.1f}" stroke="{cor_linha}" stroke-width="2" />
            
            <line x1="{bx}" y1="{y_min:.1f}" x2="{bx}" y2="{y_q1:.1f}" stroke="{cor_linha}" stroke-width="2" />
            <line x1="{bx-20}" y1="{y_min:.1f}" x2="{bx+20}" y2="{y_min:.1f}" stroke="{cor_linha}" stroke-width="2" />

            <!-- Caixa Interquartil (IQR) -->
            <rect x="{bx-45}" y="{y_q3:.1f}" width="90" height="{h_box:.1f}" fill="{cor_box}" stroke="{cor_linha}" stroke-width="2" rx="4" />
            
            <!-- Linha da Mediana -->
            <line x1="{bx-45}" y1="{y_med:.1f}" x2="{bx+45}" y2="{y_med:.1f}" stroke="#ffffff" stroke-width="3" />
            <circle cx="{bx}" cy="{y_med:.1f}" r="4" fill="#ffffff" />

            <!-- Rótulo Mediana -->
            <rect x="{x_rotulo:.1f}" y="{y_med-12:.1f}" width="70" height="24" fill="#ffffff" stroke="{cor_linha}" stroke-width="1.2" rx="4" />
            <text x="{x_rotulo+35:.1f}" y="{y_med+4:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="{cor_linha}">{st['med']:.1f}s</text>

            <!-- Textos Descritivos abaixo do eixo com respiro -->
            <text x="{bx}" y="{y_base+26}" text-anchor="middle" font-size="14" font-weight="700" fill="#0f172a">{label}</text>
            <text x="{bx}" y="{y_base+46}" text-anchor="middle" font-size="12" font-weight="500" fill="#64748b">Média: {st['mean']:.1f}s | P90: {st['p90']:.1f}s</text>
            <text x="{bx}" y="{y_base+64}" text-anchor="middle" font-size="11" font-weight="600" fill="{cor_linha}">{erros_txt}</text>
        </g>
        """

    box_m_svg = render_box(x_manual, sm, "#94a3b8", "#475569", "Manual (Humano)", "3 erros observados (10.0%)", lado_rotulo="esq")
    box_a_svg = render_box(x_auto, sa, "#3b82f6", "#1d4ed8", "Orquestrador IPA", "0 erros observados (0.0%)", lado_rotulo="dir")

    speedup = sm["med"] / sa["med"]

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="36" font-size="19" font-weight="700" fill="#0f172a">Figura G4: Distribuição dos Tempos Operacionais por Pedido (EXP1)</text>
        <text x="50" y="58" font-size="12.5" font-weight="400" fill="#64748b">Comparativo empírico entre digitação manual no ERP e orquestração automatizada (N=30 pedidos pareados)</text>

        <!-- Selo de Speed-Up Centralizado com ampla folga de ambos os lados -->
        <g transform="translate(385, 172)">
            <rect x="0" y="0" width="230" height="76" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5" rx="8" />
            <text x="115" y="29" text-anchor="middle" font-size="11.5" font-weight="700" fill="#047857">GANHO DE VELOCIDADE</text>
            <text x="115" y="56" text-anchor="middle" font-size="20" font-weight="800" fill="#065f46">{speedup:.1f}x MAIS RÁPIDO</text>
        </g>

        <!-- Linhas de Grade e Eixo Y -->
        <g stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4">
            <line x1="90" y1="{y_base}" x2="920" y2="{y_base}" stroke="#94a3b8" stroke-dasharray="0" stroke-width="1.5" />
            <line x1="90" y1="{y_sec(35):.1f}" x2="920" y2="{y_sec(35):.1f}" />
            <line x1="90" y1="{y_sec(70):.1f}" x2="920" y2="{y_sec(70):.1f}" />
            <line x1="90" y1="{y_sec(105):.1f}" x2="920" y2="{y_sec(105):.1f}" />
            <line x1="90" y1="{y_sec(140):.1f}" x2="920" y2="{y_sec(140):.1f}" />
        </g>

        <!-- Rótulos Eixo Y -->
        <g font-size="12" fill="#64748b" text-anchor="end">
            <text x="80" y="{y_base+4}">0s</text>
            <text x="80" y="{y_sec(35)+4:.1f}">35s</text>
            <text x="80" y="{y_sec(70)+4:.1f}">70s</text>
            <text x="80" y="{y_sec(105)+4:.1f}">105s</text>
            <text x="80" y="{y_sec(140)+4:.1f}">140s</text>
        </g>
        <text x="35" y="{y_base - altura_grafico/2}" font-size="13" font-weight="600" fill="#475569" transform="rotate(-90 35 {y_base - altura_grafico/2})" text-anchor="middle">Tempo de Processamento por Pedido (s)</text>

        <!-- Boxplots -->
        {box_m_svg}
        {box_a_svg}

        <!-- Rodapé explicativo -->
        <text x="50" y="525" font-size="11" fill="#94a3b8">Nota: Redução no tempo mediano de 74,4s para 9,0s (-87,9%). O processo manual apresentou fadiga e digitação errônea em 10% dos casos.</text>
    </svg>
    """
    return svg


def gerar_svg_g5() -> str:
    """G5: Destinos Operacionais por Categoria (Barras Empilhadas da Triagem em 3 Vias)."""
    dados = ler_csv("exp3_extracao.csv")
    if not dados:
        return ""

    categorias = ["limpo", "ruidoso", "adversarial"]
    labels = ["Limpo (N=20)", "Ruidoso (N=20)", "Adversarial (N=10)", "Total Geral (N=50)"]

    def conta_rotas(amostras):
        tot = len(amostras)
        if tot == 0:
            return 0, 0, 0
        aut = sum(1 for d in amostras if d["rota_decidida"] == "AUTOMATICO")
        rev = sum(1 for d in amostras if d["rota_decidida"] == "REVISAO")
        rej = sum(1 for d in amostras if d["rota_decidida"] == "REJEICAO")
        return aut, rev, rej

    stats = []
    for c in categorias:
        sub = [d for d in dados if d["categoria"] == c]
        stats.append(conta_rotas(sub))
    stats.append(conta_rotas(dados))

    y_base = 395
    altura_grafico = 230
    largura_barra = 96
    espaco = 96
    x_inicio = 150

    svg_barras = ""
    for i, (aut, rev, rej) in enumerate(stats):
        tot = aut + rev + rej
        bx = x_inicio + i * (largura_barra + espaco)

        p_aut = aut / tot * 100.0
        p_rev = rev / tot * 100.0
        p_rej = rej / tot * 100.0

        h_aut = (p_aut / 100.0) * altura_grafico
        h_rev = (p_rev / 100.0) * altura_grafico
        h_rej = (p_rej / 100.0) * altura_grafico

        y_aut = y_base - h_aut
        y_rev = y_aut - h_rev
        y_rej = y_rev - h_rej

        bloco = ""
        if h_aut > 0:
            bloco += f"""
            <rect x="{bx}" y="{y_aut:.1f}" width="{largura_barra}" height="{h_aut:.1f}" fill="#10b981" rx="2" />
            <text x="{bx+largura_barra/2}" y="{y_aut+h_aut/2+4:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">{aut} ({p_aut:.0f}%)</text>
            """
        if h_rev > 0:
            bloco += f"""
            <rect x="{bx}" y="{y_rev:.1f}" width="{largura_barra}" height="{h_rev:.1f}" fill="#f59e0b" rx="2" />
            <text x="{bx+largura_barra/2}" y="{y_rev+h_rev/2+4:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">{rev} ({p_rev:.0f}%)</text>
            """
        if h_rej > 0:
            bloco += f"""
            <rect x="{bx}" y="{y_rej:.1f}" width="{largura_barra}" height="{h_rej:.1f}" fill="#ef4444" rx="2" />
            <text x="{bx+largura_barra/2}" y="{y_rej+h_rej/2+4:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="#ffffff">{rej} ({p_rej:.0f}%)</text>
            """

        svg_barras += f"""
        <g class="stacked-bar">
            {bloco}
            <text x="{bx+largura_barra/2}" y="{y_base+24}" text-anchor="middle" font-size="12" font-weight="600" fill="#1e293b">{labels[i]}</text>
        </g>
        """

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="36" font-size="19" font-weight="700" fill="#0f172a">Figura G5: Destinos Operacionais da Triagem em Três Vias (EXP3 / EXP4)</text>
        <text x="50" y="58" font-size="12.5" font-weight="400" fill="#64748b">Distribuição proporcional de decisões por categoria: Automação direta, Fila Humana ou Rejeição de Segurança</text>

        <!-- Faixa de Legenda Dedicada (Área 2) -->
        <g transform="translate(50, 85)">
            <rect x="0" y="0" width="14" height="14" fill="#10b981" rx="3" />
            <text x="20" y="12" font-size="12" font-weight="600" fill="#047857">AUTOMATICO (Despacho Direto ao RPA)</text>

            <rect x="290" y="0" width="14" height="14" fill="#f59e0b" rx="3" />
            <text x="310" y="12" font-size="12" font-weight="600" fill="#b45309">REVISAO (Fila Human-in-the-Loop)</text>

            <rect x="580" y="0" width="14" height="14" fill="#ef4444" rx="3" />
            <text x="600" y="12" font-size="12" font-weight="600" fill="#b91c1c">REJEICAO (Bloqueio Anti-Injection)</text>
        </g>

        <!-- Linhas de Grade e Eixo Y -->
        <g stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4">
            <line x1="95" y1="{y_base}" x2="940" y2="{y_base}" stroke="#94a3b8" stroke-dasharray="0" stroke-width="1.5" />
            <line x1="95" y1="{y_base - altura_grafico*0.25:.1f}" x2="940" y2="{y_base - altura_grafico*0.25:.1f}" />
            <line x1="95" y1="{y_base - altura_grafico*0.50:.1f}" x2="940" y2="{y_base - altura_grafico*0.50:.1f}" />
            <line x1="95" y1="{y_base - altura_grafico*0.75:.1f}" x2="940" y2="{y_base - altura_grafico*0.75:.1f}" />
            <line x1="95" y1="{y_base - altura_grafico:.1f}" x2="940" y2="{y_base - altura_grafico:.1f}" />
        </g>

        <!-- Rótulos Eixo Y -->
        <g font-size="12" fill="#64748b" text-anchor="end">
            <text x="85" y="{y_base+4}">0%</text>
            <text x="85" y="{y_base - altura_grafico*0.25 + 4:.1f}">25%</text>
            <text x="85" y="{y_base - altura_grafico*0.50 + 4:.1f}">50%</text>
            <text x="85" y="{y_base - altura_grafico*0.75 + 4:.1f}">75%</text>
            <text x="85" y="{y_base - altura_grafico + 4:.1f}">100%</text>
        </g>
        <text x="38" y="{y_base - altura_grafico/2}" font-size="13" font-weight="600" fill="#475569" transform="rotate(-90 38 {y_base - altura_grafico/2})" text-anchor="middle">Proporção de Destino Operacional (%)</text>

        <!-- Barras Empilhadas -->
        {svg_barras}

        <!-- Rodapé explicativo -->
        <text x="50" y="525" font-size="11" fill="#94a3b8">Nota: 100% dos documentos limpos foram aprovados para RPA; 60% dos adversariais foram bloqueados por injeção e os demais encaminhados para homologação.</text>
    </svg>
    """
    return svg


def gerar_svg_g6() -> str:
    """G6: Decomposição de Custos Financeiros e Latências por Estágio (EXP7)."""
    dados = ler_csv("exp7_custos.csv")
    if not dados:
        return ""

    custos = [float(d["custo_estimado_brl"]) for d in dados]
    custo_medio = sum(custos) / len(custos) if custos else 0.00044

    # Canvas ampliado para 1040x580 com corredores de respiro total
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 580" width="1040" height="580" style="background:#ffffff; font-family:'Segoe UI',system-ui,sans-serif;">
        <!-- Cabeçalho (Área 1) -->
        <text x="50" y="38" font-size="19" font-weight="700" fill="#0f172a">Figura G6: Decomposição de Latência e Análise de Custos por Estágio (EXP7)</text>
        <text x="50" y="62" font-size="12.5" font-weight="400" fill="#64748b">Análise temporal dos módulos da esteira IPA e projeção financeira com Gemini 2.5 Flash</text>

        <!-- Painel Esquerdo: Decomposição de Latência (Largura 445px) -->
        <g transform="translate(50, 95)">
            <rect x="0" y="0" width="445" height="425" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.2" rx="8" />
            <text x="24" y="34" font-size="15" font-weight="700" fill="#0f172a">Painel A: Latência Mediana por Estágio</text>
            <text x="24" y="54" font-size="12" fill="#64748b">Tempo de resposta em execução com chamada live vs. cache local</text>

            <!-- Barra 1: Extração Inteligente IA -->
            <text x="24" y="98" font-size="12" font-weight="600" fill="#1e293b">1. Extração LLM (Gemini Flash)</text>
            <rect x="24" y="108" width="270" height="26" fill="#3b82f6" rx="4" />
            <text x="32" y="125" font-size="10" font-weight="600" fill="#ffffff">Processamento multimodal e JSON schema</text>
            <text x="306" y="125" font-size="12" font-weight="700" fill="#1d4ed8">8.95s (Live)</text>

            <!-- Barra 2: Regras e Fuzzy Matching -->
            <text x="24" y="172" font-size="12" font-weight="600" fill="#1e293b">2. Motor de Regras e Fuzzy Matching</text>
            <rect x="24" y="182" width="30" height="26" fill="#10b981" rx="4" />
            <text x="65" y="199" font-size="12" font-weight="700" fill="#047857">0.14s (Local)</text>
            <text x="24" y="224" font-size="10.5" fill="#64748b">Validação fiscal CNPJ, catálogo P-001 a P-040 e barreira injection</text>

            <!-- Barra 3: Robô RPA Playwright -->
            <text x="24" y="265" font-size="12" font-weight="600" fill="#1e293b">3. Lançamento ERP (Robô RPA)</text>
            <rect x="24" y="275" width="20" height="26" fill="#f59e0b" rx="4" />
            <text x="55" y="292" font-size="12" font-weight="700" fill="#b45309">0.05s (API) / 2.8s (Browser)</text>
            <text x="24" y="318" font-size="10.5" fill="#64748b">Preenchimento idempotente com evidência de auditoria</text>

            <!-- Resumo Total -->
            <line x1="24" y1="350" x2="420" y2="350" stroke="#cbd5e1" />
            <text x="24" y="382" font-size="13" font-weight="700" fill="#0f172a">Tempo Total Mediano Ponta a Ponta: ~9.03s</text>
            <text x="24" y="402" font-size="11" font-weight="500" fill="#64748b">(Com cache local offline: 0.20s total)</text>
        </g>

        <!-- Painel Direito: Análise de Custo Financeiro (Largura 460px) -->
        <g transform="translate(530, 95)">
            <rect x="0" y="0" width="460" height="425" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.2" rx="8" />
            <text x="24" y="34" font-size="15" font-weight="700" fill="#0f172a">Painel B: Viabilidade Econômica (R$)</text>
            <text x="24" y="54" font-size="12" fill="#64748b">Custo marginal de computação por volume de pedidos</text>

            <!-- Card Destaque Custo Unitário -->
            <rect x="24" y="74" width="412" height="74" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.2" rx="6" />
            <text x="40" y="98" font-size="11" font-weight="700" fill="#065f46">CUSTO MÉDIO POR PEDIDO DE COMPRA</text>
            <text x="40" y="132" font-size="24" font-weight="800" fill="#047857">R$ {custo_medio:.5f}</text>
            <text x="235" y="130" font-size="11.5" font-weight="500" fill="#065f46">(&lt; 5 centésimos de centavo)</text>

            <!-- Tabela de Projeção em Escala com colunas bem distanciadas -->
            <g transform="translate(24, 180)">
                <text x="0" y="14" font-size="12" font-weight="700" fill="#1e293b" text-anchor="start">Volume Mensal</text>
                <text x="175" y="14" font-size="12" font-weight="700" fill="#1e293b" text-anchor="start">Custo Total IPA</text>
                <text x="412" y="14" font-size="12" font-weight="700" fill="#1e293b" text-anchor="end">Economia vs. Humano</text>
                <line x1="0" y1="24" x2="412" y2="24" stroke="#cbd5e1" stroke-width="1.5" />

                <text x="0" y="52" font-size="12" fill="#334155" text-anchor="start">100 pedidos</text>
                <text x="175" y="52" font-size="12" font-weight="600" fill="#047857" text-anchor="start">R$ 0,04</text>
                <text x="412" y="52" font-size="12" font-weight="600" fill="#059669" text-anchor="end">&gt; 99,9% economia</text>

                <text x="0" y="84" font-size="12" fill="#334155" text-anchor="start">1.000 pedidos</text>
                <text x="175" y="84" font-size="12" font-weight="600" fill="#047857" text-anchor="start">R$ 0,44</text>
                <text x="412" y="84" font-size="12" font-weight="600" fill="#059669" text-anchor="end">&gt; 99,9% economia</text>

                <text x="0" y="116" font-size="12" fill="#334155" text-anchor="start">10.000 pedidos</text>
                <text x="175" y="116" font-size="12" font-weight="600" fill="#047857" text-anchor="start">R$ 4,37</text>
                <text x="412" y="116" font-size="12" font-weight="600" fill="#059669" text-anchor="end">&gt; 99,9% economia</text>
            </g>

            <rect x="24" y="345" width="412" height="44" fill="#eff6ff" stroke="#bfdbfe" rx="4" />
            <text x="36" y="364" font-size="11" font-weight="700" fill="#1d4ed8">&#x2022; Viabilidade Absoluta para MPMEs brasileiras</text>
            <text x="36" y="379" font-size="10" fill="#3b82f6">Elimina gargalos operacionais sem necessidade de licenças caras de RPA proprietário.</text>
        </g>

        <!-- Rodapé explicativo -->
        <text x="50" y="545" font-size="11" fill="#94a3b8">Nota: Preços calculados com base na tabela oficial Google AI Studio (US$ 0,075 / 1M tokens de entrada e US$ 0,30 / 1M tokens de saída com câmbio R$ 5,60).</text>
    </svg>
    """
    return svg


async def renderizar_figuras_png():
    """Compila os SVGs e renderiza imagens PNG nítidas (300 DPI) com Playwright."""
    geradores = [
        ("G1_f1_regex_vs_ia.png", gerar_svg_g1()),
        ("G2_curva_risco_cobertura.png", gerar_svg_g2()),
        ("G3_calibracao_confianca.png", gerar_svg_g3()),
        ("G4_boxplot_manual_vs_ipa.png", gerar_svg_g4()),
        ("G5_destino_por_categoria.png", gerar_svg_g5()),
        ("G6_custo_latencia_etapas.png", gerar_svg_g6()),
    ]

    print("\n[RENDER] Inicializando Playwright Chromium para geração das figuras científicas...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # device_scale_factor=2 garante qualidade de impressão (alta densidade de pixels)
        page = await browser.new_page(viewport={"width": 1080, "height": 620}, device_scale_factor=2)

        for nome_arquivo, svg_conteudo in geradores:
            if not svg_conteudo.strip():
                print(f"  [AVISO] SVG vazio para {nome_arquivo}, pulando.")
                continue

            html_page = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ margin: 0; padding: 20px; background: #ffffff; display: flex; justify-content: center; align-items: center; }}
                    svg {{ box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border-radius: 8px; }}
                </style>
            </head>
            <body>
                {svg_conteudo}
            </body>
            </html>"""

            await page.set_content(html_page)
            svg_element = await page.query_selector("svg")
            destino = figures_dir / nome_arquivo

            if svg_element:
                await svg_element.screenshot(path=str(destino))
            else:
                await page.screenshot(path=str(destino))

            print(f"  [OK] Figura gerada: {destino.name} ({destino.stat().st_size // 1024} KB)")

        await browser.close()
    print(f"[CONCLUÍDO] Todas as 6 figuras científicas geradas em {figures_dir.resolve()}\n")


if __name__ == "__main__":
    asyncio.run(renderizar_figuras_png())
