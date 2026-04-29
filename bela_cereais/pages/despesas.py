import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.formatters import secao, br

CATEGORIAS = {
    "FINANCEIROS":   ["JUROS EMPRESTIMOS","JUROS S/ MUTUO SOCIO","IOF","TARIFA BANCARIA"],
    "IMPOSTOS":      ["CSLL","ICMS S/ FRETE","IRPF","IRPJ","OUTROS IMPOSTOS E TAXAS","PARCELAMENTO SEFAZ"],
    "PESSOAL":       ["INSS","PRO-LABORE","HONORARIO CONTABEL","HONORARIOS DIVERSOS"],
    "LOGÍSTICA":     ["FRETE MARITIMO","FRETES/ENCOMENDAS","PEDAGIO","SEGURO CARGA","SEGURO DE CREDITO"],
    "OPERACIONAL":   ["AGUA","ALUGUEL","COMBUSTIVEL","ENERGIA","HOSPEDAGEM","INFORMATICA",
                      "INSTALACAO/MONTAGEM ESCRITORIO","INTERNET","MANUTENCAO VEICULOS",
                      "MATERIAL BENS/CONSUMO","REFEICOES/ALIMENTACAO","SISTEMA GERENTE MAX",
                      "TELEFONE MOVEL","CERTIFICADO","CONSULTORIA DE NEGOCIOS INTERNACIONAIS"],
}

CORES_CAT = {
    "FINANCEIROS":  "#E74C3C", "IMPOSTOS": "#F59E0B", "PESSOAL": "#8B5CF6",
    "LOGÍSTICA": "#3B82F6", "OPERACIONAL": "#2ECC71", "OUTROS": "#6B7080",
}

def categorizar(item: str) -> str:
    item_up = str(item).upper()
    for cat, itens in CATEGORIAS.items():
        if item_up in itens: return cat
    return "OUTROS"

def estilizar_grafico(fig, titulo="", height=380, showlegend=True, invert_y=False):
    fig.update_layout(
        title=titulo, height=height, showlegend=showlegend,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Montserrat", color="#C8CAD4", size=12),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2A2D38", borderwidth=1)
    )
    if len(fig.data) > 0 and fig.data[0].type != 'pie':
        fig.update_xaxes(gridcolor="#1E2029", linecolor="#2A2D38", tickfont=dict(size=11))
        fig.update_yaxes(gridcolor="#1E2029", linecolor="#2A2D38", tickfont=dict(size=11))
        if invert_y:
            fig.update_yaxes(autorange="reversed")
    return fig

def render(df_df: pd.DataFrame):
    secao("Análise de Despesas Administrativas", "Plano de contas detalhado com categorização automática")

    if df_df.empty or 'Item' not in df_df.columns or 'Valor' not in df_df.columns:
        st.info("Dados de despesas não disponíveis.")
        return

    df = df_df.copy()
    df['Categoria'] = df['Item'].apply(categorizar)
    total_geral = df['Valor'].sum()

    df_cat = df.groupby('Categoria')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
    maior_cat = df_cat.iloc[0] if not df_cat.empty else None

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="background:#16181F;border:1px solid #2A2D38;border-left:4px solid #E74C3C; border-radius:12px;padding:18px">
            <div style="font-size:11px;color:#6B7080;text-transform:uppercase;font-weight:600">Total Despesas</div>
            <div style="font-size:22px;font-weight:700;color:#E74C3C;font-family:'Montserrat',sans-serif">{br(total_geral)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:#16181F;border:1px solid #2A2D38;border-left:4px solid #F59E0B; border-radius:12px;padding:18px">
            <div style="font-size:11px;color:#6B7080;text-transform:uppercase;font-weight:600">Itens de Custo</div>
            <div style="font-size:22px;font-weight:700;color:#F59E0B;font-family:'Montserrat',sans-serif">{df['Item'].nunique()}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        if maior_cat is not None:
            pct = maior_cat['Valor'] / total_geral * 100 if total_geral else 0
            st.markdown(f"""
            <div style="background:#16181F;border:1px solid #2A2D38;border-left:4px solid #8B5CF6; border-radius:12px;padding:18px">
                <div style="font-size:11px;color:#6B7080;text-transform:uppercase;font-weight:600">Maior Categoria</div>
                <div style="font-size:16px;font-weight:700;color:#8B5CF6;font-family:'Montserrat',sans-serif">{maior_cat['Categoria']}</div>
                <div style="font-size:12px;color:#6B7080">{br(maior_cat['Valor'])} ({pct:.1f}%)</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        cores = [CORES_CAT.get(c, "#6B7080") for c in df_cat['Categoria']]
        fig = go.Figure(go.Pie(
            labels=df_cat['Categoria'], values=df_cat['Valor'],
            marker=dict(colors=cores, line=dict(color="#0F1117", width=2)),
            hole=0.45, textfont=dict(size=12, family="Montserrat"),
        ))
        estilizar_grafico(fig, titulo="Despesas por Categoria", height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        df_top = df.groupby('Item')['Valor'].sum().nlargest(10).reset_index()
        cores2 = [CORES_CAT.get(categorizar(r['Item']), "#6B7080") for _, r in df_top.iterrows()]
        fig2 = go.Figure(go.Bar(
            x=df_top['Valor'], y=df_top['Item'], orientation="h", marker_color=cores2,
            text=[f"R$ {v:,.0f}".replace(",",".") for v in df_top['Valor']], textposition="outside",
        ))
        estilizar_grafico(fig2, titulo="Top 10 Itens de Custo", height=360, showlegend=False, invert_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    secao("Detalhamento por Categoria")
    for cat in df_cat['Categoria']:
        df_c = df[df['Categoria'] == cat].groupby('Item')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
        total_c = df_c['Valor'].sum()
        pct_c = total_c / total_geral * 100 if total_geral else 0
        with st.expander(f"**{cat}** —  {br(total_c)}  ({pct_c:.1f}%)"):
            df_c['% do Total'] = (df_c['Valor'] / total_geral * 100).round(1)
            df_c['% da Categoria'] = (df_c['Valor'] / total_c * 100).round(1)
            st.dataframe(df_c, column_config={
                "Item": st.column_config.TextColumn("📌 Item"),
                "Valor": st.column_config.NumberColumn("💸 Valor", format="R$ %.2f"),
                "% do Total": st.column_config.ProgressColumn("% do Total", format="%.1f%%", min_value=0, max_value=100),
                "% da Categoria": st.column_config.ProgressColumn("% da Categ.", format="%.1f%%", min_value=0, max_value=100),
            }, hide_index=True, use_container_width=True)