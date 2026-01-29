# utils.py
# ============================================================
# Funções Auxiliares e Utilitárias
# ============================================================

from pathlib import Path
from io import BytesIO
import pandas as pd
import streamlit as st
import logging
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTES - COLUNAS NUMÉRICAS
# ============================================================
COLUNAS_NUMERICAS_FORCADAS = [
    'prod_kg_ha_13_5',
    'prod_sc_ha_13_5',
    'pop_plts_ha',
    'aie_mts',
    'lat_mts',
    'pmg_gr_13_5',
    'num_fil',
    'num_graos_fil'
]

# ============================================================
# FUNÇÕES DE CARREGAMENTO E VALIDAÇÃO
# ============================================================

def converter_colunas_numericas(df: pd.DataFrame, colunas: list = None) -> pd.DataFrame:
    """
    Converte colunas especificadas para tipo numérico.
    
    Args:
        df: DataFrame a ser convertido
        colunas: Lista de colunas para converter (usa COLUNAS_NUMERICAS_FORCADAS se None)
    
    Returns:
        DataFrame com colunas convertidas
    """
    if colunas is None:
        colunas = COLUNAS_NUMERICAS_FORCADAS
    
    df_conv = df.copy()
    colunas_convertidas = []
    
    for col in colunas:
        if col in df_conv.columns:
            # Tentar converter para numérico
            df_conv[col] = pd.to_numeric(df_conv[col], errors='coerce')
            colunas_convertidas.append(col)
    
    if colunas_convertidas:
        logger.info(f"🔢 Colunas convertidas para numérico: {colunas_convertidas}")
    
    return df_conv


def carregar_excel_com_validacao(caminho: Path) -> pd.DataFrame:
    """
    Carrega arquivo Excel com validação, logging e conversão de colunas numéricas
    """
    try:
        logger.info(f"Iniciando carregamento de: {caminho}")
        df = pd.read_excel(caminho)
        logger.info(f"✅ Dados carregados: {len(df):,} registros, {len(df.columns)} colunas")
        
        # Converter colunas numéricas automaticamente
        df = converter_colunas_numericas(df)
        
        return df
    except FileNotFoundError:
        logger.error(f"❌ Arquivo não encontrado: {caminho}")
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados: {str(e)}")
        raise


def validar_qualidade_dados(df: pd.DataFrame) -> dict:
    """
    Retorna estatísticas de qualidade dos dados
    """
    total_valores = df.size
    valores_nulos = df.isnull().sum().sum()
    
    qualidade = {
        "total_registros": len(df),
        "total_colunas": len(df.columns),
        "valores_nulos": valores_nulos,
        "percentual_nulos": (valores_nulos / total_valores * 100) if total_valores > 0 else 0,
        "duplicatas": df.duplicated().sum(),
        "colunas_vazias": [col for col in df.columns if df[col].isnull().all()],
        "completude": ((total_valores - valores_nulos) / total_valores * 100) if total_valores > 0 else 0
    }
    
    logger.info(f"Qualidade dos dados: {qualidade['completude']:.2f}% de completude")
    return qualidade

# ============================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================

def processar_datas_safra(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa coluna de plantio e cria coluna safra
    """
    if "plantio" in df.columns:
        df["plantio"] = pd.to_datetime(df["plantio"], errors="coerce", dayfirst=True)
        df["safra"] = df["plantio"].dt.year
        logger.info("✅ Datas processadas e safra criada")
    return df


def criar_produtor_fazenda(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria coluna produtor_fazenda concatenada
    """
    if {"produtor", "fazenda"}.issubset(df.columns):
        df["produtor_fazenda"] = (
            df["produtor"].astype(str).str.upper().str.strip()
            + "_"
            + df["fazenda"].astype(str).str.upper().str.strip()
        )
        logger.info("✅ Coluna produtor_fazenda criada")
    return df


def filtrar_valores_vazios(df: pd.DataFrame, coluna: str) -> tuple:
    """
    Remove linhas com valores vazios em uma coluna específica
    Retorna: (df_filtrado, qtd_removidas)
    """
    antes = len(df)
    df = df[df[coluna].notna()].copy()
    df = df[df[coluna] != ""].copy()
    depois = len(df)
    removidas = antes - depois
    
    if removidas > 0:
        logger.info(f"🗑️ Removidas {removidas:,} linhas com {coluna} vazio")
    
    return df, removidas

# ============================================================
# FUNÇÕES DE VISUALIZAÇÃO (AGGRID)
# ============================================================

def criar_aggrid(df: pd.DataFrame, altura: int = 400, colunas_texto: list = None) -> object:
    """
    Cria um AgGrid configurado com todas as funcionalidades
    """
    if colunas_texto is None:
        colunas_texto = ["safra"]
    
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurações padrão
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='sum',
        enableValue=True,
        enablePivot=True,
        wrapText=False,
        autoHeight=False
    )
    
    # Formatar colunas
    for col in df.columns:
        if col.lower() in [c.lower() for c in colunas_texto]:
            gb.configure_column(col, type=["textColumn"])
        elif pd.api.types.is_numeric_dtype(df[col]):
            gb.configure_column(
                col,
                type=["numericColumn"],
                precision=1,
                valueFormatter=JsCode("""
                    function(params) {
                        if (params.value == null) return '';
                        return params.value.toLocaleString('pt-BR', {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1
                        });
                    }
                """)
            )
    
    # Configurações adicionais
    gb.configure_selection(
        selection_mode='multiple',
        use_checkbox=False,
        groupSelectsChildren=True,
        groupSelectsFiltered=True
    )
    
    gb.configure_side_bar(
        filters_panel=True,
        columns_panel=True,
        defaultToolPanel=""
    )
    
    gb.configure_pagination(enabled=False)
    
    gb.configure_grid_options(
        domLayout='normal',
        enableRangeSelection=True,
        enableCharts=True,
        enableRangeHandle=True,
        suppressMenuHide=False,
        enableCellTextSelection=True,
        ensureDomOrder=True,
        animateRows=True,
        suppressColumnVirtualisation=False,
        suppressRowVirtualisation=False,
        suppressRowClickSelection=False,
        onGridReady=JsCode("""
            function(params) {
                params.api.sizeColumnsToFit();
            }
        """)
    )
    
    gridOptions = gb.build()
    
    return AgGrid(
        df,
        gridOptions=gridOptions,
        height=altura,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=True,
        theme='balham',
        allow_unsafe_jscode=True,
        reload_data=False,
        custom_css={
            "#gridToolBar": {
                "padding-bottom": "0px !important",
            }
        }
    )

# ============================================================
# FUNÇÕES DE EXPORTAÇÃO
# ============================================================

def df_para_excel_bytes(df_export: pd.DataFrame) -> bytes:
    """
    Converte DataFrame para bytes do Excel
    """
    buffer = BytesIO()
    df_tmp = df_export.copy()

    for col in df_tmp.select_dtypes(include=["datetime", "datetimetz"]).columns:
        df_tmp[col] = pd.to_datetime(df_tmp[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

    if "plantio" in df_tmp.columns:
        df_tmp["plantio"] = pd.to_datetime(df_tmp["plantio"], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_tmp.to_excel(writer, index=False, sheet_name="dados")

    buffer.seek(0)
    logger.info(f"📊 Excel gerado: {len(df_export)} registros")
    return buffer.read()


def df_para_csv_bytes(df_export: pd.DataFrame) -> bytes:
    """
    Converte DataFrame para bytes do CSV
    """
    csv = df_export.to_csv(index=False).encode('utf-8')
    logger.info(f"📄 CSV gerado: {len(df_export)} registros")
    return csv


def df_para_json_str(df_export: pd.DataFrame) -> str:
    """
    Converte DataFrame para string JSON
    """
    json_str = df_export.to_json(orient='records', indent=2, force_ascii=False)
    logger.info(f"🔧 JSON gerado: {len(df_export)} registros")
    return json_str

# ============================================================
# FUNÇÕES DE CONFIGURAÇÃO
# ============================================================

def salvar_configuracao(config_dict: dict, caminho: str = "config_producao.json") -> bool:
    """
    Salva configurações em arquivo JSON
    """
    try:
        # Adicionar timestamp
        config_dict["timestamp"] = datetime.now().isoformat()
        
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Configuração salva em: {caminho}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configuração: {str(e)}")
        return False


def carregar_configuracao(caminho: str = "config_producao.json") -> dict:
    """
    Carrega configurações de arquivo JSON
    """
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info(f"📂 Configuração carregada de: {caminho}")
        return config
    except FileNotFoundError:
        logger.warning(f"⚠️ Arquivo de configuração não encontrado: {caminho}")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {str(e)}")
        return {}

# ============================================================
# FUNÇÕES DE INTERFACE
# ============================================================

def criar_metricas_principais(df_filtrado: pd.DataFrame, df_raw: pd.DataFrame, 
                              macros_ativas: list) -> None:
    """
    Cria os cards de métricas principais
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_registros = len(df_filtrado)
        st.metric(
            label="📝 Total de Registros",
            value=f"{total_registros:,}",
            delta=f"{len(df_raw) - total_registros} filtrados"
        )

    with col2:
        total_hibridos = df_filtrado["hibrido"].nunique() if "hibrido" in df_filtrado.columns else 0
        st.metric(
            label="🧬 Híbridos Ativos",
            value=total_hibridos
        )

    with col3:
        total_macros = len(macros_ativas)
        st.metric(
            label="🧭 Macro MKT",
            value=total_macros
        )

    with col4:
        total_safras = df_filtrado["safra"].nunique() if "safra" in df_filtrado.columns else 0
        st.metric(
            label="🌾 Safras",
            value=total_safras
        )


def criar_breadcrumb(pagina_atual: str = "Produção") -> None:
    """
    Cria breadcrumb de navegação
    """
    st.markdown(f"""
        <div style='background: white; padding: 0.5rem 1rem; border-radius: 6px; margin-bottom: 1rem;'>
            <span style='color: #006838;'>🏠 Home</span>
            <span style='color: #ccc;'> / </span>
            <span style='color: #00a859; font-weight: 600;'>{pagina_atual}</span>
        </div>
    """, unsafe_allow_html=True)