# Análise de E-commerce Brasileiro — Olist

Pipeline de dados completo com análise de vendas, logística e 
satisfação de clientes de um marketplace brasileiro real.

## Tecnologias
- Python (pandas, SQLAlchemy) — ETL e limpeza de dados
- SQL Server — Modelagem dimensional (esquema estrela)
- Power BI — Dashboard executivo (em desenvolvimento)

## Dataset
Base de dados pública da Olist com ~100k pedidos reais (2016-2018).
Download: https://github.com/olist/work-at-olist-data

## Estrutura do Projeto
projeto-olist/<br><br>
├── notebooks/<br>
│   ├── 01_exploracao.py     # Análise exploratória das 9 tabelas<br>
│   ├── 02_limpeza.py        # Tratamento e padronização dos dados<br>
│   └── 03_carga_sql.py      # ETL para SQL Server (esquema estrela)<br><br>
├── sql/<br>
│   └── analises_negocio.sql # Queries de negócio (CTE, Window Functions)<br>
└── README.md<br>

## Principais Insights
- Faturamento total de R$ 15,8M em ~99k pedidos (2016-2018)
- Black Friday 2017: pico de +52% sobre outubro
- SP concentra 41% dos pedidos com menor frete e maior satisfação
- Correlação direta entre prazo de entrega e nota de avaliação
- Top vendedor fora de SP: Lauro de Freitas-BA com ticket médio de R$ 543

## Status
Em desenvolvimento — Fase 4 (Power BI) em andamento
