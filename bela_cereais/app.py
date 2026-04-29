import streamlit as st
import sys, os, pandas as pd

st.set_page_config(page_title="Bela Cereais — Dashboard", page_icon="🌾",
                   layout="wide", initial_sidebar_state="expanded")

# --- ALTERAÇÃO 8: SISTEMA DE SENHA ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def verificar_senha():
    if st.session_state["senha_digitada"] == "bela2026": # Mude a senha aqui se desejar
        st.session_state["autenticado"] = True
    else:
        st.error("Senha incorreta!")

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 Acesso Restrito - Bela Cereais</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Digite a senha para acessar o dashboard:", type="password", key="senha_digitada", on_change=verificar_senha)
    st.stop() # Interrompe o carregamento se não estiver logado
# -------------------------------------

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader import carregar_dados, calcular_kpis

# --- ESTILIZAÇÃO COMPLETA ---
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');
html, body, [class*="css"], [class*="st-"] { font-family: 'Montserrat', sans-serif !important; }
span.material-icons, span.material-symbols-rounded, [data-testid="stIconMaterial"], .st-icon, i, svg {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}
[data-testid="stSidebarNav"] { display: none !important; }
h1 { color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important; letter-spacing: -0.5px; }
h2 { color: #FFFFFF !important; font-weight: 700 !important; }
h3, h4 { color: #E0E2EB !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #2A2D38 !important; gap: 8px; }
.stTabs [data-baseweb="tab-list"] button { background: transparent !important; border: none !important; color: #6B7080 !important; font-size: 14px !important; font-weight: 500 !important; padding: 10px 20px !important; border-radius: 0 !important; }
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color: #F29124 !important; border-bottom: 2px solid #F29124 !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }
[data-testid="stMetric"] { background: #16181F !important; border: 1px solid #2A2D38 !important; border-radius: 12px !important; padding: 16px !important; }
[data-testid="stMetricValue"] { color: #F29124 !important; font-size: 20px !important; }
[data-testid="stMetricLabel"] { color: #8B8FA8 !important; font-size: 12px !important; }
.stSelectbox > div, .stMultiSelect > div { background: #1E2029 !important; border-color: #2A2D38 !important; border-radius: 8px !important; }
hr { border-color: #2A2D38 !important; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

try:
    df_lucro, df_desp = carregar_dados('DASHBOARD.xlsx')
except FileNotFoundError:
    st.error("🚨 Arquivo `DASHBOARD.xlsx` não encontrado.")
    st.stop()

anos_disp = sorted(df_lucro['Ano'].unique().tolist()) if 'Ano' in df_lucro.columns else [2026]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌾 Bela Cereais")
    st.markdown("<hr style='border-color:#2A2D38;margin:10px 0'>", unsafe_allow_html=True)

    st.markdown("##### 📆 Ano")
    filtro_anos = st.multiselect("Anos", anos_disp, default=anos_disp, key="anos")
    if not filtro_anos: filtro_anos = anos_disp

    st.markdown("<hr style='border-color:#2A2D38;margin:10px 0'>", unsafe_allow_html=True)
    st.markdown("##### 🏢 Empresa")
    lista_emp = sorted(df_lucro['Empresa'].dropna().unique()) if 'Empresa' in df_lucro.columns else []
    todas_emp = st.checkbox("Todas", value=True, key="all_emp")
    filtro_emp = lista_emp if todas_emp else [e for e in lista_emp if st.checkbox(e, value=False, key=f"e_{e}")]

    st.markdown("<hr style='border-color:#2A2D38;margin:10px 0'>", unsafe_allow_html=True)
    st.markdown("##### 🌱 Produto")
    lista_prod = sorted(df_lucro['Produto'].dropna().unique()) if 'Produto' in df_lucro.columns else []
    todos_prod = st.checkbox("Todos", value=True, key="all_prod")
    filtro_prod = lista_prod if todos_prod else [p for p in lista_prod if st.checkbox(p, value=False, key=f"p_{p}")]

    st.markdown("<hr style='border-color:#2A2D38;margin:10px 0'>", unsafe_allow_html=True)
    st.markdown("##### 📅 Mês")
    lista_mes = sorted([m for m in df_lucro['Mês_Filtro'].dropna().unique() if m != 'Sem Data']) if 'Mês_Filtro' in df_lucro.columns else []
    todos_mes = st.checkbox("Todos", value=True, key="all_mes")
    filtro_mes = lista_mes if todos_mes else [m for m in lista_mes if st.checkbox(m, value=False, key=f"m_{m}")]

# ── Filtragem Principal ───────────────────────────────────────────────────────
def filtrar_l(df):
    m = pd.Series([True]*len(df), index=df.index)
    if 'Ano' in df.columns and filtro_anos:       m &= df['Ano'].isin(filtro_anos)
    if 'Empresa' in df.columns and filtro_emp:    m &= df['Empresa'].isin(filtro_emp)
    if 'Produto' in df.columns and filtro_prod:   m &= df['Produto'].isin(filtro_prod)
    if 'Mês_Filtro' in df.columns and filtro_mes: m &= df['Mês_Filtro'].isin(filtro_mes)
    return df[m].copy()

def filtrar_d(df):
    m = pd.Series([True]*len(df), index=df.index)
    if 'Ano' in df.columns and filtro_anos:       m &= df['Ano'].isin(filtro_anos)
    if 'Empresa' in df.columns and filtro_emp:    m &= df['Empresa'].isin(filtro_emp)
    if 'Mês_Filtro' in df.columns and filtro_mes: m &= df['Mês_Filtro'].isin(filtro_mes)
    return df[m].copy()

df_lf = filtrar_l(df_lucro)
df_df = filtrar_d(df_desp)
kpis  = calcular_kpis(df_lf, df_df)

# --- ALTERAÇÃO 4: Filtros especiais para a aba Comparativo (Ignora o ano para comparar 25 e 26, mas aplica a Empresa) ---
def filtrar_comp_l(df):
    m = pd.Series([True]*len(df), index=df.index)
    if 'Empresa' in df.columns and filtro_emp:    m &= df['Empresa'].isin(filtro_emp)
    if 'Produto' in df.columns and filtro_prod:   m &= df['Produto'].isin(filtro_prod)
    if 'Mês_Filtro' in df.columns and filtro_mes: m &= df['Mês_Filtro'].isin(filtro_mes)
    return df[m].copy()

def filtrar_comp_d(df):
    m = pd.Series([True]*len(df), index=df.index)
    if 'Empresa' in df.columns and filtro_emp:    m &= df['Empresa'].isin(filtro_emp)
    if 'Mês_Filtro' in df.columns and filtro_mes: m &= df['Mês_Filtro'].isin(filtro_mes)
    return df[m].copy()

df_comp_l = filtrar_comp_l(df_lucro)
df_comp_d = filtrar_comp_d(df_desp)
# -------------------------------------------------------------------------------------------------------------------------

# ── Header ────────────────────────────────────────────────────────────────────
anos_str = " & ".join(map(str, sorted(filtro_anos)))
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            margin-bottom:8px;padding-bottom:14px;border-bottom:1px solid #2A2D38">
  <div>
    <h1 style="margin:0">🌾 Dashboard Executivo</h1>
    <p style="color:#6B7080;font-size:13px;margin:4px 0 0 0;">
      Grupo Bela Cereais — Comercialização de Grãos · {anos_str}
    </p>
  </div>
</div>""", unsafe_allow_html=True)

# ── Abas ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 Dashboard","📋 DRE","📈 Gráficos","🔄 Comparativo","📦 Contratos","💸 Despesas"])

from pages.dashboard   import render as r_dash
from pages.dre         import render as r_dre
from pages.graficos    import render as r_graf
from pages.comparativo import render as r_comp
from pages.contratos   import render as r_cont
from pages.despesas    import render as r_desp

with tabs[0]: r_dash(df_lf, df_df, kpis)
with tabs[1]: r_dre(kpis)
with tabs[2]: r_graf(df_lf, df_df)
with tabs[3]: r_comp(df_comp_l, df_comp_d, kpis) 
with tabs[4]: r_cont(df_lf)
with tabs[5]: r_desp(df_df)