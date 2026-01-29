# pages/01_Qualidade_dos_Dados.py
# ============================================================
# Sistema de Produção Agrícola - Qualidade dos Dados
# Análise detalhada da qualidade e completude dos dados
# Versão 3.6 - Com Modal Corrigido
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from config import PALETA_CORES
from utils import criar_breadcrumb, criar_aggrid, logger

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Qualidade dos Dados",
    page_icon="📊",
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
    
    .quality-score {{
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
    }}
    
    .quality-excellent {{ color: #00a859; }}
    .quality-good {{ color: #72d8a8; }}
    .quality-warning {{ color: #ff9933; }}
    .quality-poor {{ color: #dc3545; }}
    
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
# FUNÇÕES AUXILIARES
# ============================================================

def calcular_score_qualidade(df: pd.DataFrame) -> dict:
    """Calcula score de qualidade dos dados (0-100)"""
    total_valores = df.size
    valores_nulos = df.isnull().sum().sum()
    duplicatas = df.duplicated().sum()
    
    completude = ((total_valores - valores_nulos) / total_valores) * 100 if total_valores > 0 else 0
    score_completude = (completude / 100) * 60
    
    unicidade = ((len(df) - duplicatas) / len(df)) * 100 if len(df) > 0 else 0
    score_unicidade = (unicidade / 100) * 30
    
    score_consistencia = 10
    colunas_num = df.select_dtypes(include=['number']).columns
    
    for col in colunas_num:
        if len(df[col].dropna()) > 0 and df[col].std() == 0:
            score_consistencia -= 2
    
    score_total = score_completude + score_unicidade + max(0, score_consistencia)
    
    return {
        "score_total": round(float(score_total), 2),
        "completude": round(float(completude), 2),
        "unicidade": round(float(unicidade), 2),
        "score_completude": round(float(score_completude), 2),
        "score_unicidade": round(float(score_unicidade), 2),
        "score_consistencia": round(float(score_consistencia), 2)
    }


def get_quality_class(score: float) -> tuple:
    """Retorna classe e cor baseado no score"""
    if score >= 90:
        return "Excelente", "quality-excellent"
    elif score >= 75:
        return "Bom", "quality-good"
    elif score >= 60:
        return "Regular", "quality-warning"
    else:
        return "Ruim", "quality-poor"


def analisar_valores_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Análise detalhada de valores nulos por coluna"""
    nulos = df.isnull().sum()
    total = len(df)
    
    percentuais = [(n / total * 100) for n in nulos.values] if total > 0 else [0] * len(nulos)
    
    analise = pd.DataFrame({
        'Coluna': nulos.index,
        'Valores_Nulos': nulos.values,
        'Percentual': [round(p, 2) for p in percentuais],
        'Valores_Preenchidos': total - nulos.values
    })
    
    analise = analise[analise['Valores_Nulos'] > 0].sort_values('Percentual', ascending=False)
    
    return analise


def analisar_outliers(df: pd.DataFrame, coluna: str) -> dict:
    """Detecta outliers usando IQR"""
    if not pd.api.types.is_numeric_dtype(df[coluna]):
        return None
    
    Q1 = df[coluna].quantile(0.25)
    Q3 = df[coluna].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[coluna] < lower_bound) | (df[coluna] > upper_bound)]
    
    percentual = round((len(outliers) / len(df) * 100), 2) if len(df) > 0 else 0
    
    return {
        'total_outliers': len(outliers),
        'percentual': percentual,
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'outliers_inferiores': len(df[df[coluna] < lower_bound]),
        'outliers_superiores': len(df[df[coluna] > upper_bound])
    }


def medalha(pos: int) -> str:
    """Retorna emoji de medalha baseado na posição"""
    if pos == 1:
        return "🥇"
    elif pos == 2:
        return "🥈"
    elif pos == 3:
        return "🥉"
    return ""


# ============================================================
# MODAL DE EXPLICAÇÃO DO SCORE
# ============================================================
@st.dialog("📊 Como o Score de Qualidade é Calculado", width="large")
def mostrar_explicacao_score():
    """Modal com explicação detalhada do cálculo do score"""
    
    st.markdown("""
    ## 🎯 Score de Qualidade Total (0-100 pontos)
    
    O score de qualidade é uma métrica composta que avalia três dimensões principais dos seus dados:
    
    ---
    
    ### 📊 1. Completude (60% do score - máx. 60 pts)
    
    **O que mede:** Percentual de valores preenchidos (não nulos) em todo o dataset.
    
    **Fórmula:**
    
    `Completude = (Total de Valores - Valores Nulos) / Total de Valores × 100`
    
    `Score Completude = Completude × 0.60`
    
    **Interpretação:**
    - 🟢 **100%**: Todos os campos estão preenchidos
    - 🟡 **80-99%**: Alguns campos vazios, mas aceitável
    - 🔴 **< 80%**: Muitos dados faltantes, requer atenção
    
    ---
    
    ### 🔑 2. Unicidade (30% do score - máx. 30 pts)
    
    **O que mede:** Percentual de registros únicos (sem duplicatas).
    
    **Fórmula:**
    
    `Unicidade = (Total de Registros - Duplicatas) / Total de Registros × 100`
    
    `Score Unicidade = Unicidade × 0.30`
    
    **Interpretação:**
    - 🟢 **100%**: Nenhuma duplicata encontrada
    - 🟡 **95-99%**: Poucas duplicatas
    - 🔴 **< 95%**: Muitas duplicatas, verificar dados
    
    ---
    
    ### ✓ 3. Consistência (10% do score - máx. 10 pts)
    
    **O que mede:** Variabilidade dos dados numéricos.
    
    **Fórmula:**
    
    `Score Consistência = 10 - (2 × número de colunas com desvio padrão = 0)`
    
    **Interpretação:**
    - 🟢 **10 pts**: Todas as colunas têm variação natural
    - 🟡 **6-8 pts**: Algumas colunas sem variação
    - 🔴 **< 6 pts**: Muitas colunas constantes (possível erro)
    
    ---
    
    ### 🏆 Classificação Final
    
    | Score | Classificação | Significado |
    |-------|---------------|-------------|
    | 90-100 | 🟢 **Excelente** | Dados de alta qualidade, prontos para análise |
    | 75-89 | 🟢 **Bom** | Dados confiáveis, pequenas melhorias possíveis |
    | 60-74 | 🟡 **Regular** | Dados utilizáveis, mas requerem atenção |
    | < 60 | 🔴 **Ruim** | Dados com problemas, necessitam correção |
    
    ---
    
    ### 💡 Dicas para Melhorar o Score
    
    1. **Completude baixa?** 
       - Identifique colunas com muitos nulos
       - Preencha valores faltantes ou remova colunas desnecessárias
    
    2. **Unicidade baixa?**
       - Verifique registros duplicados
       - Identifique a causa (importação duplicada, erro de sistema)
    
    3. **Consistência baixa?**
       - Verifique colunas com valores constantes
       - Pode indicar erro na coleta ou dados default
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Entendi!", key="btn_fechar_modal", type="primary", use_container_width=True):
            st.rerun()


# ============================================================
# CABEÇALHO
# ============================================================
st.markdown(f"""
    <div style='background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,104,56,0.2);'>
        <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>📊 Qualidade dos Dados</h1>
        <p style='color: white; margin-top: 0.5rem; opacity: 0.95;'>Análise detalhada da completude e qualidade dos dados de produção</p>
    </div>
""", unsafe_allow_html=True)

criar_breadcrumb("Qualidade dos Dados")

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

logger.info(f"📊 Página de Qualidade carregada: {len(df)} registros")

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
# SCORE DE QUALIDADE GERAL
# ============================================================
col_titulo, col_info = st.columns([12, 1])

with col_titulo:
    st.markdown("### 🎯 Score de Qualidade Geral")

with col_info:
    if st.button("ℹ️", key="btn_info_score", help="Clique para ver como o score é calculado"):
        mostrar_explicacao_score()

score_info = calcular_score_qualidade(df)
quality_class, quality_color = get_quality_class(score_info['score_total'])

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="quality-score {quality_color}">
                {score_info['score_total']}
            </div>
            <div style="text-align: center; color: {PALETA_CORES['text_dark']}; font-size: 1.2rem; margin-top: 0.5rem;">
                Qualidade: {quality_class}
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.metric(
        label="📊 Completude",
        value=f"{score_info['completude']}%",
        delta=f"{score_info['score_completude']:.0f} pts"
    )

with col3:
    st.metric(
        label="🔑 Unicidade",
        value=f"{score_info['unicidade']}%",
        delta=f"{score_info['score_unicidade']:.0f} pts"
    )

with col4:
    st.metric(
        label="✓ Consistência",
        value=f"{score_info['score_consistencia']:.0f} pts",
        delta="10 pts máx"
    )

st.markdown("---")

# ============================================================
# MÉTRICAS PRINCIPAIS
# ============================================================
st.markdown("### 📋 Resumo Executivo")

col1, col2, col3, col4, col5 = st.columns(5)

total_valores = df.size
valores_nulos = df.isnull().sum().sum()
duplicatas = df.duplicated().sum()
colunas_com_nulos = (df.isnull().sum() > 0).sum()

with col1:
    st.metric(label="📝 Total de Registros", value=f"{len(df):,}")

with col2:
    perc_nulos = (valores_nulos / total_valores * 100) if total_valores > 0 else 0
    st.metric(
        label="⚠️ Valores Nulos",
        value=f"{valores_nulos:,}",
        delta=f"{perc_nulos:.2f}%",
        delta_color="inverse"
    )

with col3:
    st.metric(
        label="🔁 Duplicatas",
        value=f"{duplicatas:,}",
        delta=f"{(duplicatas/len(df)*100):.2f}%" if len(df) > 0 else "0%",
        delta_color="inverse"
    )

with col4:
    st.metric(label="📊 Total de Colunas", value=len(df.columns))

with col5:
    st.metric(
        label="⚠️ Colunas com Nulos",
        value=colunas_com_nulos,
        delta=f"{(colunas_com_nulos/len(df.columns)*100):.1f}%" if len(df.columns) > 0 else "0%",
        delta_color="inverse"
    )

st.markdown("---")

# ============================================================
# GRÁFICO DE QUALIDADE POR DIMENSÃO
# ============================================================
st.markdown("### 📊 Análise Multidimensional de Qualidade")

fig = go.Figure()

categorias = ['Completude', 'Unicidade', 'Consistência']
valores_radar = [
    score_info['completude'],
    score_info['unicidade'],
    (score_info['score_consistencia'] / 10 * 100)
]

fig.add_trace(go.Scatterpolar(
    r=valores_radar,
    theta=categorias,
    fill='toself',
    name='Score Atual',
    line_color=PALETA_CORES['primary'],
    fillcolor=PALETA_CORES['accent'],
    opacity=0.6
))

fig.add_trace(go.Scatterpolar(
    r=[100, 100, 100],
    theta=categorias,
    fill='toself',
    name='Score Ideal',
    line_color=PALETA_CORES['secondary'],
    fillcolor=PALETA_CORES['success'],
    opacity=0.3
))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    title="Qualidade por Dimensão",
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(color=PALETA_CORES['text_dark'])
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# ANÁLISE DETALHADA EM TABS
# ============================================================
st.markdown("""
    <div class="section-header">
        <h2 class="section-title">🔍 Análise Detalhada</h2>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Valores Nulos",
    "📈 Estatísticas",
    "📉 Distribuições",
    "🎯 Outliers",
    "🔄 Comparações"
])

# ============================================================
# TAB 1: VALORES NULOS
# ============================================================
with tab1:
    st.markdown("#### Análise de Valores Nulos por Coluna")
    
    analise_nulos = analisar_valores_nulos(df_filtrado)
    
    if len(analise_nulos) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                analise_nulos,
                x='Coluna',
                y='Percentual',
                title='Percentual de Valores Nulos por Coluna',
                color='Percentual',
                color_continuous_scale='Reds',
                labels={'Percentual': 'Percentual de Nulos (%)'}
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark']),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### Top 5 Colunas com Mais Nulos")
            for idx, row in analise_nulos.head(5).iterrows():
                st.markdown(f"""
                    <div style='background: white; padding: 1rem; border-radius: 6px; 
                                margin-bottom: 0.5rem; border-left: 4px solid #dc3545;'>
                        <strong>{row['Coluna']}</strong><br>
                        <span style='color: #dc3545; font-size: 1.5rem;'>{row['Percentual']}%</span><br>
                        <small>{row['Valores_Nulos']:,} valores nulos</small>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("##### Detalhamento Completo")
        criar_aggrid(analise_nulos, altura=400, colunas_texto=['Coluna'])
        
        if len(df_filtrado.columns) > 1:
            st.markdown("##### Matriz de Valores Nulos")
            nulos_matrix = df_filtrado.isnull().astype(int)
            corr_nulos = nulos_matrix.corr()
            
            fig = px.imshow(
                corr_nulos,
                text_auto='.2f',
                aspect="auto",
                color_continuous_scale='RdYlGn_r',
                title="Correlação entre Padrões de Nulos"
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark'])
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ Excelente! Nenhum valor nulo encontrado nos dados!")

# ============================================================
# TAB 2: ESTATÍSTICAS
# ============================================================
with tab2:
    st.markdown("#### Estatísticas Descritivas")
    
    df_base_stats = df_filtrado.copy()
    
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        st.markdown("##### 🧬 Filtrar por Híbridos")
        
        if "hibrido" in df_base_stats.columns:
            hibridos_disponiveis = sorted(df_base_stats["hibrido"].dropna().unique().tolist())
            
            todos_hibridos = st.checkbox(
                "Selecionar Todos os Híbridos",
                value=True,
                key="todos_hibridos_stats"
            )
            
            if todos_hibridos:
                hibridos_selecionados = hibridos_disponiveis
                st.success(f"✅ {len(hibridos_disponiveis)} híbridos selecionados")
            else:
                hibridos_selecionados = st.multiselect(
                    "Escolha os híbridos",
                    options=hibridos_disponiveis,
                    default=[],
                    key="hibridos_dropdown_stats"
                )
            
            if hibridos_selecionados:
                df_stats = df_base_stats[df_base_stats["hibrido"].isin(hibridos_selecionados)].copy()
            else:
                df_stats = df_base_stats.copy()
                st.warning("⚠️ Nenhum híbrido selecionado. Mostrando todos.")
                hibridos_selecionados = hibridos_disponiveis
        else:
            df_stats = df_base_stats.copy()
            st.info("ℹ️ Coluna 'hibrido' não encontrada.")
            hibridos_selecionados = []
    
    with col_filtro2:
        st.markdown("##### 📊 Selecionar Colunas Numéricas")
        
        colunas_numericas_disponiveis = df_base_stats.select_dtypes(include=['number']).columns.tolist()
        
        if 'safra' in colunas_numericas_disponiveis:
            colunas_numericas_disponiveis.remove('safra')
        
        st.caption(f"📋 {len(colunas_numericas_disponiveis)} colunas numéricas disponíveis")
        
        if colunas_numericas_disponiveis:
            todas_colunas = st.checkbox(
                "Selecionar Todas as Colunas",
                value=True,
                key="todas_colunas_stats"
            )
            
            if todas_colunas:
                colunas_selecionadas = colunas_numericas_disponiveis
                st.success(f"✅ {len(colunas_numericas_disponiveis)} colunas selecionadas")
            else:
                colunas_selecionadas = st.multiselect(
                    "Escolha as colunas",
                    options=colunas_numericas_disponiveis,
                    default=[],
                    key="colunas_dropdown_stats"
                )
        else:
            colunas_selecionadas = []
            st.warning("⚠️ Nenhuma coluna numérica disponível.")
    
    st.markdown("---")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("Híbridos Selecionados", len(hibridos_selecionados) if hibridos_selecionados else 0)
    with col_info2:
        st.metric("Registros Filtrados", f"{len(df_stats):,}")
    with col_info3:
        st.metric("Colunas Selecionadas", len(colunas_selecionadas) if colunas_selecionadas else 0)
    
    st.markdown("---")
    
    if colunas_selecionadas and len(df_stats) > 0:
        
        st.markdown("##### Resumo Estatístico")
        
        stats = df_stats[colunas_selecionadas].describe().T
        stats['skewness'] = df_stats[colunas_selecionadas].skew()
        stats['kurtosis'] = df_stats[colunas_selecionadas].kurtosis()
        stats['cv'] = (stats['std'] / stats['mean'] * 100).round(2)
        stats['missing'] = df_stats[colunas_selecionadas].isnull().sum()
        stats['missing_%'] = (stats['missing'] / len(df_stats) * 100).round(2)
        
        colunas_ordem = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max', 
                        'skewness', 'kurtosis', 'cv', 'missing', 'missing_%']
        stats = stats[[col for col in colunas_ordem if col in stats.columns]]
        
        stats_display = stats.reset_index()
        stats_display.columns = ['Coluna'] + list(stats.columns)
        
        for col in stats_display.columns:
            if col != 'Coluna':
                stats_display[col] = stats_display[col].round(2)
        
        criar_aggrid(stats_display, altura=400, colunas_texto=['Coluna'])
        
        st.download_button(
            label="📥 Download Estatísticas (CSV)",
            data=stats.to_csv().encode('utf-8'),
            file_name="estatisticas_descritivas.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        st.markdown("##### Coeficiente de Variação (CV%)")
        
        cv_data = pd.DataFrame({
            'Coluna': stats.index,
            'CV': stats['cv'].values
        }).sort_values('CV', ascending=False)
        
        fig = px.bar(
            cv_data, x='Coluna', y='CV',
            title='Coeficiente de Variação por Coluna',
            color='CV', color_continuous_scale='Viridis',
            labels={'CV': 'CV (%)'}, text='CV'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color=PALETA_CORES['text_dark']),
            xaxis_tickangle=-45, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Interpretação do Coeficiente de Variação:**
        - CV < 15%: Baixa variabilidade (dados homogêneos)
        - CV 15-30%: Variabilidade moderada
        - CV > 30%: Alta variabilidade (dados heterogêneos)
        """)
        
        st.markdown("---")
        
        if "hibrido" in df_base_stats.columns and len(hibridos_selecionados) > 1:
            st.markdown("##### 📊 Comparação entre Híbridos")
            
            coluna_comparacao = st.selectbox(
                "Selecione uma coluna para comparar entre híbridos",
                options=colunas_selecionadas,
                key="coluna_comparacao_hibridos"
            )
            
            col_comp1, col_comp2 = st.columns(2)
            
            with col_comp1:
                fig_box = px.box(
                    df_stats, x='hibrido', y=coluna_comparacao,
                    title=f'Distribuição de {coluna_comparacao} por Híbrido',
                    color='hibrido', color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_box.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    font=dict(color=PALETA_CORES['text_dark']),
                    xaxis_tickangle=-45, showlegend=False
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col_comp2:
                fig_violin = px.violin(
                    df_stats, x='hibrido', y=coluna_comparacao,
                    title=f'Densidade de {coluna_comparacao} por Híbrido',
                    color='hibrido', box=True,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_violin.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    font=dict(color=PALETA_CORES['text_dark']),
                    xaxis_tickangle=-45, showlegend=False
                )
                st.plotly_chart(fig_violin, use_container_width=True)
            
            st.markdown("##### Médias por Híbrido")
            medias_hibridos = df_stats.groupby('hibrido')[colunas_selecionadas].mean().round(2)
            
            medias_display = medias_hibridos.reset_index()
            medias_display.columns = ['Híbrido'] + list(medias_hibridos.columns)
            
            criar_aggrid(medias_display, altura=400, colunas_texto=['Híbrido'])
            
            st.download_button(
                label="📥 Download Médias por Híbrido (CSV)",
                data=medias_hibridos.to_csv().encode('utf-8'),
                file_name="medias_por_hibrido.csv",
                mime="text/csv"
            )
            
            st.markdown("##### Heatmap de Médias")
            fig_heat = px.imshow(
                medias_hibridos[colunas_selecionadas].T,
                labels=dict(x="Híbrido", y="Coluna", color="Valor"),
                x=medias_hibridos.index, y=colunas_selecionadas,
                color_continuous_scale='RdYlGn', aspect="auto", text_auto='.2f'
            )
            fig_heat.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark'])
            )
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.markdown("##### 🏆 Ranking por Coluna")
            
            ranking_col = st.selectbox(
                "Selecione uma coluna para ranking",
                options=colunas_selecionadas,
                key="ranking_coluna"
            )
            
            ranking_df = medias_hibridos[[ranking_col]].sort_values(ranking_col, ascending=False).reset_index()
            ranking_df['Posição'] = range(1, len(ranking_df) + 1)
            ranking_df['🏆'] = ranking_df['Posição'].apply(medalha)
            ranking_df = ranking_df[['🏆', 'Posição', 'hibrido', ranking_col]]
            ranking_df.columns = ['🏆', 'Posição', 'Híbrido', 'Média']
            ranking_df['Média'] = ranking_df['Média'].round(2)
            
            criar_aggrid(ranking_df, altura=400, colunas_texto=['🏆', 'Híbrido'])
        
        st.markdown("---")
        
        if len(colunas_selecionadas) > 1:
            st.markdown("##### 🔗 Matriz de Correlação")
            
            corr_matrix = df_stats[colunas_selecionadas].corr()
            
            fig_corr = px.imshow(
                corr_matrix, text_auto='.2f', aspect="auto",
                color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                title="Correlação entre Variáveis"
            )
            fig_corr.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark'])
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.markdown("##### Tabela de Correlação")
            
            corr_display = corr_matrix.reset_index()
            corr_display.columns = ['Variável'] + list(corr_matrix.columns)
            
            for col in corr_display.columns:
                if col != 'Variável':
                    corr_display[col] = corr_display[col].round(3)
            
            criar_aggrid(corr_display, altura=300, colunas_texto=['Variável'])
            
            st.info("""
            **Interpretação:**
            - Próximo de +1: Correlação positiva forte
            - Próximo de 0: Sem correlação
            - Próximo de -1: Correlação negativa forte
            """)
    
    elif not colunas_selecionadas:
        st.warning("⚠️ Selecione pelo menos uma coluna numérica para análise.")
    else:
        st.warning("⚠️ Nenhum dado disponível com os filtros aplicados.")

# ============================================================
# TAB 3: DISTRIBUIÇÕES
# ============================================================
with tab3:
    st.markdown("#### Análise de Distribuições")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns([1, 1, 1])
    
    with col_filtro1:
        st.markdown("##### 🧬 Filtrar por Híbridos")
        
        if "hibrido" in df_filtrado.columns:
            hibridos_dist = sorted(df_filtrado["hibrido"].dropna().unique().tolist())
            
            todos_hibridos_dist = st.checkbox(
                "Selecionar Todos os Híbridos",
                value=True,
                key="todos_hibridos_dist"
            )
            
            if todos_hibridos_dist:
                hibridos_selecionados_dist = hibridos_dist
            else:
                hibridos_selecionados_dist = st.multiselect(
                    "Escolha os híbridos",
                    options=hibridos_dist,
                    default=[],
                    key="hibridos_dropdown_dist"
                )
            
            if hibridos_selecionados_dist:
                df_dist = df_filtrado[df_filtrado["hibrido"].isin(hibridos_selecionados_dist)].copy()
            else:
                df_dist = df_filtrado.copy()
                hibridos_selecionados_dist = hibridos_dist
        else:
            df_dist = df_filtrado.copy()
            hibridos_selecionados_dist = []
    
    with col_filtro2:
        st.markdown("##### 📊 Selecionar Coluna")
        
        colunas_disponiveis = df_dist.columns.tolist()
        
        coluna_selecionada = st.selectbox(
            "Selecione uma coluna",
            colunas_disponiveis,
            key="dist_coluna"
        )
    
    with col_filtro3:
        st.markdown("##### 📈 Tipo de Gráfico")
        
        tipo_grafico = st.radio(
            "Escolha o tipo",
            ["Histograma", "Box Plot", "Violin Plot"],
            key="tipo_grafico",
            horizontal=True
        )
    
    st.markdown("---")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.metric("Híbridos Selecionados", len(hibridos_selecionados_dist) if hibridos_selecionados_dist else 0)
    with col_m2:
        st.metric("Registros", f"{len(df_dist):,}")
    with col_m3:
        st.metric("Coluna", coluna_selecionada)
    
    st.markdown("---")
    
    if len(df_dist) > 0:
        if pd.api.types.is_numeric_dtype(df_dist[coluna_selecionada]):
            
            if "hibrido" in df_dist.columns and len(hibridos_selecionados_dist) > 1:
                comparar_hibridos = st.checkbox(
                    "📊 Comparar distribuição por híbrido",
                    value=False,
                    key="comparar_hibridos_dist"
                )
            else:
                comparar_hibridos = False
            
            if comparar_hibridos:
                if tipo_grafico == "Histograma":
                    fig = px.histogram(
                        df_dist, x=coluna_selecionada, 
                        color='hibrido',
                        nbins=30,
                        title=f"Distribuição de {coluna_selecionada} por Híbrido",
                        barmode='overlay',
                        opacity=0.7,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                elif tipo_grafico == "Box Plot":
                    fig = px.box(
                        df_dist, x='hibrido', y=coluna_selecionada,
                        title=f"Box Plot de {coluna_selecionada} por Híbrido",
                        color='hibrido',
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        points="outliers"
                    )
                else:
                    fig = px.violin(
                        df_dist, x='hibrido', y=coluna_selecionada,
                        title=f"Violin Plot de {coluna_selecionada} por Híbrido",
                        color='hibrido',
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        box=True, points="outliers"
                    )
                
                fig.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    font=dict(color=PALETA_CORES['text_dark']),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("##### 📊 Estatísticas por Híbrido")
                
                stats_hibrido = df_dist.groupby('hibrido')[coluna_selecionada].agg([
                    ('Contagem', 'count'),
                    ('Média', 'mean'),
                    ('Mediana', 'median'),
                    ('Desvio Padrão', 'std'),
                    ('Mínimo', 'min'),
                    ('Máximo', 'max')
                ]).round(2).reset_index()
                stats_hibrido.columns = ['Híbrido', 'Contagem', 'Média', 'Mediana', 'Desvio Padrão', 'Mínimo', 'Máximo']
                
                criar_aggrid(stats_hibrido, altura=300, colunas_texto=['Híbrido'])
                
            else:
                if tipo_grafico == "Histograma":
                    fig = px.histogram(
                        df_dist, x=coluna_selecionada, nbins=50,
                        title=f"Distribuição de {coluna_selecionada}",
                        color_discrete_sequence=[PALETA_CORES['primary']],
                        marginal="box"
                    )
                elif tipo_grafico == "Box Plot":
                    fig = px.box(
                        df_dist, y=coluna_selecionada,
                        title=f"Box Plot de {coluna_selecionada}",
                        color_discrete_sequence=[PALETA_CORES['secondary']],
                        points="outliers"
                    )
                else:
                    fig = px.violin(
                        df_dist, y=coluna_selecionada,
                        title=f"Violin Plot de {coluna_selecionada}",
                        color_discrete_sequence=[PALETA_CORES['accent']],
                        box=True, points="outliers"
                    )
                
                fig.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    font=dict(color=PALETA_CORES['text_dark'])
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("##### 📈 Estatísticas Gerais")
            col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
            
            with col_a:
                st.metric("Contagem", f"{df_dist[coluna_selecionada].count():,}")
            with col_b:
                st.metric("Média", f"{df_dist[coluna_selecionada].mean():.2f}")
            with col_c:
                st.metric("Mediana", f"{df_dist[coluna_selecionada].median():.2f}")
            with col_d:
                st.metric("Desvio Padrão", f"{df_dist[coluna_selecionada].std():.2f}")
            with col_e:
                st.metric("Assimetria", f"{df_dist[coluna_selecionada].skew():.2f}")
            with col_f:
                st.metric("Curtose", f"{df_dist[coluna_selecionada].kurtosis():.2f}")
        
        else:
            value_counts = df_dist[coluna_selecionada].value_counts().head(20)
            
            fig = px.bar(
                x=value_counts.index, y=value_counts.values,
                title=f"Frequência de {coluna_selecionada} (Top 20)",
                labels={'x': coluna_selecionada, 'y': 'Frequência'},
                color_discrete_sequence=[PALETA_CORES['secondary']]
            )
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark']),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
            
            if coluna_selecionada == 'hibrido' and len(hibridos_selecionados_dist) > 1:
                st.markdown("##### 🥧 Distribuição Percentual")
                
                fig_pie = px.pie(
                    values=value_counts.values,
                    names=value_counts.index,
                    title=f"Distribuição de {coluna_selecionada}",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    font=dict(color=PALETA_CORES['text_dark'])
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Valores Únicos", df_dist[coluna_selecionada].nunique())
            with col_b:
                st.metric("Mais Frequente", str(value_counts.index[0]) if len(value_counts) > 0 else "N/A")
            with col_c:
                st.metric("Frequência Máxima", f"{value_counts.values[0]:,}" if len(value_counts) > 0 else "0")
    else:
        st.warning("⚠️ Nenhum dado disponível com os filtros aplicados.")

# ============================================================
# TAB 4: OUTLIERS
# ============================================================
with tab4:
    st.markdown("#### Detecção de Outliers")
    
    colunas_numericas = df_filtrado.select_dtypes(include=['number']).columns.tolist()
    
    if 'safra' in colunas_numericas:
        colunas_numericas.remove('safra')
    
    if colunas_numericas:
        coluna_outlier = st.selectbox(
            "Selecione uma coluna numérica",
            colunas_numericas,
            key="outlier_coluna"
        )
        
        outlier_info = analisar_outliers(df_filtrado, coluna_outlier)
        
        if outlier_info:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Outliers",
                    f"{outlier_info['total_outliers']:,}",
                    delta=f"{outlier_info['percentual']:.2f}%"
                )
            with col2:
                st.metric("Outliers Inferiores", f"{outlier_info['outliers_inferiores']:,}")
            with col3:
                st.metric("Outliers Superiores", f"{outlier_info['outliers_superiores']:,}")
            with col4:
                st.metric("Valores Normais", f"{len(df_filtrado) - outlier_info['total_outliers']:,}")
            
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=df_filtrado[coluna_outlier], name=coluna_outlier,
                boxmean='sd', marker_color=PALETA_CORES['primary']
            ))
            fig.add_hline(y=outlier_info['upper_bound'], line_dash="dash", line_color="red", annotation_text="Limite Superior")
            fig.add_hline(y=outlier_info['lower_bound'], line_dash="dash", line_color="red", annotation_text="Limite Inferior")
            fig.update_layout(
                title=f"Box Plot com Limites de Outliers - {coluna_outlier}",
                plot_bgcolor='white', paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark'])
            )
            st.plotly_chart(fig, use_container_width=True)
            
            if outlier_info['total_outliers'] > 0:
                st.markdown("##### Registros com Outliers")
                
                outliers_df = df_filtrado[
                    (df_filtrado[coluna_outlier] < outlier_info['lower_bound']) |
                    (df_filtrado[coluna_outlier] > outlier_info['upper_bound'])
                ].copy()
                
                outliers_df['Tipo_Outlier'] = outliers_df[coluna_outlier].apply(
                    lambda x: 'Inferior' if x < outlier_info['lower_bound'] else 'Superior'
                )
                
                criar_aggrid(outliers_df, altura=300)
                
                st.download_button(
                    label="📥 Download Outliers (CSV)",
                    data=outliers_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"outliers_{coluna_outlier}.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ Nenhum outlier detectado!")
            
            st.info(f"""
            **Método IQR:**
            - Limite Inferior: {outlier_info['lower_bound']:.2f}
            - Limite Superior: {outlier_info['upper_bound']:.2f}
            """)
    else:
        st.warning("⚠️ Nenhuma coluna numérica disponível.")

# ============================================================
# TAB 5: COMPARAÇÕES
# ============================================================
with tab5:
    st.markdown("#### Comparação: Dados Originais vs Filtrados")
    
    if "df_raw" in st.session_state and "df_filtrado" in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔹 Dados Originais")
            
            score_raw = calcular_score_qualidade(df_raw)
            quality_raw, color_raw = get_quality_class(score_raw['score_total'])
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="quality-score {color_raw}">{score_raw['score_total']}</div>
                    <div style="text-align: center; color: {PALETA_CORES['text_dark']}; font-size: 1rem; margin-top: 0.5rem;">{quality_raw}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.metric("Registros", f"{len(df_raw):,}")
            st.metric("Completude", f"{score_raw['completude']:.2f}%")
            st.metric("Valores Nulos", f"{df_raw.isnull().sum().sum():,}")
            st.metric("Duplicatas", f"{df_raw.duplicated().sum():,}")
        
        with col2:
            st.markdown("##### 🔹 Dados Filtrados")
            
            score_filt = calcular_score_qualidade(df_filtrado)
            quality_filt, color_filt = get_quality_class(score_filt['score_total'])
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="quality-score {color_filt}">{score_filt['score_total']}</div>
                    <div style="text-align: center; color: {PALETA_CORES['text_dark']}; font-size: 1rem; margin-top: 0.5rem;">{quality_filt}</div>
                </div>
            """, unsafe_allow_html=True)
            
            delta_registros = len(df_filtrado) - len(df_raw)
            delta_completude = score_filt['completude'] - score_raw['completude']
            delta_nulos = df_filtrado.isnull().sum().sum() - df_raw.isnull().sum().sum()
            delta_duplicatas = df_filtrado.duplicated().sum() - df_raw.duplicated().sum()
            
            st.metric("Registros", f"{len(df_filtrado):,}", delta=f"{delta_registros:,}")
            st.metric("Completude", f"{score_filt['completude']:.2f}%", delta=f"{delta_completude:+.2f}%")
            st.metric("Valores Nulos", f"{df_filtrado.isnull().sum().sum():,}", delta=f"{delta_nulos:,}")
            st.metric("Duplicatas", f"{df_filtrado.duplicated().sum():,}", delta=f"{delta_duplicatas:,}")
        
        st.markdown("##### Comparação Visual dos Scores")
        
        comparacao = pd.DataFrame({
            'Tipo': ['Original', 'Filtrado', 'Original', 'Filtrado', 'Original', 'Filtrado'],
            'Dimensão': ['Completude', 'Completude', 'Unicidade', 'Unicidade', 'Consistência', 'Consistência'],
            'Score': [
                score_raw['completude'], score_filt['completude'],
                score_raw['unicidade'], score_filt['unicidade'],
                (score_raw['score_consistencia'] / 10 * 100),
                (score_filt['score_consistencia'] / 10 * 100)
            ]
        })
        
        fig = px.bar(
            comparacao, x='Dimensão', y='Score', color='Tipo', barmode='group',
            title='Comparação de Qualidade por Dimensão',
            color_discrete_map={'Original': '#ff9933', 'Filtrado': PALETA_CORES['primary']}
        )
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color=PALETA_CORES['text_dark'])
        )
        st.plotly_chart(fig, use_container_width=True)
        
        impacto_qualidade = score_filt['score_total'] - score_raw['score_total']
        
        if impacto_qualidade > 0:
            st.success(f"✅ Qualidade melhorou em {impacto_qualidade:.2f} pontos")
        elif impacto_qualidade < 0:
            st.warning(f"⚠️ Qualidade caiu em {abs(impacto_qualidade):.2f} pontos")
        else:
            st.info("ℹ️ Qualidade permaneceu igual")
    
    else:
        st.info("ℹ️ Execute a página principal primeiro.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")

st.markdown(f"""
    <div style='text-align: center; color: {PALETA_CORES['primary']}; padding: 2rem 0;'>
        <p style='font-weight: 600;'>Análise de Qualidade dos Dados | Sistema de Produção Agrícola</p>
        <p style='font-size: 0.875rem; color: {PALETA_CORES['secondary']};'>
            Última atualização: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}
        </p>
    </div>
""", unsafe_allow_html=True)