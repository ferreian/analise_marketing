# pages/02_Analise_Dados.py
# ============================================================
# Sistema de Produção Agrícola - Análise de Dados
# Análise exploratória e visualizações avançadas
# Versão 1.9 - Com Modal Corrigido
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
    page_title="Análise de Dados",
    page_icon="📈",
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
    
    .section-header {{
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid {PALETA_CORES['accent']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    .section-title {{
        color: {PALETA_CORES['primary']};
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
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
# MODAL DE EXPLICAÇÃO DA PROBABILIDADE
# ============================================================
@st.dialog("📊 Como a Probabilidade é Calculada", width="large")
def mostrar_explicacao_probabilidade():
    """Modal com explicação detalhada do cálculo da probabilidade usando Z-score"""
    
    st.markdown("""
    ### Metodologia de Cálculo (Estatística Z)
    
    A **probabilidade** representa a chance de um híbrido atingir sua própria média de produção, considerando a variabilidade (desvio padrão) dos dados.
    
    ---
    
    ### Conceito
    
    Utilizamos a **distribuição normal** e o **Z-score** para calcular a probabilidade de uma observação estar dentro de uma faixa de **±10% da média** do híbrido.
    
    - Híbridos **consistentes** (baixo desvio padrão) → **Alta probabilidade**
    - Híbridos **variáveis** (alto desvio padrão) → **Baixa probabilidade**
    
    ---
    
    ### Fórmula do Z-score
    
    `Z = (X - μ) / σ`
    
    **Onde:**
    - **X** = Valor de referência (limite inferior ou superior)
    - **μ** = Média do híbrido
    - **σ** = Desvio padrão do híbrido
    
    ---
    
    ### Etapas do Cálculo
    
    1. Calcular a **média (μ)** e o **desvio padrão (σ)** do híbrido
    2. Definir a faixa de tolerância: **±10% da média**
       - Limite inferior = μ × 0.90
       - Limite superior = μ × 1.10
    3. Calcular os **Z-scores** para os limites
    4. Usar a **distribuição normal acumulada** para obter a probabilidade
    
    ---
    
    ### Exemplo Prático
    
    | Dado | Valor |
    |------|-------|
    | Híbrido | HBR-001 |
    | Média (μ) | **9.000 kg/ha** |
    | Desvio Padrão (σ) | **900 kg/ha** |
    | CV (%) | 10% |
    | Limite Inferior | 8.100 kg/ha (90%) |
    | Limite Superior | 9.900 kg/ha (110%) |
    | Z inferior | (8.100 - 9.000) / 900 = **-1.0** |
    | Z superior | (9.900 - 9.000) / 900 = **+1.0** |
    | **Probabilidade** | P(-1 < Z < 1) = **68.3%** |
    
    ---
    
    ### Interpretação
    
    A probabilidade de **68.3%** significa que, baseado nos dados históricos, há 68.3% de chance de uma nova observação deste híbrido ficar entre 8.100 e 9.900 kg/ha (±10% da média).
    
    ---
    
    ### Classificação
    
    | Probabilidade | Classificação | Interpretação |
    |---------------|---------------|---------------|
    | ≥ 75% | 🟢 **Alta** | Híbrido muito consistente, baixa variabilidade |
    | 50% - 74% | 🟡 **Média** | Híbrido com variabilidade moderada |
    | 25% - 49% | 🟠 **Baixa** | Híbrido com alta variabilidade |
    | < 25% | 🔴 **Muito Baixa** | Híbrido muito inconsistente |
    
    ---
    
    ### Relação com o Coeficiente de Variação (CV)
    
    | CV (%) | Probabilidade Aproximada | Consistência |
    |--------|--------------------------|--------------|
    | 5% | ~95% | Muito Alta |
    | 10% | ~68% | Alta |
    | 15% | ~50% | Moderada |
    | 20% | ~38% | Baixa |
    | 30% | ~26% | Muito Baixa |
    
    ---
    
    ### Observações Importantes
    
    - A faixa de **±10%** é um padrão comum na agricultura para avaliar consistência
    - Quanto **menor o CV**, **maior a probabilidade** de atingir a média
    - Híbridos com poucas observações (< 5) podem ter estimativas menos confiáveis
    - A análise assume que os dados seguem uma **distribuição normal**
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Entendi!", key="btn_fechar_prob", type="primary", use_container_width=True):
            st.rerun()

# ============================================================
# CABEÇALHO
# ============================================================
st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,104,56,0.2);'>
        <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>📈 Análise de Dados</h1>
        <p style='color: white; margin-top: 0.5rem; opacity: 0.95;'>Análise exploratória e visualizações avançadas dos dados de produção</p>
    </div>
""", unsafe_allow_html=True)

criar_breadcrumb("Análise de Dados")

# ============================================================
# CARREGAR DADOS
# ============================================================
if "df_final" not in st.session_state:
    st.error("❌ Dados não encontrados!")
    st.warning("⚠️ Execute a página principal primeiro para carregar os dados.")
    st.stop()

df = st.session_state["df_final"]
df_raw = st.session_state.get("df_raw", df)
df_filtrado = st.session_state.get("df_filtrado", df)

logger.info(f"📈 Página de Análise carregada: {len(df)} registros")

# ============================================================
# VISUALIZAÇÃO DOS DADOS (EXPANDER NO INÍCIO)
# ============================================================
with st.expander("📋 Ver Dados Utilizados nas Análises", expanded=False):
    
    st.markdown("##### 🗃️ Dataset Completo")
    st.caption(f"Exibindo {len(df_filtrado):,} registros e {len(df_filtrado.columns)} colunas")
    
    tab_dados1, tab_dados2, tab_dados3 = st.tabs([
        "📊 Dados Completos",
        "🔢 Apenas Numéricas",
        "ℹ️ Informações"
    ])
    
    with tab_dados1:
        criar_aggrid(df_filtrado, altura=400, colunas_texto=['hibrido', 'safra'])
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Download Completo (CSV)",
                data=df_filtrado.to_csv(index=False).encode('utf-8'),
                file_name="dados_completos.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with tab_dados2:
        colunas_num = df_filtrado.select_dtypes(include=['number']).columns.tolist()
        if 'safra' in colunas_num:
            colunas_num.remove('safra')
        
        colunas_exibir = []
        if 'hibrido' in df_filtrado.columns:
            colunas_exibir.append('hibrido')
        colunas_exibir.extend(colunas_num)
        
        df_num = df_filtrado[colunas_exibir].copy()
        
        st.caption(f"📋 {len(colunas_num)} colunas numéricas disponíveis")
        criar_aggrid(df_num, altura=400, colunas_texto=['hibrido'])
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Download Numéricas (CSV)",
                data=df_num.to_csv(index=False).encode('utf-8'),
                file_name="dados_numericos.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with tab_dados3:
        st.markdown("##### 📊 Resumo do Dataset")
        
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        
        with col_i1:
            st.metric("Total de Registros", f"{len(df_filtrado):,}")
        with col_i2:
            st.metric("Total de Colunas", len(df_filtrado.columns))
        with col_i3:
            valores_nulos_total = df_filtrado.isnull().sum().sum()
            st.metric("Valores Nulos", f"{valores_nulos_total:,}")
        with col_i4:
            completude_total = ((df_filtrado.size - valores_nulos_total) / df_filtrado.size * 100)
            st.metric("Completude", f"{completude_total:.1f}%")
        
        st.markdown("---")
        
        st.markdown("##### 📋 Estrutura das Colunas")
        
        info_colunas = []
        for col in df_filtrado.columns:
            info_colunas.append({
                'Coluna': col,
                'Tipo': str(df_filtrado[col].dtype),
                'Não Nulos': df_filtrado[col].notna().sum(),
                'Nulos': df_filtrado[col].isna().sum(),
                '% Preenchido': round(df_filtrado[col].notna().sum() / len(df_filtrado) * 100, 1),
                'Únicos': df_filtrado[col].nunique()
            })
        
        info_df = pd.DataFrame(info_colunas)
        
        criar_aggrid(info_df, altura=400, colunas_texto=['Coluna', 'Tipo'])
        
        st.markdown("---")
        
        st.markdown("##### 🔢 Colunas Numéricas Disponíveis")
        
        colunas_numericas_info = df_filtrado.select_dtypes(include=['number']).columns.tolist()
        if 'safra' in colunas_numericas_info:
            colunas_numericas_info.remove('safra')
        
        if colunas_numericas_info:
            num_cols = 4
            cols = st.columns(num_cols)
            for i, col_name in enumerate(colunas_numericas_info):
                with cols[i % num_cols]:
                    st.markdown(f"✅ `{col_name}`")
        else:
            st.warning("⚠️ Nenhuma coluna numérica encontrada.")
        
        st.markdown("---")
        
        st.markdown("##### 📝 Colunas Categóricas")
        
        colunas_categoricas = df_filtrado.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if colunas_categoricas:
            num_cols = 4
            cols = st.columns(num_cols)
            for i, col_name in enumerate(colunas_categoricas):
                with cols[i % num_cols]:
                    st.markdown(f"📌 `{col_name}`")
        else:
            st.info("ℹ️ Nenhuma coluna categórica encontrada.")

st.markdown("---")

# ============================================================
# CONTEÚDO PRINCIPAL - ANÁLISE DE PRODUÇÃO
# ============================================================

st.markdown("### 📊 Análise de Produção por Híbrido")

# ----- FILTROS -----
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
            key="coluna_producao_strip",
            horizontal=True
        )
    else:
        st.error("❌ Colunas de produção não encontradas no dataset.")
        st.stop()

with col_filtro2:
    st.markdown("##### 🧭 Filtrar por Macro MKT")
    
    if "macro_mkt" in df_filtrado.columns:
        macros_disponiveis = sorted(df_filtrado["macro_mkt"].dropna().unique().tolist())
        
        todas_macros = st.checkbox(
            "Selecionar Todas as Macros",
            value=True,
            key="todas_macros_strip"
        )
        
        if todas_macros:
            macros_selecionadas = macros_disponiveis
        else:
            macros_selecionadas = st.multiselect(
                "Escolha as macros",
                options=macros_disponiveis,
                default=macros_disponiveis[:3] if len(macros_disponiveis) >= 3 else macros_disponiveis,
                key="macros_dropdown_strip"
            )
        
        if macros_selecionadas:
            df_analise = df_filtrado[df_filtrado["macro_mkt"].isin(macros_selecionadas)].copy()
        else:
            df_analise = df_filtrado.copy()
            macros_selecionadas = macros_disponiveis
    else:
        df_analise = df_filtrado.copy()
        macros_selecionadas = []
        st.info("ℹ️ Coluna 'macro_mkt' não encontrada.")

with col_filtro3:
    st.markdown("##### 🧬 Filtrar por Híbridos")
    
    if "hibrido" in df_analise.columns:
        hibridos_disponiveis = sorted(df_analise["hibrido"].dropna().unique().tolist())
        
        todos_hibridos = st.checkbox(
            "Selecionar Todos os Híbridos",
            value=True,
            key="todos_hibridos_strip"
        )
        
        if todos_hibridos:
            hibridos_selecionados = hibridos_disponiveis
        else:
            hibridos_selecionados = st.multiselect(
                "Escolha os híbridos",
                options=hibridos_disponiveis,
                default=hibridos_disponiveis[:5] if len(hibridos_disponiveis) >= 5 else hibridos_disponiveis,
                key="hibridos_dropdown_strip"
            )
        
        if hibridos_selecionados:
            df_analise = df_analise[df_analise["hibrido"].isin(hibridos_selecionados)].copy()
        else:
            st.warning("⚠️ Selecione pelo menos um híbrido.")
            hibridos_selecionados = hibridos_disponiveis
    else:
        st.error("❌ Coluna 'hibrido' não encontrada.")
        st.stop()

st.markdown("---")

# ----- MÉTRICAS -----
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

with col_m1:
    st.metric("Macros MKT", len(macros_selecionadas) if macros_selecionadas else 0)
with col_m2:
    st.metric("Híbridos", len(hibridos_selecionados))
with col_m3:
    st.metric("Registros", f"{len(df_analise):,}")
with col_m4:
    media_geral = df_analise[coluna_producao].mean()
    st.metric("Média Geral", f"{media_geral:,.1f}")
with col_m5:
    mediana_geral = df_analise[coluna_producao].median()
    st.metric("Mediana Geral", f"{mediana_geral:,.1f}")

st.markdown("---")

# ----- STRIP PLOT COM RÓTULOS E QUADRO DE MÉDIA -----
if len(df_analise) > 0 and len(hibridos_selecionados) > 0:
    
    # Calcular média por híbrido para ordenar
    medias_hibrido = df_analise.groupby('hibrido')[coluna_producao].mean().sort_values(ascending=False)
    ordem_hibridos = medias_hibrido.index.tolist()
    
    # Verificar se cidade_cod3 existe
    tem_cidade = 'cidade_cod3' in df_analise.columns
    
    # Opção para mostrar rótulos
    if tem_cidade:
        mostrar_rotulos = st.checkbox(
            "🏷️ Mostrar rótulos (cidade_cod3)",
            value=False,
            key="mostrar_rotulos_strip"
        )
    else:
        mostrar_rotulos = False
    
    # Preparar dados com jitter manual no eixo Y
    df_plot = df_analise.copy()
    
    # Criar mapeamento numérico para híbridos
    hibrido_map = {h: i for i, h in enumerate(ordem_hibridos)}
    df_plot['hibrido_num'] = df_plot['hibrido'].map(hibrido_map)
    
    # Adicionar jitter
    np.random.seed(42)
    df_plot['hibrido_jitter'] = df_plot['hibrido_num'] + np.random.uniform(-0.3, 0.3, len(df_plot))
    
    # Criar figura
    fig = go.Figure()
    
    # Cores
    cores = px.colors.qualitative.Set2
    
    # Adicionar pontos por híbrido
    for i, hibrido in enumerate(ordem_hibridos):
        df_h = df_plot[df_plot['hibrido'] == hibrido]
        
        cor = cores[i % len(cores)]
        
        # Calcular média do híbrido
        media_hibrido_valor = df_h[coluna_producao].mean()
        
        # Configurar texto e modo
        if mostrar_rotulos and tem_cidade:
            texto = df_h['cidade_cod3'].astype(str).tolist()
            modo = 'markers+text'
        else:
            texto = None
            modo = 'markers'
        
        # Hover template
        if tem_cidade:
            hover_texto = [
                f"<b>{cidade}</b><br>{opcoes_producao[coluna_producao]}: {prod:,.1f}<br>Híbrido: {hibrido}"
                for cidade, prod in zip(df_h['cidade_cod3'].astype(str), df_h[coluna_producao])
            ]
        else:
            hover_texto = [
                f"{opcoes_producao[coluna_producao]}: {prod:,.1f}<br>Híbrido: {hibrido}"
                for prod in df_h[coluna_producao]
            ]
        
        # Adicionar pontos
        fig.add_trace(go.Scatter(
            x=df_h[coluna_producao],
            y=df_h['hibrido_jitter'],
            mode=modo,
            name=hibrido,
            text=texto,
            textposition='top center',
            textfont=dict(size=8, color='black'),
            marker=dict(
                size=10,
                color=cor,
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            hovertext=hover_texto,
            hoverinfo='text'
        ))
        
        # Adicionar quadro com a média do híbrido
        fig.add_trace(go.Scatter(
            x=[media_hibrido_valor],
            y=[i],
            mode='markers+text',
            name=f'Média {hibrido}',
            text=[f'{media_hibrido_valor:,.0f}'],
            textposition='middle center',
            textfont=dict(size=9, color='white', family='Arial Black'),
            marker=dict(
                size=40,
                color=cor,
                symbol='square',
                opacity=0.9,
                line=dict(width=2, color='white')
            ),
            hovertemplate=f"<b>Média {hibrido}</b><br>{opcoes_producao[coluna_producao]}: {media_hibrido_valor:,.1f}<extra></extra>",
            showlegend=False
        ))
    
    # Adicionar linha de média geral (referência)
    fig.add_vline(
        x=media_geral,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"Média Geral: {media_geral:,.1f}",
        annotation_position="top"
    )
    
    # Layout
    fig.update_layout(
        title=f"Distribuição de {opcoes_producao[coluna_producao]} por Híbrido",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=PALETA_CORES['text_dark']),
        showlegend=False,
        height=max(500, len(hibridos_selecionados) * 45),
        xaxis=dict(
            title=opcoes_producao[coluna_producao],
            gridcolor='lightgray',
            gridwidth=0.5
        ),
        yaxis=dict(
            title="",
            tickmode='array',
            tickvals=list(range(len(ordem_hibridos))),
            ticktext=ordem_hibridos,
            gridcolor='lightgray',
            gridwidth=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ----- TABELA DE ESTATÍSTICAS -----
    st.markdown("##### 📊 Estatísticas por Híbrido")
    
    stats_hibrido = df_analise.groupby('hibrido')[coluna_producao].agg([
        ('Contagem', 'count'),
        ('Média', 'mean'),
        ('Mediana', 'median'),
        ('Desvio Padrão', 'std'),
        ('Mínimo', 'min'),
        ('Máximo', 'max'),
        ('CV %', lambda x: (x.std() / x.mean() * 100) if x.mean() != 0 else 0)
    ]).round(2).reset_index()
    
    stats_hibrido.columns = ['Híbrido', 'Contagem', 'Média', 'Mediana', 'Desvio Padrão', 'Mínimo', 'Máximo', 'CV %']
    stats_hibrido = stats_hibrido.sort_values('Média', ascending=False)
    
    criar_aggrid(stats_hibrido, altura=400, colunas_texto=['Híbrido'])
    
    # Download
    st.download_button(
        label="📥 Download Estatísticas (CSV)",
        data=stats_hibrido.to_csv(index=False).encode('utf-8'),
        file_name=f"estatisticas_{coluna_producao}.csv",
        mime="text/csv"
    )
    
    # ============================================================
    # ANÁLISE DE PROBABILIDADE (COM ESTATÍSTICA Z)
    # ============================================================
    
    st.markdown("---")
    
    # Título com botão de informação
    col_titulo_prob, col_info_prob = st.columns([11, 1])
    
    with col_titulo_prob:
        st.markdown("### 📈 Probabilidade de Atingir a Média (Estatística Z)")
    
    with col_info_prob:
        if st.button("ℹ️", key="btn_info_prob", help="Clique para ver como a probabilidade é calculada"):
            mostrar_explicacao_probabilidade()
    
    # Mostrar macros selecionadas
    if len(macros_selecionadas) <= 5:
        macros_texto = ", ".join([str(m) for m in macros_selecionadas])
    else:
        macros_texto = f"{len(macros_selecionadas)} macros selecionadas"
    
    st.info(f"📊 **Análise de consistência dos híbridos** | Macros: {macros_texto} | Faixa de tolerância: **±10% da média**")
    
    # Calcular probabilidade por híbrido usando Z-score
    probabilidades = []
    
    for hibrido in hibridos_selecionados:
        df_h = df_analise[df_analise['hibrido'] == hibrido][coluna_producao].dropna()
        
        if len(df_h) > 1:
            n_obs = len(df_h)
            media_hibrido = df_h.mean()
            std_hibrido = df_h.std()
            cv_hibrido = (std_hibrido / media_hibrido * 100) if media_hibrido != 0 else 0
            
            if std_hibrido > 0:
                limite_inferior = media_hibrido * 0.90
                limite_superior = media_hibrido * 1.10
                
                z_inferior = (limite_inferior - media_hibrido) / std_hibrido
                z_superior = (limite_superior - media_hibrido) / std_hibrido
                
                probabilidade = (stats.norm.cdf(z_superior) - stats.norm.cdf(z_inferior)) * 100
            else:
                probabilidade = 100.0
            
            probabilidades.append({
                'Híbrido': hibrido,
                'Observações': n_obs,
                'Média': round(media_hibrido, 1),
                'Desvio Padrão': round(std_hibrido, 1),
                'CV (%)': round(cv_hibrido, 1),
                'Probabilidade (%)': round(probabilidade, 1)
            })
        elif len(df_h) == 1:
            probabilidades.append({
                'Híbrido': hibrido,
                'Observações': 1,
                'Média': round(df_h.mean(), 1),
                'Desvio Padrão': 0.0,
                'CV (%)': 0.0,
                'Probabilidade (%)': None
            })
    
    # Criar DataFrame
    df_prob = pd.DataFrame(probabilidades)
    
    # Filtrar apenas híbridos com probabilidade calculável
    df_prob_valid = df_prob[df_prob['Probabilidade (%)'].notna()].copy()
    df_prob_valid = df_prob_valid.sort_values('Probabilidade (%)', ascending=False)
    
    # Classificação
    def classificar_probabilidade(prob):
        if pd.isna(prob):
            return "⚪ N/A"
        elif prob >= 75:
            return "🟢 Alta"
        elif prob >= 50:
            return "🟡 Média"
        elif prob >= 25:
            return "🟠 Baixa"
        else:
            return "🔴 Muito Baixa"
    
    df_prob['Classificação'] = df_prob['Probabilidade (%)'].apply(classificar_probabilidade)
    df_prob = df_prob[['Híbrido', 'Observações', 'Média', 'Desvio Padrão', 'CV (%)', 'Probabilidade (%)', 'Classificação']]
    df_prob = df_prob.sort_values('Probabilidade (%)', ascending=False, na_position='last')
    
    # Métricas resumo
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    
    with col_p1:
        hibridos_alta = len(df_prob[df_prob['Probabilidade (%)'] >= 75])
        st.metric("🟢 Alta (≥75%)", hibridos_alta)
    with col_p2:
        hibridos_media_prob = len(df_prob[(df_prob['Probabilidade (%)'] >= 50) & (df_prob['Probabilidade (%)'] < 75)])
        st.metric("🟡 Média (50-74%)", hibridos_media_prob)
    with col_p3:
        hibridos_baixa = len(df_prob[(df_prob['Probabilidade (%)'] >= 25) & (df_prob['Probabilidade (%)'] < 50)])
        st.metric("🟠 Baixa (25-49%)", hibridos_baixa)
    with col_p4:
        hibridos_muito_baixa = len(df_prob[df_prob['Probabilidade (%)'] < 25])
        st.metric("🔴 Muito Baixa (<25%)", hibridos_muito_baixa)
    
    st.markdown("---")
    
    # Gráfico de barras
    if len(df_prob_valid) > 0:
        fig_prob = px.bar(
            df_prob_valid.sort_values('Probabilidade (%)', ascending=True),
            x='Probabilidade (%)',
            y='Híbrido',
            orientation='h',
            color='Probabilidade (%)',
            color_continuous_scale='RdYlGn',
            title="Probabilidade de Atingir a Média (±10%) - Baseado na Estatística Z",
            text='Probabilidade (%)',
            hover_data=['CV (%)', 'Desvio Padrão', 'Observações']
        )
        
        fig_prob.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        fig_prob.add_vline(
            x=50,
            line_dash="dash",
            line_color="gray",
            line_width=2,
            annotation_text="50%",
            annotation_position="top"
        )
        
        fig_prob.add_vline(
            x=68.27,
            line_dash="dot",
            line_color="blue",
            line_width=1,
            annotation_text="68.3% (1σ)",
            annotation_position="bottom"
        )
        
        fig_prob.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color=PALETA_CORES['text_dark']),
            height=max(400, len(df_prob_valid) * 35),
            xaxis=dict(range=[0, 105]),
            showlegend=False
        )
        
        st.plotly_chart(fig_prob, use_container_width=True)
    
    # Tabela
    st.markdown("##### 📋 Tabela de Probabilidades")
    
    criar_aggrid(df_prob, altura=400, colunas_texto=['Híbrido', 'Classificação'])
    
    # Download
    st.download_button(
        label="📥 Download Probabilidades (CSV)",
        data=df_prob.to_csv(index=False).encode('utf-8'),
        file_name=f"probabilidades_zscore_{coluna_producao}.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")

st.markdown(f"""
    <div style='text-align: center; color: {PALETA_CORES['primary']}; padding: 2rem 0;'>
        <p style='font-weight: 600;'>Análise de Dados | Sistema de Produção Agrícola</p>
        <p style='font-size: 0.875rem; color: {PALETA_CORES['secondary']};'>
            Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}
        </p>
    </div>
""", unsafe_allow_html=True)