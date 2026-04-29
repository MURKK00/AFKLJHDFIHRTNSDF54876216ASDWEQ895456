import streamlit as st
from utils.formatters import secao, br, pct_fmt

def render(kpis: dict):
    k = kpis

    # 1. Cabeçalho com a caixinha (badge) de status no topo
    pos = k['lucro_liquido_final'] >= 0
    cor_status = "#2ECC71" if pos else "#E74C3C"
    texto_status = "RESULTADO POSITIVO" if pos else "RESULTADO NEGATIVO"

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; 
                margin-bottom:24px; padding-bottom:12px; border-bottom:1px solid #2A2D38">
        <div>
            <h2 style='margin:0; color:#FFFFFF; font-weight:800; font-size: 24px; font-family:"Montserrat", sans-serif;'>Demonstração do Resultado</h2>
            <span style='color:#8B8FA8; font-size:14px;'>Período selecionado via filtros</span>
        </div>
        <div style="background:{cor_status}22; border:1px solid {cor_status}; border-radius:6px; 
                    padding:6px 12px; display:flex; align-items:center; gap:8px">
            <div style="width:8px; height:8px; background:{cor_status}; border-radius:50%"></div>
            <span style="color:{cor_status}; font-size:11px; font-weight:700; letter-spacing:0.5px;">{texto_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_dre, col_info = st.columns([2, 1])

    with col_dre:
        # Construção da DRE em blocos colados (visual Premium mantido)
        cor_final = "#2ECC71" if k['lucro_liquido_final'] >= 0 else "#E74C3C"
        
        html_dre = (
            "<div style='background:#16181F;border:1px solid #2A2D38;border-radius:16px;padding:32px'>"
            # Linha de Receita
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:20px;background:rgba(255,255,255,0.03);border-radius:10px;margin-bottom:12px'>"
            f"<span style='color:#C8CAD4;font-size:16px;font-weight:800'>(+) Receita / Lucro Bruto dos Contratos</span>"
            f"<span style='color:#F29124;font-size:18px;font-weight:800;font-family:\"Montserrat\",sans-serif'>{br(k['receita_bruta'])}</span>"
            "</div>"
            # Linhas de Dedução
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #2A2D38'>"
            f"<span style='color:#C8CAD4;font-size:15px;font-weight:500'>(-) Total de Fretes</span>"
            f"<span style='color:#E74C3C;font-size:16px;font-weight:500;font-family:\"Montserrat\",sans-serif'>{br(-k['frete'])}</span>"
            "</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #2A2D38'>"
            f"<span style='color:#C8CAD4;font-size:15px;font-weight:500'>(-) Impostos sobre Contratos</span>"
            f"<span style='color:#E74C3C;font-size:16px;font-weight:500;font-family:\"Montserrat\",sans-serif'>{br(-k['impostos_venda'])}</span>"
            "</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:14px 20px;margin-bottom:10px'>"
            f"<span style='color:#C8CAD4;font-size:15px;font-weight:500'>(-) Comissões Pagas</span>"
            f"<span style='color:#E74C3C;font-size:16px;font-weight:500;font-family:\"Montserrat\",sans-serif'>{br(-k['comissao'])}</span>"
            "</div>"
            # Resultado Operacional
            "<div style='height:2px;background:#2A2D38;margin:15px 0'></div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:20px;background:rgba(59,130,246,0.05);border-radius:10px;margin:12px 0'>"
            f"<span style='color:#C8CAD4;font-size:16px;font-weight:800'>(=) Lucro Líquido Operacional</span>"
            f"<span style='color:#3B82F6;font-size:18px;font-weight:800;font-family:\"Montserrat\",sans-serif'>{br(k['lucro_operacional'])}</span>"
            "</div>"
            # Despesas Administrativas
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:14px 20px;margin-bottom:10px'>"
            f"<span style='color:#C8CAD4;font-size:15px;font-weight:500'>(-) Despesas Administrativas</span>"
            f"<span style='color:#E74C3C;font-size:16px;font-weight:500;font-family:\"Montserrat\",sans-serif'>{br(-k['despesas_admin'])}</span>"
            "</div>"
            # Resultado Final
            "<div style='height:2px;background:#2A2D38;margin:15px 0'></div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:22px 20px;background:rgba(46,204,113,0.08);border-radius:10px;margin-top:12px'>"
            f"<span style='color:#C8CAD4;font-size:17px;font-weight:900'>(=) LUCRO LÍQUIDO FINAL</span>"
            f"<span style='color:{cor_final};font-size:20px;font-weight:900;font-family:\"Montserrat\",sans-serif'>{br(k['lucro_liquido_final'])}</span>"
            "</div>"
            "</div>"
        )
        st.markdown(html_dre, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Impacto Financeiro (movido para ficar grudado na tabela DRE principal)
        st.markdown("<p style='font-family:\"Montserrat\",sans-serif;font-size:16px;font-weight:700;color:#E0E2EB;margin:0 0 16px 0'>Impacto Financeiro (Deduções)</p>", unsafe_allow_html=True)
        
        itens = [
            ("Fretes",           k['frete'],           k['receita_bruta']),
            ("Impostos",         k['impostos_venda'],  k['receita_bruta']),
            ("Comissões",        k['comissao'],         k['receita_bruta']),
            ("Desp. Admin.",     k['despesas_admin'],   k['receita_bruta']),
        ]
        
        c1, c2, c3, c4 = st.columns(4)
        for i, (nome, val, base) in enumerate(itens):
            pct = val / base * 100 if base else 0
            with [c1, c2, c3, c4][i]:
                # Cards levemente ajustados (padding reduzido) para encaixarem perfeitamente na coluna da DRE
                h = (
                    f"<div style='background:#16181F;border:1px solid #2A2D38;border-radius:12px;padding:16px;text-align:center'>"
                    f"<div style='font-size:11px;color:#6B7080;font-weight:600;text-transform:uppercase;margin-bottom:8px'>{nome}</div>"
                    f"<div style='font-size:18px;font-weight:800;color:#E74C3C;font-family:\"Montserrat\",sans-serif'>{br(val)}</div>"
                    f"<div style='font-size:12px;color:#F59E0B;margin-top:4px'>{pct_fmt(pct)} da receita</div>"
                    f"<div style='background:#2A2D38;border-radius:6px;height:6px;margin-top:10px'><div style='background:#E74C3C;height:6px;border-radius:6px;width:{min(pct,100):.1f}%'></div></div></div>"
                )
                st.markdown(h, unsafe_allow_html=True)

    with col_info:
        # Análise de Margens continua na direita, agora mais limpa
        st.markdown("<div style='background:#16181F;border:1px solid #2A2D38;border-radius:16px;padding:24px'><p style='font-family:\"Montserrat\",sans-serif;font-size:16px;font-weight:700;color:#E0E2EB;margin:0 0 20px 0'>Análise de Margens</p>", unsafe_allow_html=True)

        margens = [
            ("Margem Bruta",         k['margem_bruta'],  "% após custos diretos"),
            ("Margem Operacional",   k['margem_op'],     "% após fretes e impostos"),
            ("Margem Líquida Final", k['margem_liq'],    "% após todas as despesas"),
            ("Desp. / Receita",      k['indice_desp'],   "% da receita consumida"),
        ]

        html_info = ""
        for nome, val, desc in margens:
            cor = "#2ECC71" if val >= 15 else "#F59E0B" if val >= 0 else "#E74C3C"
            html_info += (
                f"<div style='margin-bottom:16px;padding:18px;background:#1E2029;border-radius:12px;border-left:5px solid {cor}'>"
                f"<div style='font-size:12px;color:#6B7080;font-weight:600;text-transform:uppercase;letter-spacing:1px'>{nome}</div>"
                f"<div style='font-size:28px;font-weight:800;color:{cor};font-family:\"Montserrat\",sans-serif'>{pct_fmt(val)}</div>"
                f"<div style='font-size:12px;color:#8B8FA8;margin-top:4px'>{desc}</div></div>"
            )
            
        st.markdown(html_info + "</div>", unsafe_allow_html=True)