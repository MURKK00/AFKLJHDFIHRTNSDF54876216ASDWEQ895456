import streamlit as st
import pandas as pd
from utils.formatters import secao, br, pct_fmt

def render(df_lf: pd.DataFrame):
    secao("Detalhamento de Contratos", "Todos os contratos do período selecionado")

    if df_lf.empty:
        st.info("Nenhum contrato encontrado para os filtros selecionados.")
        return

    # ── Filtro rápido por produto ─────────────────────────────────────────────
    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        if 'Produto' in df_lf.columns:
            produtos = ["Todos"] + sorted(df_lf['Produto'].dropna().unique().tolist())
            sel_prod = st.selectbox("🌱 Filtrar por Produto", produtos)
        else:
            sel_prod = "Todos"
    with col_f2:
        if 'Cliente' in df_lf.columns:
            clientes = ["Todos"] + sorted(df_lf['Cliente'].dropna().unique().tolist())
            sel_cli = st.selectbox("👤 Filtrar por Cliente", clientes)
        else:
            sel_cli = "Todos"

    df_view = df_lf.copy()
    if sel_prod != "Todos" and 'Produto' in df_view.columns:
        df_view = df_view[df_view['Produto'] == sel_prod]
    if sel_cli != "Todos" and 'Cliente' in df_view.columns:
        df_view = df_view[df_view['Cliente'] == sel_cli]

    st.markdown(f"<p style='color:#6B7080;font-size:13px'>{len(df_view)} contratos exibidos</p>", unsafe_allow_html=True)

    # ── Tabela principal ──────────────────────────────────────────────────────
    colunas_exib = {}
    mapa_cols = {
        "Contrato V":  ("📄 Contrato V",  st.column_config.TextColumn),
        "Contrato C":  ("📋 Contrato C",  st.column_config.TextColumn),
        "Fornecedor":  ("🏭 Fornecedor",  st.column_config.TextColumn),
        "Cliente":     ("👤 Cliente",     st.column_config.TextColumn),
        "Produto":     ("🌱 Produto",     st.column_config.TextColumn),
        "Empresa":     ("🏢 Empresa",     st.column_config.TextColumn),
        "Mês_Filtro":  ("📅 Mês",         st.column_config.TextColumn),
        "Peso Kg":     ("⚖️ Peso Kg",    lambda l: st.column_config.NumberColumn(l, format="%d")),
        "Sacas/Ton":   ("📦 Sacas/Ton",  lambda l: st.column_config.NumberColumn(l, format="%d")),
        "Lucro Bruto": ("💰 L. Bruto",   lambda l: st.column_config.NumberColumn(l, format="R$ %.2f")),
        "Total Frete": ("🚚 Frete",      lambda l: st.column_config.NumberColumn(l, format="R$ %.2f")),
        "Impostos":    ("🏛️ Impostos",   lambda l: st.column_config.NumberColumn(l, format="R$ %.2f")),
        "Comissão":    ("🤝 Comissão",   lambda l: st.column_config.NumberColumn(l, format="R$ %.2f")),
        "Lucro Líq.":  ("🎯 L. Líquido",lambda l: st.column_config.NumberColumn(l, format="R$ %.2f")),
    }

    for col_orig, (label, col_fn) in mapa_cols.items():
        if col_orig in df_view.columns:
            colunas_exib[col_orig] = col_fn(label)

    st.dataframe(df_view[[c for c in mapa_cols if c in df_view.columns]],
                 column_config=colunas_exib,
                 hide_index=True, use_container_width=True)

   # ── Resumo por fornecedor ─────────────────────────────────────────────────
    if 'Fornecedor' in df_view.columns and 'Lucro Líq.' in df_view.columns:
        st.markdown("<br>", unsafe_allow_html=True)
        secao("Resumo por Fornecedor (Ranking)")
        
        # ALTERAÇÃO 2: Criando o Ranking 
        df_forn = (df_view.groupby('Fornecedor')
                         .agg({'Lucro Bruto':'sum','Lucro Líq.':'sum','Peso Kg':'sum'})
                         .reset_index()
                         .sort_values('Lucro Líq.', ascending=False))
        
        # Insere a coluna de Posição/Rank no começo do dataframe
        df_forn.insert(0, 'Posição', range(1, len(df_forn) + 1))
        
        st.dataframe(df_forn, column_config={
            "Posição":     st.column_config.NumberColumn("🏆 Rank"),
            "Fornecedor":  st.column_config.TextColumn("🏭 Fornecedor"),
            "Lucro Bruto": st.column_config.NumberColumn("💰 L. Bruto",  format="R$ %.2f"),
            "Lucro Líq.":  st.column_config.NumberColumn("🎯 L. Líquido",format="R$ %.2f"),
            "Peso Kg":     st.column_config.NumberColumn("⚖️ Peso Kg",   format="%d"),
        }, hide_index=True, use_container_width=True)