import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.formatters import secao, br, br_mil, pct_fmt
from utils.data_loader import calcular_kpis, mensal_por_ano, trimestral_por_ano, por_produto_ano

LAY = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
           font=dict(family="Montserrat", color="#C8CAD4", size=12),
           margin=dict(l=10,r=10,t=40,b=10),
           legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2A2D38", borderwidth=1),
           xaxis=dict(gridcolor="#1E2029", linecolor="#2A2D38"),
           yaxis=dict(gridcolor="#1E2029", linecolor="#2A2D38"))

C25, C26 = "#3B82F6", "#F29124"

def _delta_card(titulo, v25, v26, pct=False, icone=""):
    if pct:
        s25, s26 = pct_fmt(v25), pct_fmt(v26)
        pct_chg = v26 - v25
    else:
        s25, s26 = br_mil(v25), br_mil(v26)
        delta = v26 - v25
        pct_chg = (delta/abs(v25)*100) if v25 else 0
    pos = pct_chg >= 0
    cor = "#2ECC71" if pos else "#E74C3C"
    sig = "▲" if pos else "▼"
    st.markdown(f"""
    <div style="background:#16181F;border:1px solid #2A2D38;border-radius:12px;padding:16px 18px;margin-bottom:4px">
      <div style="font-size:10px;color:#6B7080;text-transform:uppercase;font-weight:600;letter-spacing:1px;margin-bottom:10px">{icone} {titulo}</div>
      <div style="display:flex;justify-content:space-between;align-items:flex-end">
        <div>
          <div style="font-size:10px;color:{C25};font-weight:600;margin-bottom:2px">2025</div>
          <div style="font-family:'Montserrat',sans-serif;font-size:15px;font-weight:700;color:{C25}">{s25}</div>
        </div>
        <div style="text-align:center;padding:0 10px">
          <div style="font-size:16px">{sig}</div>
          <div style="font-size:11px;color:{cor};font-weight:700">{pct_fmt(abs(pct_chg))}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:10px;color:{C26};font-weight:600;margin-bottom:2px">2026</div>
          <div style="font-family:'Montserrat',sans-serif;font-size:15px;font-weight:700;color:{C26}">{s26}</div>
        </div>
      </div>
      <div style="background:#2A2D38;border-radius:4px;height:3px;margin-top:10px">
        <div style="background:{cor};height:3px;border-radius:4px;width:{min(abs(pct_chg),100):.0f}%"></div>
      </div>
    </div>""", unsafe_allow_html=True)

def render(df_lucro, df_desp, kpis):
    anos = sorted(df_lucro['Ano'].unique()) if 'Ano' in df_lucro.columns else []
    tem_2025 = 2025 in anos and 2026 in anos

    # Apenas as abas relevantes (sem mercado externo/interno)
    sub_tabs = st.tabs(["📊 Anual","📆 Trimestral","🌱 Por Produto"])

    # ══════════════════ ABA ANUAL ══════════════════════════════════════════════
    with sub_tabs[0]:
        if not tem_2025:
            st.info("Preencha os dados de 2025 no Excel para ativar o comparativo.")
            _graf_apenas_2026(df_lucro, df_desp)
        else:
            k25 = calcular_kpis(df_lucro[df_lucro['Ano']==2025], df_desp[df_desp['Ano']==2025] if 'Ano' in df_desp.columns else pd.DataFrame())
            k26 = calcular_kpis(df_lucro[df_lucro['Ano']==2026], df_desp[df_desp['Ano']==2026] if 'Ano' in df_desp.columns else pd.DataFrame())

            secao("KPIs Anuais — 2025 × 2026")
            c1,c2,c3 = st.columns(3)
            with c1:
                _delta_card("Lucro Bruto",             k25['receita_bruta'],     k26['receita_bruta'],     icone="💰")
                _delta_card("Despesas Administrativas",k25['despesas_admin'],     k26['despesas_admin'],     icone="📉")
            with c2:
                _delta_card("Lucro Líq. Operacional",  k25['lucro_operacional'], k26['lucro_operacional'], icone="⚙️")
                _delta_card("Margem Operacional",       k25['margem_op'],         k26['margem_op'],         icone="📊", pct=True)
            with c3:
                _delta_card("Lucro Líquido Final",      k25['lucro_liquido_final'],k26['lucro_liquido_final'],icone="🏆")
                _delta_card("Margem Líquida",           k25['margem_liq'],        k26['margem_liq'],        icone="📈", pct=True)

            st.markdown("<br>", unsafe_allow_html=True)
            secao("Evolução Mensal: Lucro Líquido Operacional")
            df_men = mensal_por_ano(df_lucro, df_desp)
            fig = go.Figure()
            for ano, cor in [(2025,C25),(2026,C26)]:
                col = f'Lucro_Op_{ano}'
                if col in df_men.columns:
                    fig.add_trace(go.Bar(name=str(ano), x=df_men['Mês'], y=df_men[col],
                                         marker_color=cor, opacity=0.85))
            fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y", line=dict(color="#E74C3C", dash="dash"))
            fig.update_layout(**LAY, barmode="group", height=340, title="Lucro Líq. Operacional/Mês")
            st.plotly_chart(fig, use_container_width=True)

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig2 = go.Figure()
                for ano, cor in [(2025,C25),(2026,C26)]:
                    col = f'Receita_{ano}'
                    if col in df_men.columns:
                        fig2.add_trace(go.Scatter(name=str(ano), x=df_men['Mês'], y=df_men[col],
                                                   mode="lines+markers", line=dict(color=cor,width=2.5), marker=dict(size=7)))
                fig2.update_layout(**LAY, height=300, title="Receita Bruta Mensal")
                st.plotly_chart(fig2, use_container_width=True)
            with col_g2:
                fig3 = go.Figure()
                for ano, cor in [(2025,C25),(2026,C26)]:
                    col = f'Desp_{ano}'
                    if col in df_men.columns:
                        fig3.add_trace(go.Scatter(name=str(ano), x=df_men['Mês'], y=df_men[col],
                                                   mode="lines+markers", line=dict(color=cor,width=2.5,dash='dot'),
                                                   marker=dict(size=7)))
                fig3.update_layout(**LAY, height=300, title="Despesas Administrativas/Mês")
                st.plotly_chart(fig3, use_container_width=True)

    # ══════════════════ ABA TRIMESTRAL ════════════════════════════════════════
    with sub_tabs[1]:
        secao("Comparativo Trimestral", "Lucro Líquido por trimestre" + (" — 2025 vs 2026" if tem_2025 else " — 2026"))
        df_trim = trimestral_por_ano(df_lucro, df_desp)

        fig_t = go.Figure()
        for ano, cor in [(2025,C25),(2026,C26)]:
            col = f'Lucro_Liq_{ano}'
            if col in df_trim.columns:
                fig_t.add_trace(go.Bar(name=str(ano), x=df_trim['Trimestre'], y=df_trim[col],
                                        marker_color=cor, opacity=0.9, text=[br_mil(v) for v in df_trim[col]],
                                        textposition='outside'))
        fig_t.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y", line=dict(color="#E74C3C", dash="dash"))
        fig_t.update_layout(**LAY, barmode="group", height=380, title="Lucro Líquido por Trimestre")
        st.plotly_chart(fig_t, use_container_width=True)

        secao("Detalhamento Trimestral")
        rows_tab = []
        for _, row in df_trim.iterrows():
            entry = {'Trimestre': row['Trimestre']}
            for ano in [2025,2026]:
                if f'Receita_{ano}' in row: entry[f'Receita {ano}'] = row[f'Receita_{ano}']
                if f'Lucro_Op_{ano}' in row: entry[f'L.Op. {ano}']  = row[f'Lucro_Op_{ano}']
                if f'Lucro_Liq_{ano}' in row: entry[f'L.Líq. {ano}']= row[f'Lucro_Liq_{ano}']
            if tem_2025:
                entry['Δ L.Líq.'] = row.get('Lucro_Liq_2026',0) - row.get('Lucro_Liq_2025',0)
                v25 = row.get('Lucro_Liq_2025',0)
                entry['Δ %'] = (entry['Δ L.Líq.']/abs(v25)*100) if v25 else 0
            rows_tab.append(entry)
        df_tab = pd.DataFrame(rows_tab)
        cfg = {'Trimestre': st.column_config.TextColumn("📆 Trimestre")}
        for col in df_tab.columns:
            if col == 'Trimestre': continue
            if 'Δ %' in col:
                cfg[col] = st.column_config.NumberColumn(col, format="%.1f%%")
            else:
                cfg[col] = st.column_config.NumberColumn(col, format="R$ %.2f")
        st.dataframe(df_tab, column_config=cfg, hide_index=True, use_container_width=True)

    # ══════════════════ ABA PRODUTO ════════════════════════════════════════════
    with sub_tabs[2]:
        secao("Comparativo por Produto / Commodity")
        df_prod = por_produto_ano(df_lucro)

        fig_p = go.Figure()
        for ano, cor in [(2025,C25),(2026,C26)]:
            col = f'LL_{ano}'
            if col in df_prod.columns:
                fig_p.add_trace(go.Bar(name=str(ano), x=df_prod['Produto'], y=df_prod[col],
                                        marker_color=cor, opacity=0.9))
        fig_p.update_layout(**LAY, barmode="group", height=360, title="Lucro Líquido por Produto")
        st.plotly_chart(fig_p, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_kg = go.Figure()
            for ano, cor in [(2025,C25),(2026,C26)]:
                col = f'KG_{ano}'
                if col in df_prod.columns:
                    fig_kg.add_trace(go.Bar(name=str(ano), x=df_prod['Produto'], y=df_prod[col],
                                             marker_color=cor, opacity=0.9))
            fig_kg.update_layout(**LAY, barmode="group", height=300, title="Peso (Kg) por Produto")
            st.plotly_chart(fig_kg, use_container_width=True)
        with col_g2:
            ano_ref = 2026
            col_lb = f'LB_{ano_ref}'
            if col_lb in df_prod.columns:
                df_pie = df_prod[df_prod[col_lb] > 0]
                fig_pie = go.Figure(go.Pie(
                    labels=df_pie['Produto'], values=df_pie[col_lb],
                    hole=0.45, marker=dict(line=dict(color="#0F1117", width=2)),
                    textfont=dict(size=12, family="Montserrat")))
                fig_pie.update_layout(**LAY, height=300, title=f"Participação no Lucro Bruto ({ano_ref})")
                st.plotly_chart(fig_pie, use_container_width=True)

        secao("Tabela Detalhada por Produto")
        tab_rows = []
        for _, row in df_prod.iterrows():
            entry = {'Produto': row['Produto']}
            for ano in [2025,2026]:
                if f'LB_{ano}' in row: entry[f'L.Bruto {ano}'] = row[f'LB_{ano}']
                if f'LL_{ano}' in row: entry[f'L.Líq. {ano}']  = row[f'LL_{ano}']
                if f'KG_{ano}' in row: entry[f'Peso Kg {ano}'] = row[f'KG_{ano}']
                if f'NC_{ano}' in row: entry[f'Contratos {ano}']= int(row[f'NC_{ano}'])
            if tem_2025 and 'LL_2025' in row and 'LL_2026' in row:
                delta = row['LL_2026'] - row['LL_2025']
                entry['Δ L.Líq.'] = delta
                entry['Δ %'] = (delta/abs(row['LL_2025'])*100) if row['LL_2025'] else 0
            tab_rows.append(entry)
        df_tab_p = pd.DataFrame(tab_rows)
        cfg_p = {'Produto': st.column_config.TextColumn("🌱 Produto")}
        for col in df_tab_p.columns:
            if col == 'Produto': continue
            if 'Δ %' in col or '%' in col:
                cfg_p[col] = st.column_config.NumberColumn(col, format="%.1f%%")
            elif 'Contratos' in col:
                cfg_p[col] = st.column_config.NumberColumn(col, format="%d")
            elif 'Kg' in col:
                cfg_p[col] = st.column_config.NumberColumn(col, format="%d")
            else:
                cfg_p[col] = st.column_config.NumberColumn(col, format="R$ %.2f")
        st.dataframe(df_tab_p, column_config=cfg_p, hide_index=True, use_container_width=True)

def _graf_apenas_2026(df_lucro, df_desp):
    nomes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    ys = [df_lucro[(df_lucro['Ano']==2026)&(df_lucro['MesNum']==mi)]['Lucro Líq.'].sum()
          for mi in range(1,13)]
    fig = go.Figure(go.Bar(x=nomes, y=ys, marker_color=C26))
    fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y", line=dict(color="#E74C3C", dash="dash"))
    fig.update_layout(**LAY, title="Lucro Líquido — 2026")
    st.plotly_chart(fig, use_container_width=True)