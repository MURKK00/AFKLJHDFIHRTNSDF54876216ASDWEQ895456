import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.formatters import secao

def estilizar_grafico(fig, titulo="", height=380, showlegend=True, invert_y=False):
    fig.update_layout(
        title=titulo, height=height, showlegend=showlegend,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Montserrat", color="#C8CAD4", size=12),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2A2D38", borderwidth=1)
    )
    if len(fig.data) > 0 and fig.data[0].type not in ['pie', 'treemap']:
        fig.update_xaxes(gridcolor="#1E2029", linecolor="#2A2D38", tickfont=dict(size=11))
        fig.update_yaxes(gridcolor="#1E2029", linecolor="#2A2D38", tickfont=dict(size=11))
        if invert_y:
            fig.update_yaxes(autorange="reversed")
    return fig

def render(df_lf: pd.DataFrame, df_df: pd.DataFrame):
    secao("Evolução Financeira Mensal", "Receita, resultado operacional e lucro líquido por período")

    if not df_lf.empty and 'Mês_Filtro' in df_lf.columns:
        cols_sum = {c: 'sum' for c in ['Lucro Bruto','Total Frete','Impostos','Comissão','Lucro Líq.'] if c in df_lf.columns}
        df_mes = df_lf.groupby('Mês_Filtro').agg(cols_sum).reset_index().sort_values('Mês_Filtro')

        if 'Lucro Bruto' in df_mes.columns:
            df_mes['Lucro Op.'] = (df_mes['Lucro Bruto'] - df_mes.get('Total Frete', 0) - df_mes.get('Impostos', 0) - df_mes.get('Comissão', 0))

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Lucro Bruto", x=df_mes['Mês_Filtro'], y=df_mes.get('Lucro Bruto'), marker_color="#F29124", opacity=0.85))
        if 'Lucro Op.' in df_mes.columns:
            fig.add_trace(go.Scatter(name="Lucro Operacional", x=df_mes['Mês_Filtro'], y=df_mes['Lucro Op.'], mode="lines+markers", line=dict(color="#3B82F6", width=2.5), marker=dict(size=7)))
        if 'Lucro Líq.' in df_mes.columns:
            fig.add_trace(go.Scatter(name="Lucro Líquido", x=df_mes['Mês_Filtro'], y=df_mes['Lucro Líq.'], mode="lines+markers", line=dict(color="#2ECC71", width=2.5, dash="dot"), marker=dict(size=7)))

        estilizar_grafico(fig, titulo="Evolução Financeira por Mês", showlegend=True)
        fig.update_layout(barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados mensais insuficientes para gráfico.")

    st.markdown("<br>", unsafe_allow_html=True)
    secao("Cascata da DRE", "Decomposição visual do resultado — do lucro bruto ao lucro líquido final")

    from utils.data_loader import calcular_kpis
    k = calcular_kpis(df_lf, df_df)
    labels = ["Lucro Bruto", "(-) Fretes", "(-) Impostos", "(-) Comissões", "Luc. Operacional", "(-) Desp. Admin.", "Luc. Líquido Final"]
    valores = [k.get('receita_bruta',0), -k.get('frete',0), -k.get('impostos_venda',0), -k.get('comissao',0), k.get('lucro_operacional',0), -k.get('despesas_admin',0), k.get('lucro_liquido_final',0)]
    medidas = ["absolute","relative","relative","relative","total","relative","total"]

    fig_wf = go.Figure(go.Waterfall(
        name="DRE", orientation="v", measure=medidas, x=labels, y=valores,
        connector=dict(line=dict(color="#2A2D38", width=1.5)),
        decreasing=dict(marker=dict(color="#E74C3C")), increasing=dict(marker=dict(color="#2ECC71")),
        totals=dict(marker=dict(color="#F29124")), text=[f"R$ {abs(v)/1000:.0f}K" for v in valores], textposition="outside",
    ))
    estilizar_grafico(fig_wf, titulo="Waterfall — DRE", height=420, showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        secao("Top 10 Despesas Administrativas")
        if not df_df.empty and 'Item' in df_df.columns and 'Valor' in df_df.columns:
            top10 = df_df.groupby('Item')['Valor'].sum().nlargest(10).reset_index()
            fig_bar = go.Figure(go.Bar(
                x=top10['Valor'], y=top10['Item'], orientation="h",
                marker=dict(color=top10['Valor'], colorscale=[[0,"#2A2D38"],[1,"#F29124"]]),
                text=[f"R$ {v:,.0f}".replace(",",".") for v in top10['Valor']], textposition="outside",
            ))
            estilizar_grafico(fig_bar, titulo="Maiores Despesas", height=380, showlegend=False, invert_y=True)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Dados de despesas indisponíveis.")

    with col2:
        secao("Lucro Líquido por Produto (Treemap)")
        if not df_lf.empty and 'Produto' in df_lf.columns and 'Lucro Líq.' in df_lf.columns:
            df_tree = df_lf.groupby('Produto')['Lucro Líq.'].sum().reset_index()
            df_tree = df_tree[df_tree['Lucro Líq.'] > 0]
            if not df_tree.empty:
                fig_tree = px.treemap(df_tree, path=['Produto'], values='Lucro Líq.', color='Lucro Líq.', color_continuous_scale=["#1E2029","#F29124"])
                estilizar_grafico(fig_tree, height=380)
                fig_tree.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("Sem dados positivos para treemap.")
        else:
            st.info("Coluna 'Produto' não encontrada.")

    st.markdown("<br>", unsafe_allow_html=True)
    secao("Eficiência por Contrato", "Volume negociado vs lucro gerado")

    if not df_lf.empty and all(c in df_lf.columns for c in ['Peso Kg','Lucro Líq.','Produto']):
        
        # --- 100% BLINDADO: Gráfico reconstruído sem o Plotly Express ---
        fig_sc = go.Figure()
        produtos = df_lf['Produto'].unique()
        cores_px = px.colors.qualitative.Set2
        
        for i, prod in enumerate(produtos):
            df_p = df_lf[df_lf['Produto'] == prod]
            
            # Monta o texto que aparece ao passar o mouse
            hover_text = df_p.apply(
                lambda row: f"Produto: {row['Produto']}<br>Cliente: {row.get('Cliente', 'N/A')}<br>Peso: {row['Peso Kg']:,.0f} kg<br>Lucro Líq.: R$ {row['Lucro Líq.']:,.2f}", 
                axis=1
            )
            
            fig_sc.add_trace(go.Scatter(
                x=df_p['Peso Kg'], 
                y=df_p['Lucro Líq.'],
                mode='markers',
                name=prod,
                text=hover_text,
                hoverinfo='text',
                marker=dict(
                    size=12,  # TAMANHO FIXO SEM USAR COLUNA, IMPOSSÍVEL DAR ERRO!
                    color=cores_px[i % len(cores_px)],
                    line=dict(width=1, color="#16181F")
                )
            ))
            
        fig_sc.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y", line=dict(color="#E74C3C", dash="dash"))
        estilizar_grafico(fig_sc, titulo="Volume (Kg) × Lucro Líquido por Contrato", height=420)
        st.plotly_chart(fig_sc, use_container_width=True)

    if not df_df.empty and 'Mês_Filtro' in df_df.columns and 'Valor' in df_df.columns:
        secao("Evolução das Despesas Administrativas")
        df_desp_mes = df_df.groupby('Mês_Filtro')['Valor'].sum().reset_index().sort_values('Mês_Filtro')
        fig_line = go.Figure(go.Scatter(
            x=df_desp_mes['Mês_Filtro'], y=df_desp_mes['Valor'], mode="lines+markers",
            fill="tozeroy", fillcolor="rgba(242,145,36,0.08)", line=dict(color="#F29124", width=2.5), marker=dict(size=8, color="#F29124"),
        ))
        estilizar_grafico(fig_line, titulo="Despesas Admin. por Período", showlegend=False)
        st.plotly_chart(fig_line, use_container_width=True)