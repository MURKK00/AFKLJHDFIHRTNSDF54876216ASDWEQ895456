import streamlit as st
import pandas as pd
from utils.formatters import card_kpi, secao, br_mil, pct_fmt, kg_fmt, br, badge

def render(df_lf: pd.DataFrame, df_df: pd.DataFrame, kpis: dict):
    k = kpis

    # ── Linha 1: KPIs de volume e receita ────────────────────────────────────
    secao("Indicadores Operacionais", "Resumo do período selecionado")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card_kpi("Contratos Fechados", str(k['n_contratos']),
                 icone="📄", cor="#F29124")
    with c2:
        card_kpi("Peso Total Negociado", kg_fmt(k['peso_total']),
                 icone="⚖️", cor="#F29124")
    with c3:
        card_kpi("Sacas / Toneladas", f"{k['sacas_total']:,.0f}".replace(",", "."),
                 icone="📦", cor="#F29124")
    with c4:
        card_kpi("Ticket Médio / Contrato", br_mil(k['ticket_medio']),
                 icone="🎫", cor="#8B5CF6")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Linha 2: KPIs financeiros ─────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        card_kpi("Lucro Bruto", br_mil(k['receita_bruta']),
                 subtitulo="Total dos contratos",
                 icone="💰", cor="#F29124")
    with c6:
        card_kpi("Lucro Líq. Operacional", br_mil(k['lucro_operacional']),
                 subtitulo=f"Margem op.: {pct_fmt(k['margem_op'])}",
                 icone="⚙️",
                 cor="#2ECC71" if k['lucro_operacional'] >= 0 else "#E74C3C",
                 alerta=True, positivo=k['lucro_operacional'] >= 0)
    with c7:
        card_kpi("Desp. Administrativas", br_mil(k['despesas_admin']),
                 subtitulo=f"{pct_fmt(k['indice_desp'])} da receita bruta",
                 icone="📉",
                 cor="#E74C3C" if k['indice_desp'] > 80 else "#F29124",
                 alerta=k['indice_desp'] > 80, positivo=False)
    with c8:
        pos = k['lucro_liquido_final'] >= 0
        card_kpi("Lucro Líquido Final", br_mil(k['lucro_liquido_final']),
                 subtitulo=f"Margem líq.: {pct_fmt(k['margem_liq'])}",
                 icone="🏆" if pos else "🚨",
                 cor="#2ECC71" if pos else "#E74C3C",
                 alerta=True, positivo=pos)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Linha 3: indicadores de eficiência ────────────────────────────────────
    c9, c10, c11, c12 = st.columns(4)
    with c9:
        card_kpi("Lucro por Saca/Ton", br(k['lucro_por_saca']),
                 subtitulo="Eficiência por unidade",
                 icone="📐", cor="#3B82F6")
    with c10:
        card_kpi("Margem Bruta", pct_fmt(k['margem_bruta']),
                 icone="📊", cor="#8B5CF6")
    with c11:
        card_kpi("Margem Operacional", pct_fmt(k['margem_op']),
                 icone="📈",
                 cor="#2ECC71" if k['margem_op'] >= 0 else "#E74C3C")
    with c12:
        cor_idx = "#E74C3C" if k['indice_desp'] > 80 else "#F59E0B" if k['indice_desp'] > 60 else "#2ECC71"
        card_kpi("Índice Desp./Receita", pct_fmt(k['indice_desp']),
                 subtitulo="⚠️ Crítico se > 80%" if k['indice_desp'] > 80 else "Saudável se < 60%",
                 icone="🎚️", cor=cor_idx)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabela por produto ────────────────────────────────────────────────────
    secao("Resultados por Produto / Commodity")
    if not df_lf.empty and 'Produto' in df_lf.columns:
        cols_agg = {c: 'sum' for c in ['Peso Kg','Sacas/Ton','Lucro Bruto','Total Frete','Impostos','Comissão','Lucro Líq.'] if c in df_lf.columns}
        df_prod = df_lf.groupby('Produto').agg(cols_agg).reset_index()
        if 'Lucro Bruto' in df_prod.columns and 'Lucro Líq.' in df_prod.columns:
            df_prod['Mg. Líq. %'] = (df_prod['Lucro Líq.'] / df_prod['Lucro Bruto'] * 100).round(1)
        df_prod = df_prod.sort_values('Lucro Líq.', ascending=False)

        st.dataframe(
            df_prod,
            column_config={
                "Produto":      st.column_config.TextColumn("🌱 Commodity"),
                "Peso Kg":      st.column_config.NumberColumn("⚖️ Peso (Kg)",    format="%d"),
                "Sacas/Ton":    st.column_config.NumberColumn("📦 Sacas/Ton",    format="%d"),
                "Lucro Bruto":  st.column_config.NumberColumn("💰 L. Bruto",     format="R$ %.2f"),
                "Total Frete":  st.column_config.NumberColumn("🚚 Frete",        format="R$ %.2f"),
                "Impostos":     st.column_config.NumberColumn("🏛️ Impostos",     format="R$ %.2f"),
                "Comissão":     st.column_config.NumberColumn("🤝 Comissão",     format="R$ %.2f"),
                "Lucro Líq.":   st.column_config.NumberColumn("🎯 L. Líquido",   format="R$ %.2f"),
                "Mg. Líq. %":   st.column_config.ProgressColumn("📈 Mg. Líq. %", format="%.1f%%", min_value=0, max_value=100),
            },
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("Dados de produto não disponíveis para os filtros selecionados.")

    # ── Top clientes ──────────────────────────────────────────────────────────
    if not df_lf.empty and 'Cliente' in df_lf.columns and 'Lucro Líq.' in df_lf.columns:
        st.markdown("<br>", unsafe_allow_html=True)
        secao("Top 5 Clientes por Lucro Líquido", "Concentração de carteira")
        top_cli = (df_lf.groupby('Cliente')['Lucro Líq.'].sum()
                        .nlargest(5).reset_index()
                        .rename(columns={'Cliente': 'Cliente', 'Lucro Líq.': 'Lucro Líquido'}))
        total_ll = top_cli['Lucro Líquido'].sum()
        top_cli['Participação %'] = (top_cli['Lucro Líquido'] / total_ll * 100).round(1) if total_ll else 0

        st.dataframe(top_cli, column_config={
            "Cliente":       st.column_config.TextColumn("👤 Cliente"),
            "Lucro Líquido": st.column_config.NumberColumn("🎯 Lucro Líquido", format="R$ %.2f"),
            "Participação %":st.column_config.ProgressColumn("📊 Participação", format="%.1f%%", min_value=0, max_value=100),
        }, hide_index=True, use_container_width=True)
