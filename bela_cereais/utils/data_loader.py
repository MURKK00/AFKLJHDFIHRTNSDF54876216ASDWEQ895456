import pandas as pd
import streamlit as st

MAPA_EMPRESAS = {
    'BC_MATRIZ': 'Bela Cereais Matriz',
    'BC_FILIAL': 'Bela Cereais Filial',
    'MM':        'MM Comercio de Grãos',
}

# --- LISTAS DE CLASSIFICAÇÃO CONTÁBIL ---
DESP_COMPL_IGNORAR = {
    'TRANSFERENCIA ENTRE CONTAS', 'FORNECEDORES MERCADORIA', 'EMPRESAS', 'CAPITAL GIRO', 
    'MUTUO SOCIO', 'ADIANTAMENTOS FORNECEDORES', 'IMOVEIS', 'CONSORCIO', 
    'COMISSÃO CONTRATOS (CORRETORA)', 'FRETE (ADTO/SALDO)', 'COMISSAO CONTRATO', 
    'CLIENTES MERCADORIAS', 'ADIANTAMENTOS CLIENTES', 'TRANSFERENCIA'
}

DESP_RESULTADO_FINANCEIRO = {
    'AJUSTE NDF', 'JUROS EMPRESTIMOS', 'JUROS S/ MUTUO SOCIO', 'IOF', 'TARIFA BANCARIA',
    'TAXA FINANCIAMENTO', 'JUROS DE ANTECIPACAO', 'TARIFA CAMBIO/EXPORTACAO',
    'JUROS FCO', 'JUROS/ENCARGOS', 'JUROS FORNECEDORES'
}

DESP_PESSOAL_ATIVO = {'IRPF', 'TERRENO LUZIMANGUES', 'INSTALACAO/MONTAGEM ESCRITORIO 505 SUL PALMAS TO'}

# VOCÊ DEVE ADICIONAR AQUI OS NOMES DOS CUSTOS OPERACIONAIS COMO SAEM DO SEU SISTEMA
DESP_CUSTOS_OPERACIONAIS = {
    'ARMAZENAGEM', 'SECAGEM', 'FUMIGACAO', 'CLASSIFICACAO', 'CUSTO OPERACIONAL'
}

RECEITA_CATEGORIA = {
    'FINANCEIRA': 'Rendimentos Financeiros',
    'RENDIMETO FINANCEIRO': 'Rendimentos Financeiros',
    'AJUSTE NDF': 'Resultado NDF',
    'ENTRADAS DIVERSAS': 'Entradas Diversas',
    'REPRESENTACAO': 'Representação',
    'VARIACAO CAMBIAL NF VENDA': 'Variação Cambial',
    'AJUSTE': 'Ajustes'
}

# --- BUSCADORES INTELIGENTES (Evitam KeyError) ---
def _ajustar_cabecalho(df):
    """Procura a linha correta do cabeçalho caso o sistema exporte com linhas em branco no topo"""
    if df.empty: return df
    for i in range(min(15, len(df))):
        valores = [str(x).upper() for x in df.iloc[i].values]
        if any('VALOR' in v for v in valores) or any('DATA' in v or 'MÊS' in v or 'MES' in v for v in valores):
            df.columns = df.iloc[i]
            df = df.iloc[i+1:].reset_index(drop=True)
            df.columns = [str(c).strip() for c in df.columns]
            return df
    # Fallback
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _encontrar_col(df, possiveis_nomes):
    """Encontra a coluna mesmo que o sistema mude o nome ligeiramente"""
    col_map = {str(c).strip().upper(): c for c in df.columns}
    for p in possiveis_nomes:
        if p.upper() in col_map: return col_map[p.upper()]
    for c in df.columns:
        c_upper = str(c).upper()
        for p in possiveis_nomes:
            if p.upper() in c_upper: return c
    return None

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(arquivo='DASHBOARD.xlsx'):
    xls = pd.read_excel(arquivo, sheet_name=None, header=None)
    
    raw_l = xls.get('BD_LUCRO', pd.DataFrame())
    raw_l = _ajustar_cabecalho(raw_l)
        
    raw_dc = xls.get('BD_DESP_COMPL', pd.DataFrame())
    if raw_dc.empty:
        raw_dc = xls.get('BD_DESP', pd.DataFrame()) # Fallback automático
    raw_dc = _ajustar_cabecalho(raw_dc)

    raw_r = xls.get('BD_REC_FIN', pd.DataFrame())
    raw_r = _ajustar_cabecalho(raw_r)
    
    return _limpar_lucro(raw_l), _limpar_desp_compl(raw_dc), _limpar_rec_fin(raw_r)

# --- LIMPEZAS ---
def _limpar_lucro(df):
    if df.empty: return df
    df = df.copy()
    
    col_emp = _encontrar_col(df, ['EMPRESA', 'FILIAL'])
    col_prod = _encontrar_col(df, ['PRODUTO'])
    col_cli = _encontrar_col(df, ['CLIENTE'])
    col_mes = _encontrar_col(df, ['MÊS', 'MES', 'DATA'])
    
    for col in [col_emp, col_prod, col_cli]:
        if col and col in df.columns:
            df = df[~df[col].astype(str).str.upper().str.contains('TOTAL', na=False)]
            
    if col_mes:
        df['Mês'] = pd.to_datetime(df[col_mes], errors='coerce', dayfirst=True)
        df['Ano'] = df['Mês'].dt.year.fillna(2025).astype(int)
    else:
        df['Mês'] = pd.to_datetime('today')
        df['Ano'] = 2025
        
    df = df[df['Ano'].isin([2024, 2025, 2026])]
    
    if col_emp:
        df['Empresa'] = df[col_emp].map(MAPA_EMPRESAS).fillna(df[col_emp])
        
    colunas_fin = ['Lucro Bruto', 'Total Frete', 'Impostos', 'Comissão', 'Lucro Líq.', 'Peso Kg', 'Sacas/Ton']
    for c_name in colunas_fin:
        col_real = _encontrar_col(df, [c_name])
        if col_real:
            df[c_name] = pd.to_numeric(df[col_real], errors='coerce').fillna(0)
        else:
            df[c_name] = 0.0 
            
    df['Mês_Filtro'] = df['Mês'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['MesNum'] = df['Mês'].dt.month.fillna(0).astype(int)
    df['Contrato_Aberto'] = df['Lucro Bruto'] == 0
        
    return df.reset_index(drop=True)

def _limpar_desp_compl(df):
    if df.empty: return df
    df = df.copy()
    
    col_emp = _encontrar_col(df, ['EMPRESA', 'FILIAL'])
    if col_emp:
        df = df[df[col_emp].astype(str).str.strip().str.upper() != 'TOTAL']
        df = df[df[col_emp].notna()]
        df['Empresa'] = df[col_emp].map(MAPA_EMPRESAS).fillna(df[col_emp])
        
    col_data = _encontrar_col(df, ['DATAPAGTO', 'DATA PAGTO', 'DATA', 'MÊS', 'MES', 'VENCIMENTO'])
    if col_data:
        df['_data'] = pd.to_datetime(df[col_data], errors='coerce', dayfirst=True)
    else:
        df['_data'] = pd.to_datetime('today')
        
    df['Ano'] = df['_data'].dt.year.fillna(2025).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    
    col_val = _encontrar_col(df, ['VALORPAGOR$', 'VALOR PAGO', 'VALOR', 'R$', 'TOTAL'])
    if col_val:
        df['Valor'] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
    else:
        df['Valor'] = 0.0
        
    df = df[df['Valor'].abs() > 0]
    
    col_cat = _encontrar_col(df, ['DESCRICAOPLANOCONTAS', 'PLANO DE CONTAS', 'ITEM', 'DESCRICAO', 'CATEGORIA'])
    if col_cat:
        df['Item'] = df[col_cat].astype(str).str.strip()
    else:
        df['Item'] = 'OUTROS'
    
    def _classificar(item):
        s = item.upper()
        if any(i in s for i in DESP_COMPL_IGNORAR): return 'IGNORAR'
        if any(i in s for i in DESP_RESULTADO_FINANCEIRO): return 'FINANCEIRO'
        if any(i in s for i in DESP_PESSOAL_ATIVO): return 'PESSOAL_ATIVO'
        if any(i in s for i in DESP_CUSTOS_OPERACIONAIS): return 'CUSTO_OP'
        return 'ADMIN'
        
    df['Categoria_Desp'] = df['Item'].apply(_classificar)
    df['Eh_Desp_Admin'] = df['Categoria_Desp'] == 'ADMIN'
    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    return df.reset_index(drop=True)

def _limpar_rec_fin(df):
    if df.empty: return pd.DataFrame(columns=['Empresa','Ano','MesNum','Mês_Filtro','Item','Categoria','Valor'])
    df = df.copy()
    
    col_data = _encontrar_col(df, ['DATAPAGTO', 'DATA PAGTO', 'DATA', 'MÊS', 'MES', 'VENCIMENTO'])
    if col_data:
        df['_data'] = pd.to_datetime(df[col_data], errors='coerce', dayfirst=True)
    else:
        df['_data'] = pd.to_datetime('today')
        
    df['Ano'] = df['_data'].dt.year.fillna(2025).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    
    col_val = _encontrar_col(df, ['VALORPAGOR$', 'VALOR PAGO', 'VALOR', 'R$', 'TOTAL'])
    if col_val:
        df['Valor'] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
    else:
        df['Valor'] = 0.0
        
    df = df[df['Valor'] > 0]
    
    col_cat = _encontrar_col(df, ['DESCRICAOPLANOCONTAS', 'PLANO DE CONTAS', 'ITEM', 'DESCRICAO', 'CATEGORIA'])
    if col_cat:
        df['Item'] = df[col_cat].astype(str).str.strip()
    else:
        df['Item'] = 'OUTRAS RECEITAS'
    
    df['Categoria'] = df['Item'].map(RECEITA_CATEGORIA).fillna('Outras Receitas')
    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    return df.reset_index(drop=True)

# --- CALCULO E AGREGAÇÕES ---
def calcular_kpis(df_l, df_d, df_r=None):
    def s(df, col): return df[col].sum() if (not df.empty and col in df.columns) else 0
    
    df_f = df_l[~df_l['Contrato_Aberto']].copy() if (not df_l.empty and 'Contrato_Aberto' in df_l.columns) else df_l.copy()
    
    rb = s(df_f, 'Lucro Bruto')
    frt = s(df_f, 'Total Frete')
    imp = s(df_f, 'Impostos')
    com = s(df_f, 'Comissão')
    llc = s(df_f, 'Lucro Líq.')
    sac = s(df_f, 'Sacas/Ton')
    nc = len(df_f)
    
    custo_op = 0.0
    if not df_d.empty and 'Categoria_Desp' in df_d.columns:
        custo_op = df_d[df_d['Categoria_Desp'] == 'CUSTO_OP']['Valor'].sum()

    lop = rb - frt - imp - com - custo_op
    
    kg_total = s(df_l, 'Peso Kg')
    sac_total = s(df_l, 'Sacas/Ton')
    
    da = df_d[df_d['Eh_Desp_Admin']]['Valor'].sum() if (not df_d.empty and 'Eh_Desp_Admin' in df_d.columns) else 0
    rec_fin_total = df_r['Valor'].sum() if (df_r is not None and not df_r.empty and 'Valor' in df_r.columns) else 0.0
    
    llf = lop - da + rec_fin_total
    
    return dict(
        receita_bruta=rb, frete=frt, impostos_venda=imp, comissao=com, custo_operacional=custo_op,
        lucro_operacional=lop, despesas_admin=da, receita_financeira=rec_fin_total,
        lucro_liquido_final=llf,
        margem_bruta=llc / rb * 100 if rb else 0,
        margem_op=lop / rb * 100 if rb else 0,
        margem_liq=llf / rb * 100 if rb else 0,
        indice_desp=da / rb * 100 if rb else 0,
        n_contratos=len(df_l), peso_total=kg_total, sacas_total=sac_total,
        ticket_medio=rb / nc if nc else 0,
        lucro_por_saca=llf / sac if sac else 0,
    )

def _filtrar_df(df, ano, mes):
    if df is None or df.empty: return pd.DataFrame()
    m = pd.Series([True] * len(df), index=df.index)
    if 'Ano' in df.columns: m &= df['Ano'] == ano
    if 'MesNum' in df.columns: m &= df['MesNum'] == mes
    return df[m].copy()

def _filtrar_df_meses(df, ano, meses):
    if df is None or df.empty: return pd.DataFrame()
    m = pd.Series([True] * len(df), index=df.index)
    if 'Ano' in df.columns: m &= df['Ano'] == ano
    if 'MesNum' in df.columns: m &= df['MesNum'].isin(meses)
    return df[m].copy()

def mensal_por_ano(df_l, df_d, df_r=None):
    nomes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    anos  = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2025, 2026]
    rows  = []
    for mi, nome in enumerate(nomes, 1):
        row = {'Mês': nome, 'MesNum': mi}
        for ano in anos:
            lf = _filtrar_df(df_l, ano, mi)
            dd = _filtrar_df(df_d, ano, mi)
            dr = _filtrar_df(df_r, ano, mi) if df_r is not None else None
            k  = calcular_kpis(lf, dd, dr)
            row[f'Receita_{ano}']   = k['receita_bruta']
            row[f'Lucro_Op_{ano}']  = k['lucro_operacional']
            row[f'Lucro_Liq_{ano}'] = k['lucro_liquido_final']
            row[f'Desp_{ano}']      = k['despesas_admin']
            row[f'RecFin_{ano}']    = k['receita_financeira']
        rows.append(row)
    return pd.DataFrame(rows)

def trimestral_por_ano(df_l, df_d, df_r=None):
    anos  = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2025, 2026]
    trims = [('T1',[1,2,3]),('T2',[4,5,6]),('T3',[7,8,9]),('T4',[10,11,12])]
    rows  = []
    for trim_label, meses in trims:
        row = {'Trimestre': trim_label}
        for ano in anos:
            lf = _filtrar_df_meses(df_l, ano, meses)
            dd = _filtrar_df_meses(df_d, ano, meses)
            dr = _filtrar_df_meses(df_r, ano, meses) if df_r is not None else None
            k  = calcular_kpis(lf, dd, dr)
            row[f'Receita_{ano}']   = k['receita_bruta']
            row[f'Lucro_Op_{ano}']  = k['lucro_operacional']
            row[f'Lucro_Liq_{ano}'] = k['lucro_liquido_final']
            row[f'Desp_{ano}']      = k['despesas_admin']
        rows.append(row)
    return pd.DataFrame(rows)

def por_produto_ano(df_l):
    anos = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2025, 2026]
    produtos = sorted(df_l['Produto'].dropna().unique()) if 'Produto' in df_l.columns else []
    rows = []
    for prod in produtos:
        row = {'Produto': prod}
        for ano in anos:
            lp = df_l[(df_l['Ano'] == ano) & (df_l['Produto'] == prod)]
            lp_f = lp[~lp['Contrato_Aberto']] if 'Contrato_Aberto' in lp.columns else lp
            row[f'LB_{ano}'] = lp_f['Lucro Bruto'].sum() if 'Lucro Bruto' in lp_f.columns else 0
            row[f'LL_{ano}'] = lp_f['Lucro Líq.'].sum() if 'Lucro Líq.' in lp_f.columns else 0
            row[f'KG_{ano}'] = lp['Peso Kg'].sum() if 'Peso Kg' in lp.columns else 0
            row[f'SC_{ano}'] = lp['Sacas/Ton'].sum() if 'Sacas/Ton' in lp.columns else 0
            row[f'NC_{ano}'] = len(lp)
        rows.append(row)
    return pd.DataFrame(rows)