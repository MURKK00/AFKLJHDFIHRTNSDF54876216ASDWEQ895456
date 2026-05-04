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

# ── Itens a IGNORAR no BD_DESP_COMPL (fluxo de caixa / ativo / duplicata) ────
DESP_COMPL_IGNORAR = {
    'TRANSFERENCIA ENTRE CONTAS',
    'FORNECEDORES MERCADORIA',     # CMV — já capturado em BD_LUCRO
    'EMPRESAS',                    # transferência intercompany
    'CAPITAL GIRO',                # passivo financeiro
    'MUTUO SOCIO',                 # empréstimo sócio
    'ADIANTAMENTOS FORNECEDORES',  # ativo circulante
    'IMOVEIS',                     # ativo imobilizado
    'CONSORCIO',                   # ativo
    'COMISSÃO CONTRATOS (CORRETORA)',  # já em BD_LUCRO (Comissão)
    'FRETE (ADTO/SALDO)',          # já em BD_LUCRO (Total Frete)
    'COMISSAO CONTRATO',           # já em BD_LUCRO (Comissão)
    'CLIENTES MERCADORIAS',        # receita — lado errado
    'ADIANTAMENTOS CLIENTES',      # ativo circulante
    'TRANSFERENCIA',
}

# Itens financeiros que saem da despesa e são tratados no bloco financeiro
DESP_RESULTADO_FINANCEIRO = {
    'AJUSTE NDF',
    'JUROS EMPRESTIMOS',
    'JUROS S/ MUTUO SOCIO',
    'IOF',
    'TARIFA BANCARIA',
    'TAXA FINANCIAMENTO',
    'JUROS DE ANTECIPACAO',
    'TARIFA CAMBIO/EXPORTACAO',
    'JUROS FCO',
    'JUROS/ENCARGOS',
    'JUROS FORNECEDORES',
}

DESP_PESSOAL_ATIVO = {
    'IRPF',
    'TERRENO LUZIMANGUES',
    'INSTALACAO/MONTAGEM ESCRITORIO 505 SUL PALMAS TO',
}

# ── Itens do BD_REC_FIN que são receita P&L ────────────────────────────────
RECEITA_PL = {
    'FINANCEIRA',
    'RENDIMETO FINANCEIRO',   # nota: grafia do sistema tem erro intencional
    'AJUSTE NDF',             # lado receita do hedge
    'ENTRADAS DIVERSAS',
    'REPRESENTACAO',
    'VARIACAO CAMBIAL NF VENDA',
    'AJUSTE',
}

# Categorias de receita para exibição
RECEITA_CATEGORIA = {
    'FINANCEIRA':                'Rendimentos Financeiros',
    'RENDIMETO FINANCEIRO':      'Rendimentos Financeiros',
    'AJUSTE NDF':                'Resultado NDF',
    'ENTRADAS DIVERSAS':         'Entradas Diversas',
    'REPRESENTACAO':             'Representação',
    'VARIACAO CAMBIAL NF VENDA': 'Variação Cambial',
    'AJUSTE':                    'Ajustes',
}

# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(arquivo='DASHBOARD.xlsx'):
    """
    Retorna: (df_lucro, df_desp, df_rec_fin)

    df_desp  → BD_DESP_COMPL (preferencial) ou BD_DESP (fallback)
    df_rec_fin → BD_REC_FIN filtrado para itens de receita P&L
    """
    xls = pd.read_excel(arquivo, sheet_name=None, header=None)

    # ── BD_LUCRO ──────────────────────────────────────────────────────────────
    raw_l = xls.get('BD_LUCRO', pd.DataFrame())
    if not raw_l.empty:
        raw_l.columns = raw_l.iloc[0]
        raw_l = raw_l.iloc[1:].reset_index(drop=True)
        raw_l.columns = [str(c).strip() for c in raw_l.columns]

    # ── BD_DESP_COMPL (primário) ou BD_DESP (fallback) ────────────────────────
    raw_dc = xls.get('BD_DESP_COMPL', pd.DataFrame())
    if not raw_dc.empty:
        raw_dc.columns = raw_dc.iloc[0]
        raw_dc = raw_dc.iloc[1:].reset_index(drop=True)
        raw_dc.columns = [str(c).strip() for c in raw_dc.columns]
        df_desp = _limpar_desp_compl(raw_dc)
    else:
        # Fallback: BD_DESP legado
        raw_d = xls.get('BD_DESP', pd.DataFrame())
        if not raw_d.empty:
            raw_d.columns = raw_d.iloc[0]
            raw_d = raw_d.iloc[1:].reset_index(drop=True)
            raw_d.columns = [str(c).strip() for c in raw_d.columns]
        df_desp = _limpar_desp_legado(raw_d)

    # ── BD_REC_FIN ─────────────────────────────────────────────────────────────
    raw_r = xls.get('BD_REC_FIN', pd.DataFrame())
    if not raw_r.empty:
        raw_r.columns = raw_r.iloc[0]
        raw_r = raw_r.iloc[1:].reset_index(drop=True)
        raw_r.columns = [str(c).strip() for c in raw_r.columns]
    df_rec_fin = _limpar_rec_fin(raw_r)

    return _limpar_lucro(raw_l), df_desp, df_rec_fin


# ── Limpeza BD_LUCRO ──────────────────────────────────────────────────────────
def _limpar_lucro(df):
    if df.empty:
        return df
    df = df.copy()

    for col in ['Empresa', 'Produto', 'Cliente']:
        if col in df.columns:
            df = df[~df[col].astype(str).str.upper().str.contains('TOTAL', na=False)]

    df['Mês'] = pd.to_datetime(df.get('Mês'), errors='coerce')
    df['Ano'] = _extrair_ano(df)
    df = df[df['Ano'].isin([2025, 2026])]

    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])

    for col in ['Lucro Bruto', 'Total Frete', 'Impostos', 'Comissão',
                'Lucro Líq.', 'Peso Kg', 'Sacas/Ton']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Mês_Filtro'] = df['Mês'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['MesNum']     = df['Mês'].dt.month.fillna(0).astype(int)
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')

    df['Mercado'] = df['Cliente'].apply(
        lambda x: 'Exportação'
        if str(x).strip().upper() in {c.upper() for c in EXP_CLIENTS}
        else 'Mercado Interno')

    # Contratos sem Lucro Bruto = compras em aberto (marcados mas não excluídos)
    if 'Lucro Bruto' in df.columns:
        df['Contrato_Aberto'] = df['Lucro Bruto'] == 0
    else:
        df['Contrato_Aberto'] = False

    cols_fin = [c for c in ['Lucro Bruto', 'Peso Kg'] if c in df.columns]
    if cols_fin:
        df = df[df[cols_fin].abs().sum(axis=1) > 0]

    return df.reset_index(drop=True)


# ── Limpeza BD_DESP_COMPL (novo, preferencial) ───────────────────────────────
def _limpar_desp_compl(df):
    if df.empty:
        return df
    df = df.copy()

    # Remove linha de totais do sistema
    if 'Empresa' in df.columns:
        df = df[df['Empresa'].astype(str).str.strip().str.upper() != 'TOTAL']
        df = df[df['Empresa'].notna()]

    # Data vem de DataPagto neste formato
    data_col = 'DataPagto' if 'DataPagto' in df.columns else 'Mês'
    df['_data'] = pd.to_datetime(df[data_col], errors='coerce')
    df['Ano']    = df['_data'].dt.year.fillna(2026).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    df = df[df['Ano'].isin([2025, 2026])]

    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])

    # Coluna de valor
    val_col = 'ValorPagoR' if 'ValorPagoR' in df.columns else 'Valor'
    df['Valor'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
    df = df[df['Valor'].abs() > 0]

    # Coluna de item/categoria
    cat_col = 'DescricaoPlanoContas' if 'DescricaoPlanoContas' in df.columns else 'Item'
    df['Item'] = df[cat_col].astype(str).str.strip()
    df = df[df['Item'].notna() & (df['Item'] != '') & (df['Item'] != 'nan')]

    # Classificação
    def _classificar(item):
        s = item.upper()
        if s in {i.upper() for i in DESP_COMPL_IGNORAR}:     return 'IGNORAR'
        if s in {i.upper() for i in DESP_RESULTADO_FINANCEIRO}: return 'FINANCEIRO'
        if s in {i.upper() for i in DESP_PESSOAL_ATIVO}:     return 'PESSOAL_ATIVO'
        return 'ADMIN'

    df['Categoria_Desp'] = df['Item'].apply(_classificar)
    df['Eh_Desp_Admin']  = df['Categoria_Desp'] == 'ADMIN'

    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')

    return df.reset_index(drop=True)


# ── Limpeza BD_DESP legado (fallback) ─────────────────────────────────────────
def _limpar_desp_legado(df):
    if df.empty:
        return df
    df = df.copy()

    if 'Item' in df.columns:
        df = df[df['Item'].notna()]
        df = df[df['Item'].astype(str).str.strip() != '']
        df = df[df['Item'].astype(str).str.strip() != 'nan']
        df = df[~df['Item'].astype(str).str.upper().str.contains('TOTAL', na=False)]

    df['Mês'] = pd.to_datetime(df.get('Mês'), errors='coerce')
    df['Ano'] = _extrair_ano(df)
    df = df[df['Ano'].isin([2025, 2026])]

    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])

    if 'Valor' in df.columns:
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df = df[df['Valor'].abs() > 0]

    ITENS_EXCLUIR = (
        {'JUROS EMPRESTIMOS','JUROS S/ MUTUO SOCIO','IOF','TARIFA BANCARIA',
         'TAXA FINANCIAMENTO','AJUSTE NDF','TARIFA CAMBIO/EXPORTACAO',
         'JUROS/ENCARGOS','JUROS DE ANTECIPACAO','IRPF',
         'TERRENO LUZIMANGUES','INSTALACAO/MONTAGEM ESCRITORIO 505 SUL PALMAS TO',
         'COMISSAO CONTRATO'}
    )

    def _cls(item):
        s = str(item).upper().strip()
        if s in {i.upper() for i in ITENS_EXCLUIR}: return 'NAO_ADMIN'
        return 'ADMIN'

    if 'Item' in df.columns:
        df['Categoria_Desp'] = df['Item'].apply(_cls)
        df['Eh_Desp_Admin']  = df['Categoria_Desp'] == 'ADMIN'
    else:
        df['Categoria_Desp'] = 'ADMIN'
        df['Eh_Desp_Admin']  = True

    df['_data']      = df['Mês']
    df['MesNum']     = df['Mês'].dt.month.fillna(0).astype(int)
    df['Mês_Filtro'] = df['Mês'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')

    return df.reset_index(drop=True)


# ── Limpeza BD_REC_FIN ────────────────────────────────────────────────────────
def _limpar_rec_fin(df):
    if df.empty:
        return pd.DataFrame(columns=[
            'Empresa','Ano','MesNum','Mês_Filtro','Trimestre',
            'Item','Categoria','Valor'
        ])
    df = df.copy()

    # Remove totais
    if 'Empresa' in df.columns:
        df = df[df['Empresa'].astype(str).str.strip().str.upper() != 'TOTAL']
        df = df[df['Empresa'].notna()]

    data_col = 'DataPagto' if 'DataPagto' in df.columns else 'Mês'
    df['_data'] = pd.to_datetime(df[data_col], errors='coerce')
    df['Ano']    = df['_data'].dt.year.fillna(2026).astype(int)
    df['MesNum'] = df['_data'].dt.month.fillna(0).astype(int)
    df = df[df['Ano'].isin([2025, 2026])]

    if 'Empresa' in df.columns:
        df['Empresa'] = df['Empresa'].map(MAPA_EMPRESAS).fillna(df['Empresa'])

    val_col = 'ValorPagoR' if 'ValorPagoR' in df.columns else 'Valor'
    df['Valor'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
    df = df[df['Valor'] > 0]

    cat_col = 'DescricaoPlanoContas' if 'DescricaoPlanoContas' in df.columns else 'Item'
    df['Item'] = df[cat_col].astype(str).str.strip()

    # Filtra somente itens P&L
    df = df[df['Item'].isin(RECEITA_PL)]

    df['Categoria']  = df['Item'].map(RECEITA_CATEGORIA).fillna('Outros')
    df['Mês_Filtro'] = df['_data'].dt.strftime('%m/%Y').fillna('Sem Data')
    df['Trimestre']  = df['MesNum'].map(
        {1:'T1',2:'T1',3:'T1',4:'T2',5:'T2',6:'T2',
         7:'T3',8:'T3',9:'T3',10:'T4',11:'T4',12:'T4'}).fillna('T?')

    return df.reset_index(drop=True)


# ── Extrator de ano ───────────────────────────────────────────────────────────
def _extrair_ano(df):
    if 'Ano' in df.columns:
        s = pd.to_numeric(df['Ano'], errors='coerce')
        mask = s.isna() | ~s.between(2020, 2035)
        if 'Mês' in df.columns:
            s[mask] = df.loc[mask, 'Mês'].apply(
                lambda x: x.year if hasattr(x, 'year') else 2026)
        return s.fillna(2026).astype(int)
    if 'Mês' in df.columns:
        return df['Mês'].apply(
            lambda x: x.year if hasattr(x, 'year') else 2026).astype(int)
    return pd.Series([2026] * len(df), index=df.index)


# ── KPIs ──────────────────────────────────────────────────────────────────────
def calcular_kpis(df_l, df_d, df_r=None):
    """
    df_l  : BD_LUCRO filtrado
    df_d  : BD_DESP_COMPL (ou legado) filtrado
    df_r  : BD_REC_FIN filtrado (opcional)
    """
    def s(df, col):
        return df[col].sum() if (not df.empty and col in df.columns) else 0

    # ── Contratos fechados (para métricas financeiras) ─────────────────────
    if not df_l.empty and 'Contrato_Aberto' in df_l.columns:
        df_f = df_l[~df_l['Contrato_Aberto']].copy()
    else:
        df_f = df_l.copy()

    rb  = s(df_f, 'Lucro Bruto')
    frt = s(df_f, 'Total Frete')
    imp = s(df_f, 'Impostos')
    com = s(df_f, 'Comissão')
    llc = s(df_f, 'Lucro Líq.')
    sac = s(df_f, 'Sacas/Ton')
    nc  = len(df_f)
    lop = rb - frt - imp - com

    # ── Volume total (inclui contratos abertos — mostra carteira completa) ──
    nc_total  = len(df_l)
    kg_total  = s(df_l, 'Peso Kg')
    sac_total = s(df_l, 'Sacas/Ton')
    n_abertos = int(df_l['Contrato_Aberto'].sum()) if 'Contrato_Aberto' in df_l.columns else 0

    # ── Despesas administrativas (apenas itens ADMIN) ──────────────────────
    if not df_d.empty and 'Eh_Desp_Admin' in df_d.columns:
        da = df_d[df_d['Eh_Desp_Admin']]['Valor'].sum()
    else:
        da = s(df_d, 'Valor')

    # Resultado financeiro via despesas (juros empréstimos etc.)
    desp_fin = 0.0
    if not df_d.empty and 'Categoria_Desp' in df_d.columns:
        desp_fin = df_d[df_d['Categoria_Desp'] == 'FINANCEIRO']['Valor'].sum()

    # ── Receitas financeiras e outros (BD_REC_FIN) ─────────────────────────
    rec_fin_total = 0.0
    rec_fin_det   = {}
    ajuste_ndf_rec = 0.0

    if df_r is not None and not df_r.empty and 'Valor' in df_r.columns:
        # NDF líquido = receita NDF - despesa NDF
        ajuste_ndf_rec = df_r[df_r['Item'] == 'AJUSTE NDF']['Valor'].sum()
        ajuste_ndf_desp = desp_fin  # já somado acima separadamente
        # Na prática usamos o total bruto de receitas e tratamos NDF na exibição

        for cat in df_r['Categoria'].unique():
            rec_fin_det[cat] = df_r[df_r['Categoria'] == cat]['Valor'].sum()

        rec_fin_total = df_r['Valor'].sum()

    # NDF líquido = receita - despesa NDF
    ndf_despesa = 0.0
    if not df_d.empty and 'Item' in df_d.columns:
        ndf_despesa = df_d[df_d['Item'].str.upper() == 'AJUSTE NDF']['Valor'].sum()
    ndf_liquido = ajuste_ndf_rec - ndf_despesa

    llf = lop - da + rec_fin_total

    return dict(
        # P&L contratos
        receita_bruta=rb,
        frete=frt,
        impostos_venda=imp,
        comissao=com,
        lucro_liq_contr=llc,
        lucro_operacional=lop,
        # Despesas
        despesas_admin=da,
        despesas_financeiras=desp_fin,
        # Receitas financeiras / outros
        receita_financeira=rec_fin_total,
        receita_financeira_det=rec_fin_det,
        ndf_liquido=ndf_liquido,
        # Resultado final
        lucro_liquido_final=llf,
        # Margens (base: receita bruta dos contratos)
        margem_bruta=llc / rb * 100     if rb else 0,
        margem_op=lop / rb * 100        if rb else 0,
        margem_liq=llf / rb * 100       if rb else 0,
        indice_desp=da / rb * 100       if rb else 0,
        # Operacionais
        n_contratos=nc_total,
        n_contratos_fechados=nc,
        n_contratos_abertos=n_abertos,
        peso_total=kg_total,
        sacas_total=sac_total,
        ticket_medio=rb / nc            if nc else 0,
        lucro_por_saca=llf / sac        if sac else 0,
    )


# ── Funções de agregação temporal ─────────────────────────────────────────────
def mensal_por_ano(df_l, df_d, df_r=None):
    nomes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    anos  = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    rows  = []
    for mi, nome in enumerate(nomes, 1):
        row = {'Mês': nome, 'MesNum': mi}
        for ano in anos:
            lf = df_l[(df_l['Ano'] == ano) & (df_l['MesNum'] == mi)]
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
    anos  = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    trims = [('T1',[1,2,3]),('T2',[4,5,6]),('T3',[7,8,9]),('T4',[10,11,12])]
    rows  = []
    for trim_label, meses in trims:
        row = {'Trimestre': trim_label}
        for ano in anos:
            lf = df_l[(df_l['Ano'] == ano) & (df_l['MesNum'].isin(meses))]
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
    anos    = sorted(df_l['Ano'].unique()) if 'Ano' in df_l.columns else [2026]
    produtos = sorted(df_l['Produto'].dropna().unique())
    rows = []
    for prod in produtos:
        row = {'Produto': prod}
        for ano in anos:
            lp = df_l[(df_l['Ano'] == ano) & (df_l['Produto'] == prod)]
            lp_f = lp[~lp['Contrato_Aberto']] if 'Contrato_Aberto' in lp.columns else lp
            row[f'LB_{ano}'] = lp_f['Lucro Bruto'].sum()
            row[f'LL_{ano}'] = lp_f['Lucro Líq.'].sum()
            row[f'KG_{ano}'] = lp['Peso Kg'].sum()
            row[f'SC_{ano}'] = lp['Sacas/Ton'].sum()
            row[f'NC_{ano}'] = len(lp)
        rows.append(row)
    return pd.DataFrame(rows)


# ── Helpers internos ──────────────────────────────────────────────────────────
def _filtrar_df(df, ano, mes):
    if df is None or df.empty:
        return pd.DataFrame()
    m = pd.Series([True] * len(df), index=df.index)
    if 'Ano' in df.columns:    m &= df['Ano'] == ano
    if 'MesNum' in df.columns: m &= df['MesNum'] == mes
    return df[m].copy()


def _filtrar_df_meses(df, ano, meses):
    if df is None or df.empty:
        return pd.DataFrame()
    m = pd.Series([True] * len(df), index=df.index)
    if 'Ano' in df.columns:    m &= df['Ano'] == ano
    if 'MesNum' in df.columns: m &= df['MesNum'].isin(meses)
    return df[m].copy()