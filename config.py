# config.py
# ============================================================
# Configurações Centralizadas do Sistema
# ============================================================

# Paleta de Cores
PALETA_CORES = {
    "primary": "#006838",
    "secondary": "#00a859",
    "accent": "#72d8a8",
    "bg_light": "#f0f7f4",
    "bg_sidebar": "#e8f5ed",
    "success": "#c8e6d4",
    "warning": "#ffe8cc",
    "text_dark": "#004d2a",
    "text_medium": "#006838",
}

# Dados de Macro MKT
DADOS_MACRO_MKT = [
    ("Oeste - BA", "BA", "MAPITO", 1),
    ("Norte - MS", "MS", "MS", 1),
    ("Planalto Central - GO", "GO", "GO/MG", 1),
    ("Sudoeste - GO", "GO", "GO/MG", 1),
    ("Nordeste", "MA", "MAPITO", 1),
    ("Sul - MG", "MG", "GO/MG", 1),
    ("Sul - MS", "MS", "GO/MG", 1),
    ("BR 163 - MT", "MT", "BR-163 + PARECIS + SUL MT", 1),
    ("Parecis - MT", "MT", "BR-163 + PARECIS + SUL MT", 1),
    ("Sul - MT", "MT", "BR-163 + PARECIS + SUL MT", 1),
    ("Vale do Araguaia - MT", "MT", "VALE", 0),
    ("Norte - PR", "PR", "PR", 0),
]

# Configuração de Colunas Base
COLUNAS_BASE = [
    ("hibrido", 1, 1),
    ("prod_kg_ha_13_5", 0, 2),
    ("prod_sc_ha_13_5", 1, 3),
    ("macro_regiao", 1, 4),
    ("conjunta", 1, 5),
    ("sub_conjunta", 1, 6),
    ("micro_regiao", 1, 7),
    ("regional", 1, 8),
    ("estado_cod", 1, 9),
    ("estado", 1, 10),
    ("cidade", 1, 11),
    ("safra", 1, 12),
    ("macro_mkt", 1, 13),
    ("cidade_cod3", 1, 14),
]

# Configurações de AgGrid
AGGRID_OPTIONS = {
    "altura_principal": 400,
    "altura_auxiliar": 300,
    "theme": "balham",
}

# Colunas que não devem ter formatação numérica
COLUNAS_TEXTO = ["safra"]