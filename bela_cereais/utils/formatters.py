import streamlit as st

# ── Formatadores numéricos ──────────────────────────────────────────────────
def br(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def br_mil(valor: float) -> str:
    if abs(valor) >= 1_000_000:
        return f"R$ {valor/1_000_000:,.2f} M".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(valor) >= 1_000:
        return f"R$ {valor/1_000:,.1f} K".replace(",", "X").replace(".", ",").replace("X", ".")
    return br(valor)

def kg_fmt(valor: float) -> str:
    if valor >= 1_000_000:
        return f"{valor/1_000_000:,.2f} M kg".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{valor:,.0f} kg".replace(",", "X").replace(".", ",").replace("X", ".")

def pct_fmt(valor: float) -> str:
    return f"{valor:.1f}%".replace(".", ",")

def sinal(valor: float) -> str:
    return "▲" if valor >= 0 else "▼"

# ── CSS Global ────────────────────────────────────────────────────────────────
def injetar_css():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
    /* Reset e base */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
    }

    /* Fundo geral */
    .stApp {
        background: #0F1117;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #16181F !important;
        border-right: 1px solid #2A2D38 !important;
    }
    [data-testid="stSidebar"] * {
        color: #C8CAD4 !important;
    }
    [data-testid="stSidebar"] .stCheckbox label p,
    [data-testid="stSidebar"] h3 {
        color: #8B8FA8 !important;
        font-size: 13px !important;
    }

    /* Títulos */
    h1 { font-family: 'Syne', sans-serif !important; color: #FFFFFF !important; font-size: 28px !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h2 { font-family: 'Syne', sans-serif !important; color: #FFFFFF !important; font-weight: 700 !important; }
    h3, h4 { font-family: 'Syne', sans-serif !important; color: #E0E2EB !important; font-weight: 600 !important; }

    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #2A2D38 !important;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background: transparent !important;
        border: none !important;
        color: #6B7080 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #F29124 !important;
        border-bottom: 2px solid #F29124 !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px !important;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    .dvn-scroller { background: #16181F !important; }

    /* Métricas nativas (fallback) */
    [data-testid="stMetric"] {
        background: #16181F !important;
        border: 1px solid #2A2D38 !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] { color: #F29124 !important; font-size: 20px !important; }
    [data-testid="stMetricLabel"] { color: #8B8FA8 !important; font-size: 12px !important; }

    /* Selectbox / multiselect */
    .stSelectbox > div, .stMultiSelect > div {
        background: #1E2029 !important;
        border-color: #2A2D38 !important;
        border-radius: 8px !important;
    }

    /* Dividers */
    hr { border-color: #2A2D38 !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0F1117; }
    ::-webkit-scrollbar-thumb { background: #2A2D38; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #F29124; }
    </style>
    """, unsafe_allow_html=True)


# ── Card KPI ──────────────────────────────────────────────────────────────────
def card_kpi(titulo: str, valor: str, subtitulo: str = "",
             cor: str = "#F29124", icone: str = "",
             alerta: bool = False, positivo: bool = True):
    cor_borda = cor if not alerta else ("#2ECC71" if positivo else "#E74C3C")
    cor_valor = cor_borda
    bg_alerta = "rgba(231,76,60,0.06)" if (alerta and not positivo) else "rgba(46,204,113,0.06)" if (alerta and positivo) else "#16181F"

    st.markdown(f"""
    <div style="
        background:{bg_alerta};
        border:1px solid #2A2D38;
        border-left:4px solid {cor_borda};
        border-radius:12px;
        padding:18px 20px;
        margin-bottom:4px;
        transition:all .2s;
    ">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <span style="font-size:18px">{icone}</span>
            <span style="font-family:'DM Sans',sans-serif;font-size:11px;font-weight:600;
                         color:#6B7080;text-transform:uppercase;letter-spacing:1px">{titulo}</span>
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;
                    color:{cor_valor};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
            {valor}
        </div>
        {"" if not subtitulo else f'<div style="font-size:11px;color:#6B7080;margin-top:4px">{subtitulo}</div>'}
    </div>
    """, unsafe_allow_html=True)


# ── Card DRE linha ────────────────────────────────────────────────────────────
def dre_linha(descricao: str, valor: float, destaque: bool = False,
              negativo: bool = False, separador: bool = False):
    if separador:
        st.markdown('<hr style="border-color:#2A2D38;margin:4px 0">', unsafe_allow_html=True)
        return
    peso = "700" if destaque else "400"
    cor_txt = "#FFFFFF" if destaque else "#C8CAD4"
    cor_val = "#2ECC71" if (destaque and valor >= 0) else "#E74C3C" if (destaque and valor < 0) else ("#6B7080" if negativo else "#E0E2EB")
    bg = "rgba(242,145,36,0.05)" if destaque else "transparent"
    borda = "border-left:3px solid #F29124;" if destaque else ""
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:10px 16px;background:{bg};border-radius:8px;{borda}
                margin:2px 0">
        <span style="font-family:'DM Sans',sans-serif;font-size:14px;
                     font-weight:{peso};color:{cor_txt}">{descricao}</span>
        <span style="font-family:'Syne',sans-serif;font-size:15px;
                     font-weight:{peso};color:{cor_val}">{br(valor)}</span>
    </div>
    """, unsafe_allow_html=True)


# ── Seção título ──────────────────────────────────────────────────────────────
def secao(titulo: str, subtitulo: str = ""):
    sub_html = f'<p style="color:#6B7080;font-size:13px;margin:2px 0 0 0">{subtitulo}</p>' if subtitulo else ""
    st.markdown(f"""
    <div style="margin:24px 0 16px 0">
        <h3 style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;
                   color:#E0E2EB;margin:0">{titulo}</h3>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


# ── Badge status ──────────────────────────────────────────────────────────────
def badge(texto: str, tipo: str = "neutro") -> str:
    cores = {
        "positivo": ("#2ECC71", "rgba(46,204,113,0.12)"),
        "negativo": ("#E74C3C", "rgba(231,76,60,0.12)"),
        "alerta":   ("#F29124", "rgba(242,145,36,0.12)"),
        "neutro":   ("#8B8FA8", "rgba(139,143,168,0.12)"),
    }
    c, bg = cores.get(tipo, cores["neutro"])
    return f'<span style="background:{bg};color:{c};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600">{texto}</span>'
