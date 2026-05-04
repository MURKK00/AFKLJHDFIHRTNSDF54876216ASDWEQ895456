import pandas as pd
import streamlit as st

MAPA_EMPRESAS = {
    'BC_MATRIZ': 'Bela Cereais Matriz',
    'BC_FILIAL': 'Bela Cereais Filial',
    'MM':        'MM Comercio de Grãos',
}

# --- LISTAS DE CLASSIFICAÇÃO CONTÁBIL ---

# IGNORADOS NAS DESPESAS (Fluxo de Caixa E Custos já embutidos no CMV/Custo Operacional)
DESP_COMPL_IGNORAR = {
    'TRANSFERENCIA ENTRE CONTAS', 'FORNECEDORES MERCADORIA', 'EMPRESAS', 'CAPITAL GIRO', 
    'MUTUO SOCIO', 'ADIANTAMENTOS FORNECEDORES', 'IMOVEIS', 'CONSORCIO', 
    'COMISSÃO CONTRATOS (CORRETORA)', 'FRETE (ADTO/SALDO)', 'COMISSAO CONTRATO', 
    'CLIENTES MERCADORIAS', 'ADIANTAMENTOS CLIENTES', 'TRANSFERENCIA',
    'COMPRA DE MERCADORIA', 'PAGAMENTO FORNECEDOR', 'APLICACAO FINANCEIRA',
    # CORREÇÃO DO ERRO DA OUTRA IA: Estes custos já estão cobertos ou deduzidos do Lucro Bruto contábil
    'FETHAB', 'TERCEIROS', 'BENEFICIAMENTO DE GRÃOS', 'BENEFICIAMENTO DE GRAOS',
    'ARMAZENAGEM', 'SECAGEM', 'FUMIGACAO', 'CLASSIFICACAO', 'CUSTO OPERACIONAL'
}

# DESPESAS FINANCEIRAS (Serão descontadas das Receitas Extras)
DESP_RESULTADO_FINANCEIRO = {
    'AJUSTE NDF', 'JUROS EMPRESTIMOS', 'JUROS S/ MUTUO SOCIO', 'IOF', 'TARIFA BANCARIA',
    'TAXA FINANCIAMENTO', 'JUROS DE ANTECIPACAO', 'TARIFA CAMBIO/EXPORTACAO',
    'JUROS FCO', 'JUROS/ENCARGOS', 'JUROS FORNECEDORES'
}

DESP_PESSOAL_ATIVO = {'IRPF', 'TERRENO LUZIMANGUES', 'INSTALACAO/MONTAGEM ESCRITORIO 505 SUL PALMAS TO'}

# IGNORADOS NAS RECEITAS (Fluxo de caixa puro)
REC_FIN_IGNORAR = {
    'TRANSFERENCIA ENTRE CONTAS', 'TRANSFERENCIA', 'CLIENTES MERCADORIAS', 'EMPRESAS', 
    'CAPITAL GIRO', 'MUTUO SOCIO', 'ADIANTAMENTOS CLIENTES', 'ADIANTAMENTOS FORNECEDORES', 
    'PAGAMENTO FORNECEDOR', 'FORNECEDORES MERCADORIA', 'APLICACAO FINANCEIRA'
}

# --- BUSCADORES INTELIGENTES ---
def _ajustar_cabecalho(df):
    if df.empty: return df
    for i in range(min(15, len(df))):
        valores = [str(x).upper() for x in df.iloc[i].values]
        if any('VALOR' in v for v in valores) or any('DATA' in v or 'MÊS' in v or 'MES' in v for v in valores) or any('LUCRO BRUTO' in v for v in valores):
            df.columns = df.iloc[i]
            df = df.iloc[i+1:].reset_index(drop=True)
            df.columns = [str(c).strip() for c in df.columns]
            return df
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _encontrar_col(df, possiveis_nomes):
    col_map = {str(c).strip().upper(): c for c in df.columns}
    for p in possiveis_nomes:
        if p.upper() in col_map: return col_map[p.upper()]
    for c in df.columns:
        c_upper = str(c).upper()
        for p in possiveis_nomes:
            if p.upper() in c_upper: return c
    return None

def _traduzir_data_br(serie):
    s = serie.astype(str).str.lower().str.strip()
    mapa_meses = {'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06',
                  'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'}
    for pt, num in mapa_meses.items():
        s = s.str.replace(pt, num, regex=False)
    return pd.to_datetime(s, errors='coerce', dayfirst=True, format='mixed')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(arquivo='DASHBOARD.xlsx'):
    xls = pd.read_excel(arquivo, sheet_name=None, header=None)
    
    raw_l = xls.get('BD_LUCRO', pd.DataFrame())
    raw_l = _ajustar_cabecalho(raw_l)
        
    raw_dc = xls.get('BD_DESP_COMPL', pd.DataFrame())
    if raw_dc.empty: raw_dc = xls.get('BD_DESP', pd.DataFrame())
    raw_dc = _ajustar_cabecalho(raw_dc)

    raw_r = xls.get('BD_REC_FIN', pd.DataFrame())
    raw_r = _ajustar_cabecalho(raw_r)
    
    return _limpar_lucro(raw_l), _limpar_desp_compl(raw_dc), _limpar_rec_fin(raw_r)

# --- LIMPEZAS E CONVERSÕES ---
def _limpar_lucro(df):
    if df.empty: return df
    df = df.copy()
    
    col_emp = _encontrar_col(df, ['EMPRESA', 'FILIAL'])
    col_mes = _encontrar_col(df, ['MÊS', 'MES', 'DATA'])
    
    if col_emp and col_emp in df.columns:
        df = df[~df[col_emp].astype(str).str.upper().str.contains('TOTAL', na=False)]
    
    if col_mes:
        df['Mês'] = _traduzir_data_br(df[col_mes])
        df['Ano'] = df['Mês'].dt.year.fillna(2025).astype(int)
    else:
        df['Mês'] = pd.to_datetime('today')
        df['Ano'] = 2025
        
    df = df[df['Ano'].isin([2024, 2025, 2026])]
    if col_emp: df['Empresa'] = df[col_emp].map(MAPA_EMPRESAS).fillna(df[col_emp])
        
    colunas_fin = ['Lucro Bruto', 'Total Frete', 'Impostos', 'Comissão', 'Lucro Líq.', 'Peso Kg', 'Sacas/Ton']
    for c_name in colunas_fin:
        col_real = _encontrar_col(df, [c_name])
        if col_real: df[c_name] = pd.to_numeric(df[col_real], errors='coerce').fillna(0)
        else: df[c_name] = 0.0 
            
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
    if col_data: df['_data'] = _traduzir_data_br(df[col_data])
    else: df['_data'] = pd.to_datetime('today')
        
    df['Ano'] = df['_data'].dt.year.fillna(2025).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    
    col_val = _encontrar_col(df, ['VALORPAGOR$', 'VALOR PAGO', 'VALOR', 'R$', 'TOTAL'])
    if col_val: df['Valor'] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
    else: df['Valor'] = 0.0
        
    df = df[df['Valor'].abs() > 0]
    
    col_cat = _encontrar_col(df, ['DESCRICAOPLANOCONTAS', 'PLANO DE CONTAS', 'ITEM', 'DESCRICAO', 'CATEGORIA'])
    df['Item'] = df[col_cat].astype(str).str.strip() if col_cat else 'OUTROS'
    
    def _classificar(item):
        s = item.upper()
        if any(i in s for i in DESP_COMPL_IGNORAR): return 'IGNORAR'
        if any(i in s for i in DESP_RESULTADO_FINANCEIRO): return 'FINANCEIRO'
        if any(i in s for i in DESP_PESSOAL_ATIVO): return 'PESSOAL_ATIVO'
        return 'ADMIN' 
        
    df['Categoria_Desp'] = df['Item'].apply(_classificar)
    df['Eh_Desp_Admin'] = df['Categoria_Desp'] == 'ADMIN'
    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    return df.reset_index(drop=True)

def _limpar_rec_fin(df):
    if df.empty: return pd.DataFrame(columns=['Empresa','Ano','MesNum','Mês_Filtro','Item','Categoria','Valor'])
    df = df.copy()
    
    col_emp = _encontrar_col(df, ['EMPRESA', 'FILIAL'])
    if col_emp:
        df = df[df[col_emp].astype(str).str.strip().str.upper() != 'TOTAL']
        df = df[df[col_emp].notna()]
        df['Empresa'] = df[col_emp].map(MAPA_EMPRESAS).fillna(df[col_emp])
    
    col_data = _encontrar_col(df, ['DATAPAGTO', 'DATA PAGTO', 'DATA', 'MÊS', 'MES', 'VENCIMENTO'])
    df['_data'] = _traduzir_data_br(df[col_data]) if col_data else pd.to_datetime('today')
    df['Ano'] = df['_data'].dt.year.fillna(2025).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    
    col_val = _encontrar_col(df, ['VALORPAGOR$', 'VALOR PAGO', 'VALOR', 'R$', 'TOTAL'])
    df['Valor'] = pd.to_numeric(df[col_val], errors='coerce').fillna(0) if col_val else 0.0
    df = df[df['Valor'] != 0]
    
    col_cat = _encontrar_col(df, ['DESCRICAOPLANOCONTAS', 'PLANO DE CONTAS', 'ITEM', 'DESCRICAO'])
    df['Item'] = df[col_cat].astype(str).str.strip() if col_cat else 'OUTRAS RECEITAS'
    
    def verificar_ignorado(item):
        s = item.upper()
        return any(i in s for i in REC_FIN_IGNORAR)
        
    df['IGNORADO'] = df['Item'].apply(verificar_ignorado)
    df = df[~df['IGNORADO']] 
    
    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    return df.reset_index(drop=True)

# --- MATEMÁTICA ALINHADA À DRE ---
def calcular_kpis(df_l, df_d, df_r=None):
    def s(df, col): return df[col].sum() if (not df.empty and col in df.columns) else 0
    
    df_f = df_l.copy()
    
    rb = s(df_f, 'Lucro Bruto')
    frt = s(df_f, 'Total Frete')
    imp = s(df_f, 'Impostos')
    com = s(df_f, 'Comissão')
    llc = s(df_f, 'Lucro Líq.')
    sac = s(df_f, 'Sacas/Ton')
    
    abertos = df_f['Contrato_Aberto'] if 'Contrato_Aberto' in df_f.columns else pd.Series(False, index=df_f.index)
    nc = len(df_f[~abertos]) 

    lop = rb - frt - imp - com
    
    kg_total = s(df_l, 'Peso Kg')
    sac_total = s(df_l, 'Sacas/Ton')
    
    da = df_d[df_d['Eh_Desp_Admin']]['Valor'].sum() if (not df_d.empty and 'Eh_Desp_Admin' in df_d.columns) else 0
    
    desp_fin = df_d[df_d['Categoria_Desp'] == 'FINANCEIRO']['Valor'].sum() if (not df_d.empty and 'Categoria_Desp' in df_d.columns) else 0
    rec_fin_bruta = df_r['Valor'].sum() if (df_r is not None and not df_r.empty and 'Valor' in df_r.columns) else 0.0
    rec_fin_liquida = rec_fin_bruta - desp_fin
    
    llf = lop - da + rec_fin_liquida
    
    return dict(
        receita_bruta=rb, frete=frt, impostos_venda=imp, comissao=com, custo_operacional=0,
        lucro_operacional=lop, despesas_admin=da, receita_financeira=rec_fin_liquida,
        lucro_liquido_final=llf,
        margem_bruta=llf / rb * 100 if rb else 0,
        margem_op=lop / rb * 100 if rb else 0,
        margem_liq=llf / rb * 100 if rb else 0,
        indice_desp=da / rb * 100 if rb else 0,
        n_contratos=len(df_l), peso_total=kg_total, sacas_total=sac_total,
        ticket_medio=rb / nc if nc else 0, lucro_por_saca=llf / sac if sac else 0,
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

def mensal_por_ano(df_l, df_d, df_r=None): return pd.DataFrame() 
def trimestral_por_ano(df_l, df_d, df_r=None): return pd.DataFrame()
def por_produto_ano(df_l): return pd.DataFrame()