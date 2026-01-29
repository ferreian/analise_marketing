# pages/03_Confiabilidade_Hibridos.py
# ============================================================
# Sistema de Produção Agrícola - Confiabilidade dos Híbridos
# Análise: "Esse híbrido entrega o que promete?"
# Versão 1.2 - Com Modais Corrigidos
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path
from scipy import stats

# Adicionar diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from config import PALETA_CORES
from utils import criar_breadcrumb, criar_aggrid, logger

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Confiabilidade dos Híbridos",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO
# ============================================================
st.markdown(f"""
    <style>
    .main {{
        background-color: {PALETA_CORES['bg_light']};
    }}
    
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {PALETA_CORES['secondary']};
        margin-bottom: 1rem;
    }}
    
    .score-card {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,104,56,0.3);
    }}
    
    .score-value {{
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
    }}
    
    .score-label {{
        font-size: 1rem;
        opacity: 0.9;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background-color: white;
        padding: 0.75rem;
        border-radius: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: {PALETA_CORES['bg_light']};
        border-radius: 6px;
        color: {PALETA_CORES['primary']};
        font-weight: 500;
        padding: 0.75rem 1.5rem !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# ============================================================
# MODAIS DE EXPLICAÇÃO
# ============================================================

@st.dialog("📊 Probabilidade de Atingir a Média (Estatística Z)", width="large")
def mostrar_explicacao_probabilidade_z():
    """Modal com explicação do cálculo da probabilidade Z"""
    
    st.markdown("""
    ### O que é?
    
    A **Probabilidade Z** mede a chance de uma observação do híbrido estar dentro de uma faixa de **±10% da sua média**.
    
    ---
    
    ### Como é calculada?
    
    1. Calcula a **média (μ)** e o **desvio padrão (σ)** do híbrido
    2. Define os limites: **90% a 110% da média**
    3. Usa a **distribuição normal** para calcular a probabilidade
    
    **Fórmula:**
    
    `Z = (X - μ) / σ`
    
    `Probabilidade = P(Z_inferior < Z < Z_superior)`
    
    ---
    
    ### Exemplo
    
    | Dado | Valor |
    |------|-------|
    | Média | 9.000 kg/ha |
    | Desvio Padrão | 900 kg/ha |
    | Limite Inferior | 8.100 (90%) |
    | Limite Superior | 9.900 (110%) |
    | **Probabilidade** | **68.3%** |
    
    ---
    
    ### Interpretação
    
    | Probabilidade | Significado |
    |---------------|-------------|
    | ≥ 75% | 🟢 Híbrido muito consistente |
    | 50-74% | 🟡 Consistência moderada |
    | 25-49% | 🟠 Alta variabilidade |
    | < 25% | 🔴 Muito inconsistente |
    """)
    
    if st.button("✅ Entendi!", key="btn_fechar_prob_z", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("✅ Taxa de Sucesso", width="large")
def mostrar_explicacao_taxa_sucesso():
    """Modal com explicação da taxa de sucesso"""
    
    st.markdown("""
    ### O que é?
    
    A **Taxa de Sucesso** mede a porcentagem de vezes que o híbrido produziu **acima de um limiar mínimo aceitável**.
    
    ---
    
    ### Como é calculada?
    
    **Fórmula:**
    
    `Limiar = 80% da Média Geral das Macros Selecionadas`
    
    `Taxa de Sucesso = (Observações ≥ Limiar) / Total de Observações × 100`
    
    ---
    
    ### Exemplo
    
    | Dado | Valor |
    |------|-------|
    | Média Geral | 8.500 kg/ha |
    | Limiar (80%) | 6.800 kg/ha |
    | Observações do Híbrido | 10 |
    | Observações ≥ 6.800 | 9 |
    | **Taxa de Sucesso** | **90%** |
    
    ---
    
    ### Interpretação
    
    | Taxa | Significado |
    |------|-------------|
    | ≥ 90% | 🟢 Excelente - Raramente decepciona |
    | 75-89% | 🟡 Bom - Ocasionalmente abaixo |
    | 50-74% | 🟠 Regular - Frequentemente abaixo |
    | < 50% | 🔴 Ruim - Mais vezes abaixo que acima |
    """)
    
    if st.button("✅ Entendi!", key="btn_fechar_taxa", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("⚠️ Risco de Frustração", width="large")
def mostrar_explicacao_risco():
    """Modal com explicação do risco de frustração"""
    
    st.markdown("""
    ### O que é?
    
    O **Risco de Frustração** mede a porcentagem de vezes que o híbrido produziu **muito abaixo da sua própria média** (decepcionou).
    
    ---
    
    ### Como é calculado?
    
    **Fórmula:**
    
    `Limiar de Frustração = 80% da Média do Híbrido`
    
    `Risco = (Observações < Limiar) / Total de Observações × 100`
    
    ---
    
    ### Exemplo
    
    | Dado | Valor |
    |------|-------|
    | Média do Híbrido | 9.000 kg/ha |
    | Limiar de Frustração (80%) | 7.200 kg/ha |
    | Observações do Híbrido | 10 |
    | Observações < 7.200 | 2 |
    | **Risco de Frustração** | **20%** |
    
    ---
    
    ### Interpretação
    
    | Risco | Significado |
    |-------|-------------|
    | < 10% | 🟢 Baixo risco - Muito confiável |
    | 10-20% | 🟡 Risco moderado - Aceitável |
    | 20-35% | 🟠 Risco alto - Atenção |
    | > 35% | 🔴 Risco muito alto - Evitar |
    """)
    
    if st.button("✅ Entendi!", key="btn_fechar_risco", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("🏆 Score de Confiabilidade", width="large")
def mostrar_explicacao_score():
    """Modal com explicação do score de confiabilidade"""
    
    st.markdown("""
    ### O que é?
    
    O **Score de Confiabilidade** é uma nota de **0 a 100** que combina todas as métricas para responder: **"Esse híbrido entrega o que promete?"**
    
    ---
    
    ### Como é calculado?
    
    **Fórmula:**
    
    `Score = (Prob. Z × 0.35) + (Taxa Sucesso × 0.35) + ((100 - Risco) × 0.20) + (Fator Obs × 0.10)`
    
    | Componente | Peso | O que mede |
    |------------|------|------------|
    | Probabilidade Z | 35% | Consistência estatística |
    | Taxa de Sucesso | 35% | Frequência acima do mínimo |
    | 100 - Risco | 20% | Inverso do risco de frustração |
    | Fator Observações | 10% | Confiança nos dados (mais dados = mais confiável) |
    
    ---
    
    ### Fator de Observações
    
    | Observações | Fator |
    |-------------|-------|
    | ≥ 20 | 100% |
    | 10-19 | 80% |
    | 5-9 | 60% |
    | < 5 | 40% |
    
    ---
    
    ### Classificação Final
    
    | Score | Classificação | Recomendação |
    |-------|---------------|--------------|
    | ≥ 80 | 🏆 **Excelente** | Altamente recomendado |
    | 65-79 | 🥈 **Bom** | Recomendado |
    | 50-64 | 🥉 **Regular** | Usar com cautela |
    | < 50 | ⚠️ **Baixo** | Não recomendado |
    """)
    
    if st.button("✅ Entendi!", key="btn_fechar_score", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("🏆 Ranking de Confiabilidade", width="large")
def mostrar_explicacao_ranking():
    """Modal com explicação do ranking de confiabilidade"""
    
    st.markdown("""
    ### O que é o Ranking?
    
    O **Ranking de Confiabilidade** ordena os híbridos do **mais confiável** para o **menos confiável**, baseado no **Score de Confiabilidade**.
    
    ---
    
    ### Como interpretar o gráfico?
    
    | Zona | Score | Cor | Significado |
    |------|-------|-----|-------------|
    | 🟢 Verde | ≥ 80 | Verde escuro | **Excelente** - Altamente recomendado |
    | 🟡 Amarelo | 65-79 | Amarelo/Verde claro | **Bom** - Recomendado |
    | 🟠 Laranja | 50-64 | Laranja | **Regular** - Usar com cautela |
    | 🔴 Vermelho | < 50 | Vermelho | **Baixo** - Não recomendado |
    
    ---
    
    ### Linhas de Referência no Gráfico
    
    | Linha | Valor | Significado |
    |-------|-------|-------------|
    | 🟢 Verde tracejada | 80 | Limite para "Excelente" |
    | 🟠 Laranja tracejada | 65 | Limite para "Bom" |
    | 🔴 Vermelha tracejada | 50 | Limite para "Regular" |
    
    ---
    
    ### Composição do Score
    
    O Score é calculado combinando 4 métricas:
    
    | Componente | Peso | O que mede |
    |------------|------|------------|
    | Probabilidade Z | 35% | Consistência estatística (±10% da média) |
    | Taxa de Sucesso | 35% | % de vezes acima do mínimo aceitável |
    | 100 - Risco | 20% | Inverso do risco de frustração |
    | Fator Observações | 10% | Confiança baseada na quantidade de dados |
    
    ---
    
    ### Como usar o Ranking?
    
    1. **Identifique os híbridos no topo** → São os mais confiáveis
    2. **Observe a cor da barra** → Verde = melhor, Vermelho = pior
    3. **Compare com as linhas de referência** → Verifique em qual zona cada híbrido está
    4. **Priorize híbridos acima de 65** → São os recomendados para plantio
    
    ---
    
    ### Recomendações por Classificação
    
    | Classificação | Recomendação |
    |---------------|--------------|
    | 🏆 **Excelente** (≥80) | Primeira escolha para plantio. Alta confiança. |
    | 🥈 **Bom** (65-79) | Boa opção. Monitorar desempenho. |
    | 🥉 **Regular** (50-64) | Usar apenas se não houver alternativas melhores. |
    | ⚠️ **Baixo** (<50) | Evitar. Alto risco de frustração. |
    
    ---
    
    ### Dica
    
    Para análise detalhada de um híbrido específico, use a seção **"🔍 Detalhamento por Híbrido"** abaixo do ranking.
    """)
    
    if st.button("✅ Entendi!", key="btn_fechar_ranking", type="primary", use_container_width=True):
        st.rerun()


# ============================================================
# CABEÇALHO
# ============================================================
st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,104,56,0.2);'>
        <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>🎯 Confiabilidade dos Híbridos</h1>
        <p style='color: white; margin-top: 0.5rem; opacity: 0.95;'>"Esse híbrido entrega o que promete?"</p>
    </div>
""", unsafe_allow_html=True)

criar_breadcrumb("Confiabilidade dos Híbridos")

# ============================================================
# CARREGAR DADOS
# ============================================================
if "df_final" not in st.session_state:
    st.error("❌ Dados não encontrados!")
    st.warning("⚠️ Execute a página principal primeiro para carregar os dados.")
    st.stop()

df = st.session_state["df_final"]
df_filtrado = st.session_state.get("df_filtrado", df)

logger.info(f"🎯 Página de Confiabilidade carregada: {len(df)} registros")

# ============================================================
# FILTROS
# ============================================================
st.markdown("### 🔍 Filtros")

col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

with col_filtro1:
    st.markdown("##### 📏 Métrica de Produção")
    
    opcoes_producao = {
        'prod_kg_ha_13_5': 'Produção (kg/ha)',
        'prod_sc_ha_13_5': 'Produção (sc/ha)'
    }
    
    colunas_disponiveis = [col for col in opcoes_producao.keys() if col in df_filtrado.columns]
    
    if colunas_disponiveis:
        coluna_producao = st.radio(
            "Escolha a unidade de medida",
            options=colunas_disponiveis,
            format_func=lambda x: opcoes_producao[x],
            key="coluna_producao_conf",
            horizontal=True
        )
    else:
        st.error("❌ Colunas de produção não encontradas.")
        st.stop()

with col_filtro2:
    st.markdown("##### 🧭 Filtrar por Macro MKT")
    
    if "macro_mkt" in df_filtrado.columns:
        macros_disponiveis = sorted(df_filtrado["macro_mkt"].dropna().unique().tolist())
        
        todas_macros = st.checkbox(
            "Selecionar Todas as Macros",
            value=True,
            key="todas_macros_conf"
        )
        
        if todas_macros:
            macros_selecionadas = macros_disponiveis
        else:
            macros_selecionadas = st.multiselect(
                "Escolha as macros",
                options=macros_disponiveis,
                default=macros_disponiveis[:3] if len(macros_disponiveis) >= 3 else macros_disponiveis,
                key="macros_dropdown_conf"
            )
        
        if macros_selecionadas:
            df_analise = df_filtrado[df_filtrado["macro_mkt"].isin(macros_selecionadas)].copy()
        else:
            df_analise = df_filtrado.copy()
            macros_selecionadas = macros_disponiveis
    else:
        df_analise = df_filtrado.copy()
        macros_selecionadas = []

with col_filtro3:
    st.markdown("##### 🧬 Filtrar por Híbridos")
    
    if "hibrido" in df_analise.columns:
        hibridos_disponiveis = sorted(df_analise["hibrido"].dropna().unique().tolist())
        
        todos_hibridos = st.checkbox(
            "Selecionar Todos os Híbridos",
            value=False,
            key="todos_hibridos_conf"
        )
        
        if todos_hibridos:
            hibridos_selecionados = hibridos_disponiveis
        else:
            default_hibridos = hibridos_disponiveis[:10] if len(hibridos_disponiveis) >= 10 else hibridos_disponiveis
            hibridos_selecionados = st.multiselect(
                "Escolha os híbridos (máx. 15 para melhor visualização)",
                options=hibridos_disponiveis,
                default=default_hibridos,
                key="hibridos_dropdown_conf"
            )
        
        if hibridos_selecionados:
            df_analise = df_analise[df_analise["hibrido"].isin(hibridos_selecionados)].copy()
        else:
            st.warning("⚠️ Selecione pelo menos um híbrido.")
            st.stop()
    else:
        st.error("❌ Coluna 'hibrido' não encontrada.")
        st.stop()

st.markdown("---")

# ============================================================
# CÁLCULO DAS MÉTRICAS DE CONFIABILIDADE
# ============================================================

if len(df_analise) > 0 and len(hibridos_selecionados) > 0:
    
    # Média geral das macros selecionadas
    media_geral = df_analise[coluna_producao].mean()
    limiar_sucesso = media_geral * 0.80
    
    # Calcular métricas para cada híbrido
    resultados = []
    
    for hibrido in hibridos_selecionados:
        df_h = df_analise[df_analise['hibrido'] == hibrido][coluna_producao].dropna()
        
        if len(df_h) > 1:
            n_obs = len(df_h)
            media_hibrido = df_h.mean()
            std_hibrido = df_h.std()
            cv_hibrido = (std_hibrido / media_hibrido * 100) if media_hibrido != 0 else 0
            
            # 1. Probabilidade Z (±10% da média)
            if std_hibrido > 0:
                limite_inf = media_hibrido * 0.90
                limite_sup = media_hibrido * 1.10
                z_inf = (limite_inf - media_hibrido) / std_hibrido
                z_sup = (limite_sup - media_hibrido) / std_hibrido
                prob_z = (stats.norm.cdf(z_sup) - stats.norm.cdf(z_inf)) * 100
            else:
                prob_z = 100.0
            
            # 2. Taxa de Sucesso (>= 80% da média geral)
            obs_sucesso = (df_h >= limiar_sucesso).sum()
            taxa_sucesso = (obs_sucesso / n_obs) * 100
            
            # 3. Risco de Frustração (< 80% da média do híbrido)
            limiar_frustracao = media_hibrido * 0.80
            obs_frustracao = (df_h < limiar_frustracao).sum()
            risco_frustracao = (obs_frustracao / n_obs) * 100
            
            # 4. Fator de Observações
            if n_obs >= 20:
                fator_obs = 100
            elif n_obs >= 10:
                fator_obs = 80
            elif n_obs >= 5:
                fator_obs = 60
            else:
                fator_obs = 40
            
            # 5. Score de Confiabilidade (0-100)
            score = (
                (prob_z * 0.35) +
                (taxa_sucesso * 0.35) +
                ((100 - risco_frustracao) * 0.20) +
                (fator_obs * 0.10)
            )
            
            # Classificação do Score
            if score >= 80:
                classificacao = "🏆 Excelente"
            elif score >= 65:
                classificacao = "🥈 Bom"
            elif score >= 50:
                classificacao = "🥉 Regular"
            else:
                classificacao = "⚠️ Baixo"
            
            resultados.append({
                'Híbrido': hibrido,
                'Observações': n_obs,
                'Média': round(media_hibrido, 1),
                'CV (%)': round(cv_hibrido, 1),
                'Prob. Z (%)': round(prob_z, 1),
                'Taxa Sucesso (%)': round(taxa_sucesso, 1),
                'Risco (%)': round(risco_frustracao, 1),
                'Score': round(score, 1),
                'Classificação': classificacao
            })
    
    # Criar DataFrame
    df_conf = pd.DataFrame(resultados)
    df_conf = df_conf.sort_values('Score', ascending=False).reset_index(drop=True)
    df_conf.index = df_conf.index + 1
    df_conf.index.name = 'Rank'
    df_conf = df_conf.reset_index()
    
    # ============================================================
    # MÉTRICAS RESUMO
    # ============================================================
    
    st.markdown("### 📊 Resumo Geral")
    
    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
    
    with col_r1:
        st.metric("Híbridos Analisados", len(df_conf))
    with col_r2:
        excelentes = len(df_conf[df_conf['Score'] >= 80])
        st.metric("🏆 Excelentes", excelentes)
    with col_r3:
        bons = len(df_conf[(df_conf['Score'] >= 65) & (df_conf['Score'] < 80)])
        st.metric("🥈 Bons", bons)
    with col_r4:
        regulares = len(df_conf[(df_conf['Score'] >= 50) & (df_conf['Score'] < 65)])
        st.metric("🥉 Regulares", regulares)
    with col_r5:
        baixos = len(df_conf[df_conf['Score'] < 50])
        st.metric("⚠️ Baixos", baixos)
    
    st.markdown("---")
    
    # ============================================================
    # MÉTRICAS COM BOTÕES DE INFO
    # ============================================================
    
    st.markdown("### 📈 Métricas de Confiabilidade")
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    
    with col_t1:
        col_titulo, col_btn = st.columns([5, 1])
        with col_titulo:
            st.markdown("##### 📊 Probabilidade Z")
        with col_btn:
            if st.button("ℹ️", key="btn_info_prob", help="Como é calculada a Probabilidade Z"):
                mostrar_explicacao_probabilidade_z()
    
    with col_t2:
        col_titulo, col_btn = st.columns([5, 1])
        with col_titulo:
            st.markdown("##### ✅ Taxa de Sucesso")
        with col_btn:
            if st.button("ℹ️", key="btn_info_taxa", help="Como é calculada a Taxa de Sucesso"):
                mostrar_explicacao_taxa_sucesso()
    
    with col_t3:
        col_titulo, col_btn = st.columns([5, 1])
        with col_titulo:
            st.markdown("##### ⚠️ Risco de Frustração")
        with col_btn:
            if st.button("ℹ️", key="btn_info_risco", help="Como é calculado o Risco"):
                mostrar_explicacao_risco()
    
    with col_t4:
        col_titulo, col_btn = st.columns([5, 1])
        with col_titulo:
            st.markdown("##### 🏆 Score Final")
        with col_btn:
            if st.button("ℹ️", key="btn_info_score", help="Como é calculado o Score"):
                mostrar_explicacao_score()
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        media_prob = df_conf['Prob. Z (%)'].mean()
        st.metric("Média", f"{media_prob:.1f}%")
    
    with col_m2:
        media_taxa = df_conf['Taxa Sucesso (%)'].mean()
        st.metric("Média", f"{media_taxa:.1f}%")
    
    with col_m3:
        media_risco = df_conf['Risco (%)'].mean()
        st.metric("Média", f"{media_risco:.1f}%")
    
    with col_m4:
        media_score = df_conf['Score'].mean()
        st.metric("Média", f"{media_score:.1f}")
    
    st.markdown("---")
    
    # ============================================================
    # GRÁFICO DE RADAR (TOP 5)
    # ============================================================
    
    st.markdown("### 🕸️ Comparativo dos Top 5 Híbridos")
    
    top5 = df_conf.head(5)
    
    if len(top5) > 0:
        categorias = ['Prob. Z', 'Taxa Sucesso', '100 - Risco', 'Score']
        
        fig_radar = go.Figure()
        
        cores_radar = px.colors.qualitative.Set2
        
        for idx, row in top5.iterrows():
            valores = [
                row['Prob. Z (%)'],
                row['Taxa Sucesso (%)'],
                100 - row['Risco (%)'],
                row['Score']
            ]
            valores.append(valores[0])
            
            fig_radar.add_trace(go.Scatterpolar(
                r=valores,
                theta=categorias + [categorias[0]],
                fill='toself',
                name=row['Híbrido'],
                line_color=cores_radar[idx % len(cores_radar)],
                opacity=0.7
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Comparativo de Métricas - Top 5 Híbridos",
            height=500
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================
    # GRÁFICO DE BARRAS - RANKING
    # ============================================================
    
    col_titulo_rank, col_info_rank = st.columns([11, 1])
    
    with col_titulo_rank:
        st.markdown("### 🏆 Ranking de Confiabilidade")
    
    with col_info_rank:
        if st.button("ℹ️", key="btn_info_ranking", help="Entenda o Ranking de Confiabilidade"):
            mostrar_explicacao_ranking()
    
    fig_score = px.bar(
        df_conf.sort_values('Score', ascending=True),
        x='Score',
        y='Híbrido',
        orientation='h',
        color='Score',
        color_continuous_scale='RdYlGn',
        title="Score de Confiabilidade por Híbrido",
        text='Score'
    )
    
    fig_score.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    
    fig_score.add_vline(x=80, line_dash="dash", line_color="green", line_width=2,
                        annotation_text="Excelente (80)", annotation_position="top")
    fig_score.add_vline(x=65, line_dash="dash", line_color="orange", line_width=1,
                        annotation_text="Bom (65)", annotation_position="bottom")
    fig_score.add_vline(x=50, line_dash="dash", line_color="red", line_width=1,
                        annotation_text="Regular (50)", annotation_position="top")
    
    fig_score.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(400, len(df_conf) * 35),
        xaxis=dict(range=[0, 105]),
        showlegend=False
    )
    
    st.plotly_chart(fig_score, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================================
    # TABELA COMPLETA
    # ============================================================
    
    st.markdown("### 📋 Tabela Completa de Confiabilidade")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"📊 **Limiar de Sucesso:** {limiar_sucesso:,.1f} {opcoes_producao[coluna_producao]} (80% da média geral: {media_geral:,.1f})")
    with col_info2:
        st.info(f"⚠️ **Limiar de Frustração:** 80% da média de cada híbrido")
    
    criar_aggrid(df_conf, altura=400, colunas_texto=['Híbrido', 'Classificação'])
    
    st.download_button(
        label="📥 Download Confiabilidade (CSV)",
        data=df_conf.to_csv(index=False).encode('utf-8'),
        file_name=f"confiabilidade_hibridos_{coluna_producao}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # ============================================================
    # DETALHAMENTO POR HÍBRIDO
    # ============================================================
    
    st.markdown("### 🔍 Detalhamento por Híbrido")
    
    hibrido_detalhe = st.selectbox(
        "Selecione um híbrido para ver detalhes:",
        options=df_conf['Híbrido'].tolist(),
        key="hibrido_detalhe"
    )
    
    if hibrido_detalhe:
        dados_hibrido = df_conf[df_conf['Híbrido'] == hibrido_detalhe].iloc[0]
        df_h_detalhe = df_analise[df_analise['hibrido'] == hibrido_detalhe][coluna_producao].dropna()
        
        col_d1, col_d2 = st.columns([1, 2])
        
        with col_d1:
            st.markdown(f"""
                <div class='score-card'>
                    <p class='score-label'>Score de Confiabilidade</p>
                    <p class='score-value'>{dados_hibrido['Score']:.0f}</p>
                    <p class='score-label'>{dados_hibrido['Classificação']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.metric("Observações", dados_hibrido['Observações'])
            st.metric("Média", f"{dados_hibrido['Média']:,.1f}")
            st.metric("CV", f"{dados_hibrido['CV (%)']:.1f}%")
            st.metric("Probabilidade Z", f"{dados_hibrido['Prob. Z (%)']:.1f}%")
            st.metric("Taxa de Sucesso", f"{dados_hibrido['Taxa Sucesso (%)']:.1f}%")
            st.metric("Risco de Frustração", f"{dados_hibrido['Risco (%)']:.1f}%")
        
        with col_d2:
            fig_hist = go.Figure()
            
            fig_hist.add_trace(go.Histogram(
                x=df_h_detalhe,
                nbinsx=15,
                name='Distribuição',
                marker_color=PALETA_CORES['primary'],
                opacity=0.7
            ))
            
            media_h = dados_hibrido['Média']
            
            fig_hist.add_vline(x=media_h, line_dash="solid", line_color="blue", line_width=2,
                              annotation_text=f"Média: {media_h:,.0f}", annotation_position="top")
            fig_hist.add_vline(x=media_h * 0.90, line_dash="dash", line_color="orange", line_width=1,
                              annotation_text="90%", annotation_position="bottom left")
            fig_hist.add_vline(x=media_h * 1.10, line_dash="dash", line_color="orange", line_width=1,
                              annotation_text="110%", annotation_position="bottom right")
            fig_hist.add_vline(x=media_h * 0.80, line_dash="dot", line_color="red", line_width=1,
                              annotation_text="Frustração (80%)", annotation_position="top left")
            
            fig_hist.update_layout(
                title=f"Distribuição de Produção - {hibrido_detalhe}",
                xaxis_title=opcoes_producao[coluna_producao],
                yaxis_title="Frequência",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=400
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            st.markdown("##### 💡 Interpretação")
            
            if dados_hibrido['Score'] >= 80:
                st.success(f"""
                **{hibrido_detalhe}** é um híbrido **excelente** com alta confiabilidade.
                - ✅ Alta probabilidade de atingir sua média
                - ✅ Baixo risco de frustração
                - ✅ Recomendado para plantio
                """)
            elif dados_hibrido['Score'] >= 65:
                st.info(f"""
                **{hibrido_detalhe}** é um híbrido **bom** com boa confiabilidade.
                - ✅ Boa probabilidade de atingir sua média
                - ⚠️ Risco moderado de frustração
                - 👍 Recomendado com atenção
                """)
            elif dados_hibrido['Score'] >= 50:
                st.warning(f"""
                **{hibrido_detalhe}** é um híbrido **regular** com confiabilidade moderada.
                - ⚠️ Variabilidade considerável
                - ⚠️ Risco de frustração presente
                - 🤔 Usar com cautela
                """)
            else:
                st.error(f"""
                **{hibrido_detalhe}** tem **baixa confiabilidade**.
                - ❌ Alta variabilidade
                - ❌ Alto risco de frustração
                - ❌ Não recomendado
                """)

else:
    st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")

st.markdown(f"""
    <div style='text-align: center; color: {PALETA_CORES['primary']}; padding: 2rem 0;'>
        <p style='font-weight: 600;'>Confiabilidade dos Híbridos | Sistema de Produção Agrícola</p>
        <p style='font-size: 0.875rem; color: {PALETA_CORES['secondary']};'>
            Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}
        </p>
    </div>
""", unsafe_allow_html=True)