# 🌾 Dashboard Bela Cereais

Dashboard executivo para comercialização de grãos — Grupo Bela Cereais.

## Estrutura

```
bela_cereais/
├── app.py                  # Entrada principal
├── requirements.txt
├── DASHBOARD.xlsx          # ← coloque seu arquivo aqui
├── logo.png                # ← opcional
├── utils/
│   ├── data_loader.py      # Carregamento e cálculo dos KPIs
│   └── formatters.py       # CSS, cards e formatação
└── pages/
    ├── dashboard.py        # Aba Dashboard (KPIs + produtos + clientes)
    ├── dre.py              # Aba DRE com waterfall e margens
    ├── graficos.py         # Aba Gráficos (Plotly)
    ├── contratos.py        # Aba Contratos (tabela detalhada)
    ├── despesas.py         # Aba Despesas (categorização automática)
    └── executivo.py        # Aba Resumo Executivo (para investidores)
```

## Instalação

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Formato esperado do DASHBOARD.xlsx

### Aba `BD_LUCRO`
| Empresa | Mês | Contrato V | Contrato C | Fornecedor | Cliente | Produto | Peso Kg | Sacas/Ton | Lucro Bruto | Total Frete | Impostos | Comissão | Lucro Líq. |

### Aba `BD_DESP`
| Empresa | Mês | Item | Valor |

### Aba `HIST. MENSAL` (a partir da linha 10)
| Mês | Qtde Contratos | Lucro Bruto | Luc. Liq. Oper. | Desp. Admin. | Lucro Líq. Final | Mg. Bruta % | Mg. Líq. % | Resultado | Var. Mês Ant. |

## Códigos de empresa no Excel
- `BC_MATRIZ` → Bela Cereais Matriz
- `BC_FILIAL`  → Bela Cereais Filial
- `MM`         → MM Comercio de Grãos
