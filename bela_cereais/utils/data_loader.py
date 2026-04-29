import pandas as pd
import streamlit as st

MAPA_EMPRESAS = {
    'BC_MATRIZ': 'Bela Cereais Matriz',
    'BC_FILIAL':  'Bela Cereais Filial',
    'MM':         'MM Comercio de Grãos',
}

EXP_CLIENTS = {
    'ADROIT OVERSEAS PTE LTD','AGC BRAZIL COMERCIAL EXPORTADORA LTDA',
    'AKSHAR AGRI INDIA PRIVATE LIMITED','AMAGGI EXPORTACAO E IMPORTACAO LTDA',
    'CUTRALE TRADING BRASIL LTDA','CUTRALE TRADING BRASIL LTDA.',
    'JASHAN FOODSTUFF TRADING FZC','JASHAN FOODSTUFF TRADING LLC',
    'LOUIS DREYFUS COMPANY BRASIL S.A.','LACTALIS DO BRASIL - COM IMP EXPT LTDA',
}

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(arquivo='DASHBOARD.xlsx'):
    xls = pd.read_excel(arquivo, sheet_name=None, header=None)
    raw_l = xls.get('BD_LUCRO', pd.DataFrame())
    raw_d = xls.get('BD_DESP',  pd.DataFrame())
    if not raw_l.empty:
        raw_l.columns = raw_l.iloc[0]
        raw_l = raw_l.iloc[1:].reset_index(drop=True)
        raw_l.columns = [str(c).strip() for c in raw_l.columns]
    if not raw_d.empty:
        raw_d.columns = raw_d.iloc[0]
        raw_d = raw_d.iloc[1:].reset_index(drop=True)
        raw_d.columns = [str(c).strip() for c in raw_d.columns]
    return _limpar_lucro(raw_l), _limpar_desp(raw_d)


def _limpar_lucro(df):
    if df.empty: return df
    df = df.copy()
    
    # --- REMOVER LINHAS DE TOTAL VINDAS DO EXCEL ---
    for col in ['Empresa', 'Produto', 'Cliente']:
        if col in df.columns:
            df = df[~df[col].astype(str).str.upper().str.contains('TOTAL', na=False)]
    
    df['Mês'] = pd.to_datetime(df.get('Mês'), errors='coerce')
    df['Ano'] = _extrair_ano(df)
    df = df[df['Ano'].isin([2025,2026])]
    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])
    for col in ['Lucro Bruto','Total Frete','Impostos','Comissão','Lucro Líq.','Peso Kg','Sacas/Ton']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Mês_Filtro'] = df['Mês'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['MesNum']     = df['Mês'].dt.month.fillna(0).astype(int)
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')
    df['Mercado'] = df['Cliente'].apply(
        lambda x: 'Exportação' if str(x).strip().upper() in {c.upper() for c in EXP_CLIENTS}
        else 'Mercado Interno')
    cols_fin = [c for c in ['Lucro Bruto','Peso Kg'] if c in df.columns]
    if cols_fin:
        df = df[df[cols_fin].abs().sum(axis=1) > 0]
    return df.reset_index(drop=True)


def _limpar_desp(df):
    if df.empty: return df
    df = df.copy()
    
    # --- REMOVER LINHAS DE TOTAL VINDAS DO EXCEL ---
    if 'Item' in df.columns:
        df = df[~df['Item'].astype(str).str.upper().str.contains('TOTAL', na=False)]
        
    df['Mês'] = pd.to_datetime(df.get('Mês'), errors='coerce')
    df['Ano'] = _extrair_ano(df)
    df = df[df['Ano'].isin([2025,2026])]
    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])
    if 'Valor' in df.columns:
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df = df[df['Valor'].abs() > 0]
    df['Mês_Filtro'] = df['Mês'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['MesNum']     = df['Mês'].dt.month.fillna(0).astype(int)
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')
    return df.reset_index(drop=True)


def _extrair_ano(df):
    if 'Ano' in df.columns:
        s = pd.to_numeric(df['Ano'], errors='coerce')
        mask = s.isna() | ~s.between(2020,2035)
        if 'Mês' in df.columns:
            s[mask] = df.loc[mask,'Mês'].apply(
                lambda x: x.year if hasattr(x,'year') else 2026)
        return s.fillna(2026).astype(int)
    if 'Mês' in df.columns:
        return df['Mês'].apply(lambda x: x.year if hasattr(x,'year') else 2026).astype(int)
    return pd.Series([2026]*len(df), index=df.index)


def calcular_kpis(df_l, df_d):
    def s(df, col): return df[col].sum() if (not df.empty and col in df.columns) else 0
    rb  = s(df_l,'Lucro Bruto'); frt = s(df_l,'Total Frete')
    imp = s(df_l,'Impostos');    com = s(df_l,'Comissão')
    llc = s(df_l,'Lucro Líq.'); sac = s(df_l,'Sacas/Ton'); kg = s(df_l,'Peso Kg')
    nc  = len(df_l); lop = rb - frt - imp - com
    da  = s(df_d,'Valor');      llf = lop - da
    return dict(
        receita_bruta=rb, frete=frt, impostos_venda=imp, comissao=com,
        lucro_liq_contr=llc, sacas_total=sac, peso_total=kg, n_contratos=nc,
        lucro_operacional=lop, despesas_admin=da, lucro_liquido_final=llf,
        margem_bruta=llc/rb*100  if rb else 0,
        margem_op=lop/rb*100     if rb else 0,
        margem_liq=llf/rb*100    if rb else 0,
        ticket_medio=rb/nc       if nc else 0,
        lucro_por_saca=llf/sac   if sac else 0,
        indice_desp=da/rb*100    if rb else 0,
    )

def mensal_por_ano(df_l, df_d):
    nomes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    anos  = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    rows  = []
    for mi, nome in enumerate(nomes, 1):
        row = {'Mês': nome, 'MesNum': mi}
        for ano in anos:
            lf = df_l[(df_l['Ano']==ano)&(df_l['MesNum']==mi)]
            dd = df_d[(df_d['Ano']==ano)&(df_d['MesNum']==mi)] if not df_d.empty else pd.DataFrame()
            k  = calcular_kpis(lf, dd)
            row[f'Receita_{ano}']   = k['receita_bruta']
            row[f'Lucro_Op_{ano}']  = k['lucro_operacional']
            row[f'Lucro_Liq_{ano}'] = k['lucro_liquido_final']
            row[f'Desp_{ano}']      = k['despesas_admin']
        rows.append(row)
    return pd.DataFrame(rows)

def trimestral_por_ano(df_l, df_d):
    anos = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    trims = [('T1',[1,2,3]),('T2',[4,5,6]),('T3',[7,8,9]),('T4',[10,11,12])]
    rows = []
    for trim_label, meses in trims:
        row = {'Trimestre': trim_label}
        for ano in anos:
            lf = df_l[(df_l['Ano']==ano)&(df_l['MesNum'].isin(meses))]
            dd = df_d[(df_d['Ano']==ano)&(df_d['MesNum'].isin(meses))] if not df_d.empty else pd.DataFrame()
            k  = calcular_kpis(lf, dd)
            row[f'Receita_{ano}']  = k['receita_bruta']
            row[f'Lucro_Op_{ano}'] = k['lucro_operacional']
            row[f'Lucro_Liq_{ano}']= k['lucro_liquido_final']
            row[f'Desp_{ano}']     = k['despesas_admin']
        rows.append(row)
    return pd.DataFrame(rows)

def por_produto_ano(df_l):
    anos = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    produtos = sorted(df_l['Produto'].dropna().unique())
    rows = []
    for prod in produtos:
        row = {'Produto': prod}
        for ano in anos:
            lp = df_l[(df_l['Ano']==ano)&(df_l['Produto']==prod)]
            row[f'LB_{ano}']  = lp['Lucro Bruto'].sum()
            row[f'LL_{ano}']  = lp['Lucro Líq.'].sum()
            row[f'KG_{ano}']  = lp['Peso Kg'].sum()
            row[f'SC_{ano}']  = lp['Sacas/Ton'].sum()
            row[f'NC_{ano}']  = len(lp)
        rows.append(row)
    return pd.DataFrame(rows)