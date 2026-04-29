import streamlit as st
import pandas as pd
from utils.formatters import secao, br, br_mil, pct_fmt

def render(kpis: dict, df_lf: pd.DataFrame, df_df: pd.DataFrame):
    k = kpis

    # ── Cabeçalho executivo ───────────────────────────────────────────────────
    pos = k['lucro_liquido_final'] >= 0
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#16181F 0%,#1E2029 100%);
                border:1px solid #2A2D38;border-radius:16px;padding:28px;
                margin-bottom:24px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div style="font-family:'Montserrat',sans-serif;font-size:11px;font-weight:600;
                            color:#6B7080;text-transform:uppercase;letter-spacing:2px;
                            margin-bottom:8px">Resumo Executivo — Grupo Bela Cereais</div>
                <div style="font-family:'Montserrat',sans-serif;font-size:26px;font-weight:800;
                            color:#FFFFFF">Comercialização de Grãos</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:32px">{'✅' if pos else '🚨'}</div>
                <div style="font-family:'Montserrat',sans-serif;font-size:14px;font-weight:700;
                            color:{'#2ECC71' if pos else '#E74C3C'};margin-top:4px">
                    {'Superavitário' if pos else 'Deficitário'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs de Destaque ─────────────────────────────────────────────────────
    kpi_items = [
        ("Receita / Lucro Bruto",     br_mil(k['receita_bruta']),    "#F29124"),
        ("Lucro Líq. Operacional",    br_mil(k['lucro_operacional']),
             "#2ECC71" if k['lucro_operacional'] >= 0 else "#E74C3C"),
        ("Lucro Líquido Final",       br_mil(k['lucro_liquido_final']),
             "#2ECC71" if k['lucro_liquido_final'] >= 0 else "#E74C3C"),
        ("Margem Líquida",            pct_fmt(k['margem_liq']),
             "#2ECC71" if k['margem_liq'] >= 0 else "#E74C3C"),
        ("Desp. sobre Receita",       pct_fmt(k['indice_desp']),
             "#2ECC71" if k['indice_desp'] < 60 else "#F59E0B" if k['indice_desp'] < 80 else "#E74C3C"),
    ]

    cols = st.columns(5)
    for i, (titulo, valor, cor) in enumerate(kpi_items):
        with cols[i]:
            st.markdown(f"""
            <div style="background:#16181F;border:1px solid #2A2D38;border-top:3px solid {cor};
                        border-radius:12px;padding:20px;text-align:center">
                <div style="font-size:11px;color:#6B7080;text-transform:uppercase;
                            font-weight:600;letter-spacing:0.5px;margin-bottom:8px">{titulo}</div>
                <div style="font-family:'Montserrat',sans-serif;font-size:20px;font-weight:800;
                            color:{cor}">{valor}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DRE Consolidada e Análise ───────────────────────────────────────────
    col_dre, col_anal = st.columns([3, 2])

    with col_dre:
        secao("DRE Consolidada")
        
        v_lb  = br(k['receita_bruta'])
        v_fr  = br(-k['frete'])
        v_imp = br(-k['impostos_venda'])
        v_com = br(-k['comissao'])
        v_lop = br(k['lucro_operacional'])
        v_dad = br(-k['despesas_admin'])
        v_liq = br(k['lucro_liquido_final'])

        st.markdown(f"""
        <div style="border: 1px solid #2A2D38; border-radius: 12px; overflow: hidden;">
            <table style="width:100%; border-collapse: collapse; font-family:'Montserrat', sans-serif; background-color: #16181F;">
                <tr style="background-color: #1E2029; color: #8B8FA8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">
                    <th style="text-align: left; padding: 15px 20px; border-bottom: 1px solid #2A2D38;">Descrição da Rubrica</th>
                    <th style="text-align: right; padding: 15px 20px; border-bottom: 1px solid #2A2D38;">Valor Total (R$)</th>
                </tr>
                <tr style="border-bottom: 1px solid #2A2D38;">
                    <td style="padding: 14px 20px; color: #E0E2EB; font-size: 13px;">Lucro Bruto (Contratos)</td>
                    <td style="padding: 14px 20px; text-align: right; color: #FFFFFF; font-weight: 600; font-family: 'JetBrains Mono', monospace;">{v_lb}</td>
                </tr>
                <tr style="border-bottom: 1px solid #2A2D38;">
                    <td style="padding: 14px 20px; color: #E0E2EB; font-size: 13px;">(-) Custos de Frete</td>
                    <td style="padding: 14px 20px; text-align: right; color: #E74C3C; font-family: 'JetBrains Mono', monospace;">{v_fr}</td>
                </tr>
                <tr style="border-bottom: 1px solid #2A2D38;">
                    <td style="padding: 14px 20px; color: #E0E2EB; font-size: 13px;">(-) Impostos e Taxas</td>
                    <td style="padding: 14px 20px; text-align: right; color: #E74C3C; font-family: 'JetBrains Mono', monospace;">{v_imp}</td>
                </tr>
                <tr style="border-bottom: 1px solid #2A2D38;">
                    <td style="padding: 14px 20px; color: #E0E2EB; font-size: 13px;">(-) Comissões sobre Venda</td>
                    <td style="padding: 14px 20px; text-align: right; color: #E74C3C; font-family: 'JetBrains Mono', monospace;">{v_com}</td>
                </tr>
                <tr style="background-color: rgba(46, 204, 113, 0.08); border-bottom: 2px solid #2ECC71;">
                    <td style="padding: 16px 20px; color: #2ECC71; font-weight: 700; font-size: 14px; text-transform: uppercase;">= RESULTADO OPERACIONAL</td>
                    <td style="padding: 16px 20px; text-align: right; color: #2ECC71; font-weight: 800; font-size: 15px; font-family: 'JetBrains Mono', monospace;">{v_lop}</td>
                </tr>
                <tr style="border-bottom: 1px solid #2A2D38;">
                    <td style="padding: 14px 20px; color: #E0E2EB; font-size: 13px;">(-) Despesas Administrativas Fixas</td>
                    <td style="padding: 14px 20px; text-align: right; color: #E74C3C; font-family: 'JetBrains Mono', monospace;">{v_dad}</td>
                </tr>
                <tr style="background: linear-gradient(90deg, #1E2029 0%, #252833 100%);">
                    <td style="padding: 20px; color: #F29124; font-weight: 800; font-size: 16px; text-transform: uppercase;">= LUCRO LÍQUIDO FINAL</td>
                    <td style="padding: 20px; text-align: right; color: #F29124; font-weight: 900; font-size: 18px; font-family: 'JetBrains Mono', monospace;">{v_liq}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_anal:
        secao("Análise de Risco")
        alertas = []
        if k['indice_desp'] > 80:
            alertas.append(("🔴 CRÍTICO", f"Despesas consomem {pct_fmt(k['indice_desp'])} da receita", "#E74C3C"))
        elif k['indice_desp'] > 60:
            alertas.append(("🟡 ATENÇÃO", f"Índice desp./receita elevado: {pct_fmt(k['indice_desp'])}", "#F59E0B"))
        if k['lucro_liquido_final'] < 0:
            alertas.append(("🔴 CRÍTICO", "Resultado líquido negativo no período", "#E74C3C"))
        
        if not alertas:
            alertas.append(("🟢 SAUDÁVEL", "Indicadores dentro dos parâmetros", "#2ECC71"))

        for tipo, msg, cor in alertas:
            st.markdown(f"""
            <div style="background:rgba(0,0,0,0.2);border-left:3px solid {cor};
                        border-radius:8px;padding:12px 14px;margin-bottom:8px">
                <div style="font-size:11px;font-weight:700;color:{cor}">{tipo}</div>
                <div style="font-size:13px;color:#C8CAD4;margin-top:3px">{msg}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        secao("Destaques Operacionais")
        volume_sacas = k['total_sacas'] if 'total_sacas' in k else k['peso_total'] / 60

        # --- CORREÇÃO: Formatação de número para o padrão PT-BR (1.234,56) ---
        vol_fmt = f"{volume_sacas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        peso_fmt = f"{k['peso_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        # ----------------------------------------------------------------------

        st.markdown(f"""
        <div style="background:#16181F;border:1px solid #2A2D38;border-radius:12px;padding:16px">
            <div style="display:flex;justify-content:space-between;padding:8px 0; border-bottom:1px solid #2A2D38">
                <span style="color:#6B7080;font-size:14px">Contratos Ativos</span>
                <span style="color:#F29124;font-weight:700;">{k['n_contratos']}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0; border-bottom:1px solid #2A2D38">
                <span style="color:#6B7080;font-size:14px">Ticket Médio</span>
                <span style="color:#F29124;font-weight:700;">{br_mil(k['ticket_medio'])}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0; border-bottom:1px solid #2A2D38">
                <span style="color:#6B7080;font-size:14px">Lucro p/ Saca</span>
                <span style="color:#F29124;font-weight:700;">{br(k['lucro_por_saca'])}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0; border-bottom:1px solid #2A2D38">
                <span style="color:#6B7080;font-size:14px">Volume Negociado</span>
                <span style="color:#F29124;font-weight:700;">{vol_fmt} scs</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0">
                <span style="color:#6B7080;font-size:14px">Peso Total</span>
                <span style="color:#F29124;font-weight:700;">{peso_fmt} kg</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Performance e Exportação ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_prod, col_exp = st.columns([3, 1])

    with col_prod:
        secao("Performance por Commodity")
        if not df_lf.empty and 'Produto' in df_lf.columns:
            df_prod = df_lf.groupby('Produto').agg({
                'Peso Kg':'sum','Lucro Bruto':'sum','Lucro Líq.':'sum'
            }).reset_index()
            df_prod = df_prod.sort_values('Lucro Líq.', ascending=False)
            st.dataframe(df_prod, column_config={
                "Produto": st.column_config.TextColumn("🌱 Commodity"),
                "Peso Kg": st.column_config.NumberColumn("⚖️ Kg", format="%d"),
                "Lucro Bruto": st.column_config.NumberColumn("💰 L. Bruto", format="R$ %.2f"),
                "Lucro Líq.": st.column_config.NumberColumn("🎯 L. Líquido", format="R$ %.2f"),
            }, hide_index=True, use_container_width=True)

    with col_exp:
        secao("Exportar Dados")
        st.button("📥 Gerar Relatório Executivo (.xlsx)", use_container_width=True)