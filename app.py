# app.py
# ============================================================
# Sistema de Produção Agrícola - Página Principal
# Versão 3.0 - Melhorada e Modularizada
# ============================================================

from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Importar módulos customizados
from config import *
from utils import *

# ------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Produção",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com paleta verde
st.markdown(f"""
    <style>
    /* Estilo geral */
    .main {{
        background-color: {PALETA_CORES['bg_light']};
    }}
    
    /* Cabeçalho */
    .header-container {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,104,56,0.2);
    }}
    
    .header-title {{
        color: white !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }}
    
    .header-subtitle {{
        color: white !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        opacity: 0.95;
    }}
    
    /* Seções */
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
    
    /* Botões */
    .stDownloadButton button {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s;
    }}
    
    .stDownloadButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,168,89,0.4);
    }}
    
    .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        color: white;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
    }}
    
    .stButton button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #004d2a 0%, {PALETA_CORES['primary']} 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,168,89,0.3);
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {PALETA_CORES['bg_sidebar']};
    }}
    
    /* Tabs */
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
        min-width: fit-content;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {PALETA_CORES['primary']} 0%, {PALETA_CORES['secondary']} 100%);
        color: white;
    }}
    
    .stTabs [data-baseweb="tab"] > div {{
        padding: 0 0.5rem;
    }}
    
    /* Métricas */
    [data-testid="stMetricValue"] {{
        color: {PALETA_CORES['primary']};
    }}
    
    [data-testid="stMetricDelta"] {{
        color: {PALETA_CORES['secondary']};
    }}
    
    /* Captions */
    .caption-text {{
        color: {PALETA_CORES['primary']};
        font-size: 0.875rem;
    }}
    
    /* Dividers */
    hr {{
        border-color: {PALETA_CORES['accent']};
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Cabeçalho principal
# ------------------------------------------------------------
st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🌾 Sistema de Produção Agrícola</h1>
        <p class="header-subtitle">Análise integrada de produção, locais e macro regiões de mercado</p>
    </div>
""", unsafe_allow_html=True)

# Breadcrumb
criar_breadcrumb("Produção")

# ------------------------------------------------------------
# Carregar dados
# ------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
ARQ_EXCEL = APP_DIR / "base" / "producao.xlsx"

if not ARQ_EXCEL.exists():
    st.error("❌ Arquivo não encontrado: `base/producao.xlsx`")
    logger.error(f"Arquivo não encontrado: {ARQ_EXCEL}")
    st.stop()

# Carregar com cache e validação
@st.cache_data(show_spinner=True)
def carregar_dados(caminho: Path) -> pd.DataFrame:
    return carregar_excel_com_validacao(caminho)

try:
    with st.spinner("⏳ Carregando dados..."):
        df_raw = carregar_dados(ARQ_EXCEL)
        df = df_raw.copy()
        
        # Validar qualidade
        qualidade = validar_qualidade_dados(df)
        
        # Mostrar alerta se houver problemas
        if qualidade["percentual_nulos"] > 10:
            st.warning(f"⚠️ Atenção: {qualidade['percentual_nulos']:.1f}% de valores nulos detectados!")
        
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    logger.error(f"Erro crítico: {str(e)}")
    st.stop()

# ------------------------------------------------------------
# Processamento inicial
# ------------------------------------------------------------

# 1) Filtrar valores vazios de prod_kg_ha_13_5
if "prod_kg_ha_13_5" in df.columns:
    df, linhas_removidas = filtrar_valores_vazios(df, "prod_kg_ha_13_5")
    
    if linhas_removidas > 0:
        st.info(f"ℹ️ Removidas {linhas_removidas:,} linhas com prod_kg_ha_13_5 vazio")

# 2) Processar datas e safra
df = processar_datas_safra(df)

# 3) Criar produtor_fazenda
df = criar_produtor_fazenda(df)

# ------------------------------------------------------------
# Tabela auxiliar de locais
# ------------------------------------------------------------
colunas_locais = ["estado_cod", "estado", "cidade", "produtor", "fazenda"]

if set(colunas_locais).issubset(df.columns):
    df_locais = df[colunas_locais].copy()
    df_locais["produtor_fazenda"] = (
        df_locais["produtor"].astype(str).str.upper().str.strip()
        + "_"
        + df_locais["fazenda"].astype(str).str.upper().str.strip()
    )
    df_locais = df_locais.drop_duplicates(subset=["produtor_fazenda"]).reset_index(drop=True)

    # cidade_cod3
    df_locais["cidade_base"] = df_locais["cidade"].astype(str).str.upper().str.strip().str[:3]
    df_locais["cidade_count"] = df_locais.groupby("cidade_base")["cidade_base"].transform("count")
    df_locais["cidade_seq"] = df_locais.groupby("cidade_base").cumcount() + 1
    df_locais["cidade_cod3"] = df_locais.apply(
        lambda r: r["cidade_base"] if r["cidade_count"] == 1 else f"{r['cidade_base']}_{r['cidade_seq']}",
        axis=1
    )
    df_locais = df_locais.drop(columns=["cidade_base", "cidade_count", "cidade_seq"])
else:
    df_locais = pd.DataFrame()

# ------------------------------------------------------------
# Macro MKT
# ------------------------------------------------------------
df_macro_base = pd.DataFrame(
    DADOS_MACRO_MKT,
    columns=["regional", "estado_cod", "macro_mkt", "flag_inserir"]
)

# ------------------------------------------------------------
# SIDEBAR — Controles
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Painel de Controle")
    st.markdown("---")
    
    # Botão de reset
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 Resetar Filtros", use_container_width=True, type="primary"):
            st.session_state.pop("macro_ctrl", None)
            st.session_state.pop("hibridos_ctrl", None)
            st.session_state.pop("colunas_ctrl", None)
            logger.info("🔄 Filtros resetados pelo usuário")
            st.rerun()
    
    st.markdown("---")

    # Macro MKT editor
    st.markdown("#### 🧭 Macro Regiões de Mercado")
    st.caption("Selecione as regiões ativas para análise")

    if "macro_ctrl" not in st.session_state:
        st.session_state["macro_ctrl"] = df_macro_base.copy()

    df_macro_ctrl = st.data_editor(
        st.session_state["macro_ctrl"],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "regional": st.column_config.TextColumn("Regional", width="medium"),
            "estado_cod": st.column_config.TextColumn("UF", width="small"),
            "macro_mkt": st.column_config.TextColumn("Macro MKT", width="medium"),
            "flag_inserir": st.column_config.CheckboxColumn("✓ Ativo", default=True)
        },
        hide_index=True
    )

    st.session_state["macro_ctrl"] = df_macro_ctrl
    
    st.markdown("---")
    
    # Botão para salvar configuração
    if st.button("💾 Salvar Configuração", use_container_width=True):
        config_salvar = {
            "macro_ctrl": df_macro_ctrl.to_dict(),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        if salvar_configuracao(config_salvar):
            st.success("✅ Configuração salva!")
        else:
            st.error("❌ Erro ao salvar configuração")

# Padronização e JOIN Macro
for col in ["regional", "estado_cod"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.upper().str.strip()

for col in ["regional", "estado_cod", "macro_mkt"]:
    df_macro_ctrl[col] = df_macro_ctrl[col].astype(str).str.upper().str.strip()

df = df.merge(
    df_macro_ctrl[["regional", "estado_cod", "macro_mkt"]],
    on=["regional", "estado_cod"],
    how="left"
)

df["macro_mkt"] = (
    df["macro_mkt"]
    .astype(str).str.upper().str.strip()
    .replace("NAN", pd.NA)
)

macros_ativas = (
    df_macro_ctrl.query("flag_inserir == 1")["macro_mkt"]
    .dropna().unique().tolist()
)
df = df[df["macro_mkt"].isin(macros_ativas)].copy()

# JOIN cidade_cod3
if not df_locais.empty and "produtor_fazenda" in df.columns:
    df = df.merge(
        df_locais[["produtor_fazenda", "cidade_cod3"]],
        on="produtor_fazenda",
        how="left"
    )

# ------------------------------------------------------------
# Híbridos
# ------------------------------------------------------------
if "hibrido" in df.columns:
    lista_hibridos = (
        df["hibrido"].astype(str).str.strip()
        .replace("nan", pd.NA).dropna()
        .drop_duplicates().sort_values()
        .tolist()
    )
else:
    lista_hibridos = []

df_hibridos_base = pd.DataFrame({"hibrido": lista_hibridos, "flag_inserir": 1})

if "hibridos_ctrl" in st.session_state:
    antigo = st.session_state["hibridos_ctrl"].copy()
    if "flag_inserir" not in antigo.columns:
        antigo["flag_inserir"] = 1
    df_hibridos_base = df_hibridos_base.merge(
        antigo[["hibrido", "flag_inserir"]],
        on="hibrido",
        how="left",
        suffixes=("", "_old")
    )
    df_hibridos_base["flag_inserir"] = df_hibridos_base["flag_inserir_old"].fillna(1).astype(int)
    df_hibridos_base = df_hibridos_base.drop(columns=["flag_inserir_old"])

st.session_state["hibridos_ctrl"] = df_hibridos_base.copy()

with st.sidebar:
    st.markdown("---")
    st.markdown("#### 🧬 Híbridos")
    st.caption("Selecione os híbridos para análise")

    df_hibridos_ctrl = st.data_editor(
        st.session_state["hibridos_ctrl"],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "hibrido": st.column_config.TextColumn("Híbrido", width="medium"),
            "flag_inserir": st.column_config.CheckboxColumn("✓ Ativo", default=True)
        },
        hide_index=True
    )
    st.session_state["hibridos_ctrl"] = df_hibridos_ctrl

# Aplicar filtro de híbridos
if "hibrido" in df.columns and not df_hibridos_ctrl.empty:
    hibridos_ativos = df_hibridos_ctrl.query("flag_inserir == 1")["hibrido"].tolist()
    df_filtrado = df[df["hibrido"].astype(str).str.strip().isin(hibridos_ativos)].copy()
else:
    df_filtrado = df.copy()

# ------------------------------------------------------------
# Colunas
# ------------------------------------------------------------
df_colunas_base = pd.DataFrame(COLUNAS_BASE, columns=["nome_coluna", "flag_inserir", "ordem"])

if "colunas_ctrl" in st.session_state:
    antigo = st.session_state["colunas_ctrl"].copy()
    if "flag_inserir" not in antigo.columns:
        antigo["flag_inserir"] = 1
    if "ordem" not in antigo.columns:
        antigo["ordem"] = range(1, len(antigo) + 1)
    df_colunas_base = df_colunas_base.merge(
        antigo[["nome_coluna", "flag_inserir", "ordem"]],
        on="nome_coluna",
        how="left",
        suffixes=("", "_old")
    )
    df_colunas_base["flag_inserir"] = df_colunas_base["flag_inserir_old"].fillna(df_colunas_base["flag_inserir"]).astype(int)
    df_colunas_base["ordem"] = df_colunas_base["ordem_old"].fillna(df_colunas_base["ordem"]).astype(int)
    df_colunas_base = df_colunas_base.drop(columns=["flag_inserir_old", "ordem_old"])

st.session_state["colunas_ctrl"] = df_colunas_base.copy()

with st.sidebar:
    st.markdown("---")
    st.markdown("#### ⚙️ Configuração de Colunas")
    st.caption("Personalize as colunas e sua ordem de exibição")

    df_colunas_ctrl = st.data_editor(
        st.session_state["colunas_ctrl"],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "nome_coluna": st.column_config.TextColumn("Coluna", width="medium"),
            "flag_inserir": st.column_config.CheckboxColumn("✓ Exibir", default=True),
            "ordem": st.column_config.NumberColumn("Ordem", min_value=1, step=1, width="small"),
        },
        hide_index=True
    )
    st.session_state["colunas_ctrl"] = df_colunas_ctrl

# Processar colunas ativas
df_ctrl_valid = df_colunas_ctrl.copy()
df_ctrl_valid["ordem"] = pd.to_numeric(df_ctrl_valid["ordem"], errors="coerce")
max_ordem = int(df_ctrl_valid["ordem"].max()) if df_ctrl_valid["ordem"].notna().any() else 0
df_ctrl_valid["ordem"] = df_ctrl_valid["ordem"].fillna(max_ordem + 999).astype(int)

colunas_ativas = (
    df_ctrl_valid
    .query("flag_inserir == 1")
    .sort_values("ordem")
    ["nome_coluna"]
    .tolist()
)

colunas_ativas = [c for c in colunas_ativas if c in df_filtrado.columns]

df_final = df_filtrado[colunas_ativas].copy()
st.session_state["df_final"] = df_final
st.session_state["df_raw"] = df_raw
st.session_state["df_filtrado"] = df_filtrado

logger.info(f"✅ df_final salvo no session_state: {len(df_final)} registros")

# ------------------------------------------------------------
# FILTROS RÁPIDOS
# ------------------------------------------------------------
st.markdown("### 🔍 Filtros Rápidos")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if "safra" in df_filtrado.columns:
        safras_disponiveis = sorted(df_filtrado["safra"].dropna().unique())
        safra_selecionada = st.multiselect(
            "Safra",
            options=safras_disponiveis,
            default=safras_disponiveis,
            key="filtro_safra"
        )
        if safra_selecionada:
            df_filtrado = df_filtrado[df_filtrado["safra"].isin(safra_selecionada)]

with col2:
    if "estado_cod" in df_filtrado.columns:
        estados = sorted(df_filtrado["estado_cod"].dropna().unique())
        estado_selecionado = st.multiselect(
            "Estado",
            options=estados,
            default=estados,
            key="filtro_estado"
        )
        if estado_selecionado:
            df_filtrado = df_filtrado[df_filtrado["estado_cod"].isin(estado_selecionado)]

with col3:
    if "prod_sc_ha_13_5" in df_filtrado.columns:
        prod_min = st.number_input(
            "Produtividade Mínima (sc/ha)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="filtro_prod_min"
        )
        if prod_min > 0:
            df_filtrado = df_filtrado[df_filtrado["prod_sc_ha_13_5"] >= prod_min]

with col4:
    busca = st.text_input("🔎 Buscar", placeholder="Digite para buscar...", key="busca_texto")
    if busca:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

# Atualizar df_final com filtros rápidos
df_final = df_filtrado[colunas_ativas].copy()
st.session_state["df_final"] = df_final

st.markdown("---")

# ------------------------------------------------------------
# MÉTRICAS PRINCIPAIS
# ------------------------------------------------------------
st.markdown("### 📊 Indicadores Principais")
criar_metricas_principais(df_filtrado, df_raw, macros_ativas)

st.markdown("---")

# ------------------------------------------------------------
# GRÁFICOS DE RESUMO
# ------------------------------------------------------------
st.markdown("### 📈 Análise Visual")

col1, col2 = st.columns(2)

with col1:
    if "safra" in df_filtrado.columns and "prod_sc_ha_13_5" in df_filtrado.columns:
        fig = px.box(
            df_filtrado,
            x="safra",
            y="prod_sc_ha_13_5",
            title="Distribuição de Produtividade por Safra",
            color_discrete_sequence=[PALETA_CORES['primary']],
            labels={"prod_sc_ha_13_5": "Produtividade (sc/ha)", "safra": "Safra"}
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color=PALETA_CORES['text_dark'])
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "macro_mkt" in df_filtrado.columns:
        contagem = df_filtrado["macro_mkt"].value_counts().reset_index()
        contagem.columns = ["macro_mkt", "count"]
        
        fig = px.bar(
            contagem,
            x="macro_mkt",
            y="count",
            title="Registros por Macro MKT",
            color_discrete_sequence=[PALETA_CORES['secondary']],
            labels={"count": "Quantidade", "macro_mkt": "Macro MKT"}
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color=PALETA_CORES['text_dark']),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# TABELAS PRINCIPAIS
# ------------------------------------------------------------
st.markdown("""
    <div class="section-header">
        <h2 class="section-title">📊 Base de Dados Filtrada</h2>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"<p class='caption-text'>Visualizando {len(df_filtrado):,} registros após aplicação dos filtros</p>", unsafe_allow_html=True)

df_view = df_filtrado.copy()
if "plantio" in df_view.columns:
    df_view["plantio"] = pd.to_datetime(df_view["plantio"], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

# AgGrid
criar_aggrid(df_view, altura=AGGRID_OPTIONS["altura_principal"], colunas_texto=COLUNAS_TEXTO)

# Botões de download
st.markdown("### 💾 Exportar Dados")

col1, col2, col3 = st.columns(3)

with col1:
    st.download_button(
        label="📊 Excel (.xlsx)",
        data=df_para_excel_bytes(df_view),
        file_name="producao_base_filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    st.download_button(
        label="📄 CSV",
        data=df_para_csv_bytes(df_view),
        file_name="producao_base_filtrada.csv",
        mime="text/csv",
        use_container_width=True
    )

with col3:
    st.download_button(
        label="🔧 JSON",
        data=df_para_json_str(df_view),
        file_name="producao_base_filtrada.json",
        mime="application/json",
        use_container_width=True
    )

st.markdown("---")

# Base Final Personalizada
st.markdown("""
    <div class="section-header">
        <h2 class="section-title">📋 Base Final Personalizada</h2>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"<p class='caption-text'>Exibindo {len(colunas_ativas)} colunas selecionadas em ordem personalizada</p>", unsafe_allow_html=True)

criar_aggrid(df_final, altura=AGGRID_OPTIONS["altura_principal"], colunas_texto=COLUNAS_TEXTO)

col1, col2, col3 = st.columns(3)

with col1:
    st.download_button(
        label="📊 Excel (.xlsx)",
        data=df_para_excel_bytes(df_final),
        file_name="producao_df_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    st.download_button(
        label="📄 CSV",
        data=df_para_csv_bytes(df_final),
        file_name="producao_df_final.csv",
        mime="text/csv",
        use_container_width=True
    )

with col3:
    st.download_button(
        label="🔧 JSON",
        data=df_para_json_str(df_final),
        file_name="producao_df_final.json",
        mime="application/json",
        use_container_width=True
    )

st.markdown("---")

# ------------------------------------------------------------
# ESTATÍSTICAS DESCRITIVAS
# ------------------------------------------------------------
with st.expander("📊 Estatísticas Descritivas", expanded=False):
    colunas_numericas = df_final.select_dtypes(include=['number']).columns.tolist()
    
    if colunas_numericas:
        st.markdown("#### Resumo Estatístico")
        st.dataframe(
            df_final[colunas_numericas].describe().T.style.format("{:.2f}"),
            use_container_width=True
        )
        
        # Correlação
        if len(colunas_numericas) > 1:
            st.markdown("#### Matriz de Correlação")
            corr_matrix = df_final[colunas_numericas].corr()
            
            fig = px.imshow(
                corr_matrix,
                text_auto='.2f',
                aspect="auto",
                color_continuous_scale="RdYlGn",
                title="Correlação entre Variáveis Numéricas"
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=PALETA_CORES['text_dark'])
            )
            st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# COMPARAÇÃO COM BASE NÃO FILTRADA
# ------------------------------------------------------------
if st.checkbox("📊 Comparar com base não filtrada"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔹 Dados Filtrados")
        st.metric("Registros", f"{len(df_filtrado):,}")
        if "prod_sc_ha_13_5" in df_filtrado.columns:
            st.metric("Média Produtividade", f"{df_filtrado['prod_sc_ha_13_5'].mean():.1f} sc/ha")
            st.metric("Mediana Produtividade", f"{df_filtrado['prod_sc_ha_13_5'].median():.1f} sc/ha")
    
    with col2:
        st.markdown("#### 🔹 Dados Originais")
        st.metric("Registros", f"{len(df_raw):,}")
        if "prod_sc_ha_13_5" in df_raw.columns:
            st.metric("Média Produtividade", f"{df_raw['prod_sc_ha_13_5'].mean():.1f} sc/ha")
            st.metric("Mediana Produtividade", f"{df_raw['prod_sc_ha_13_5'].median():.1f} sc/ha")

st.markdown("---")

# ------------------------------------------------------------
# TABELAS AUXILIARES EM TABS
# ------------------------------------------------------------
st.markdown("""
    <div class="section-header">
        <h2 class="section-title">📚 Dados Auxiliares e Configurações</h2>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "  📍  Locais  ",
    "  🧭  Macro MKT  ",
    "  🧬  Híbridos  ",
    "  ⚙️  Colunas  "
])

with tab1:
    st.markdown("#### Tabela de Locais Consolidada")
    if not df_locais.empty:
        criar_aggrid(df_locais, altura=AGGRID_OPTIONS["altura_auxiliar"], colunas_texto=COLUNAS_TEXTO)
        st.markdown(f"<p class='caption-text'>Total de {len(df_locais)} locais únicos cadastrados</p>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ Tabela auxiliar de locais não disponível.")

with tab2:
    st.markdown("#### Configuração de Macro Regiões de Mercado")
    criar_aggrid(df_macro_ctrl, altura=AGGRID_OPTIONS["altura_auxiliar"], colunas_texto=COLUNAS_TEXTO)
    ativos = df_macro_ctrl['flag_inserir'].sum()
    total = len(df_macro_ctrl)
    st.markdown(f"<p class='caption-text'>✅ {ativos} regiões ativas de {total} cadastradas</p>", unsafe_allow_html=True)

with tab3:
    st.markdown("#### Configuração de Híbridos")
    criar_aggrid(df_hibridos_ctrl, altura=AGGRID_OPTIONS["altura_auxiliar"], colunas_texto=COLUNAS_TEXTO)
    ativos_h = df_hibridos_ctrl['flag_inserir'].sum()
    total_h = len(df_hibridos_ctrl)
    st.markdown(f"<p class='caption-text'>✅ {ativos_h} híbridos ativos de {total_h} cadastrados</p>", unsafe_allow_html=True)

with tab4:
    st.markdown("#### Configuração de Colunas e Ordenação")
    criar_aggrid(df_colunas_ctrl, altura=AGGRID_OPTIONS["altura_auxiliar"], colunas_texto=COLUNAS_TEXTO)
    ativos_c = df_colunas_ctrl['flag_inserir'].sum()
    total_c = len(df_colunas_ctrl)
    st.markdown(f"<p class='caption-text'>✅ {ativos_c} colunas visíveis de {total_c} disponíveis</p>", unsafe_allow_html=True)

# ------------------------------------------------------------
# Rodapé
# ------------------------------------------------------------
st.markdown("---")
st.markdown(f"""
    <div style='text-align: center; color: {PALETA_CORES['primary']}; padding: 2rem 0;'>
        <p style='font-weight: 600;'>Sistema de Produção Agrícola | Versão 3.0</p>
        <p style='font-size: 0.875rem; color: {PALETA_CORES['secondary']};'>Desenvolvido com 🌱 usando Streamlit</p>
    </div>
""", unsafe_allow_html=True)