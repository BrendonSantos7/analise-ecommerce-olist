<div align="center"> <img src="https://img.shields.io/badge/STATUS-CONCLUÍDO-22c55e?style=for-the-badge" />
Análise de E-commerce Brasileiro — Olist
Pipeline de dados completo: da extração ao dashboard executivo interativo
Python · SQL Server · Power BI · DAX · Git
<br>

Mostrar Imagem Mostrar Imagem Mostrar Imagem Mostrar Imagem

</div>
📌 Sobre o Projeto

Este projeto foi desenvolvido do zero como portfólio prático para demonstrar as competências mais cobradas pelo mercado de dados em São Paulo — sem dados sintéticos, sem tutoriais prontos, sem atalhos.

A Olist é o maior marketplace de departamentos do Brasil, conectando pequenos lojistas a grandes redes de e-commerce. O projeto simula o trabalho de um Analista de Dados respondendo perguntas reais de negócio usando dados de ~100 mil pedidos realizados entre 2016 e 2018.

O que diferencia este projeto: pipeline ETL completo do zero — modelagem dimensional (esquema estrela) — SQL avançado com CTEs e Window Functions — dashboard executivo com design profissional, tooltips interativos e navegação entre páginas — tudo com dados 100% reais de uma empresa brasileira.

❓ Perguntas de Negócio Respondidas
#	Pergunta	Onde ver
1	Qual é a sazonalidade das vendas? Existe período de pico?	Visão Geral
2	Quais categorias geram mais receita e maior satisfação?	Produtos
3	O frete e prazo de entrega variam entre regiões do Brasil?	Logística
4	Quais vendedores merecem destaque? Quais precisam de atenção?	Vendedores
5	Existe correlação entre prazo de entrega e satisfação do cliente?	Logística
6	Como foi o crescimento acumulado do faturamento ao longo do tempo?	Visão Geral
🛠️ Stack Tecnológica
Tecnologia	Versão	Uso no projeto
Python + pandas	3.12	Extração, limpeza e transformação dos dados (ETL)
SQLAlchemy + pyodbc	latest	Conexão Python → SQL Server para carga automatizada
SQL Server + T-SQL	2022	Modelagem dimensional, queries analíticas, Views
CTEs + Window Functions	—	Ranking, acumulado, variação MoM/YoY, LAG/LEAD
Power BI Desktop	latest	Modelagem, dashboard executivo interativo
DAX	—	15 medidas: KPIs, inteligência de tempo, YoY, MoM, YTD
Git + GitHub	—	Versionamento e publicação do portfólio
🔄 Pipeline de Dados
9 CSVs brutos — dataset real Olist (100k pedidos)
        │
        ▼
01_exploracao.py
   → Análise exploratória das 9 tabelas
   → Identificação de nulos, outliers e inconsistências
   → Mapeamento dos relacionamentos entre tabelas
        │
        ▼
02_limpeza.py
   → Conversão de 5 colunas de data: str → datetime
   → Padronização de cidades para title case
   → Tratamento de nulos com mediana
   → Redução da geolocalização: 1.000.163 → 19.015 linhas por CEP
        │
        ▼
03_carga_sql.py
   → Modelagem dimensional — Esquema Estrela
   → Geração automática de dim_tempo com pd.date_range()
   → Cálculo de métricas: dias_para_entregar, dias_de_atraso
   → Carga no SQL Server: 5 tabelas, 248.927 linhas totais
        │
        ▼
SQL Server — banco olist_dw
   → dim_tempo · dim_clientes · dim_produtos
   → dim_vendedores · fato_pedidos
        │
        ▼
Power BI — Dashboard executivo
   → 4 páginas · 15 medidas DAX · tooltips interativos
   → Navegação entre páginas · tema dark + laranja
🗄️ Modelagem Dimensional — Esquema Estrela
     dim_clientes          dim_produtos
      (99.441)              (32.951)
          \                    /
           \                  /
            fato_pedidos (112.650)
           /                  \
          /                    \
    dim_vendedores          dim_tempo
      (3.095)                 (774)

Decisões técnicas documentadas:

Surrogate Keys (INT) em todas as dimensões — JOINs mais rápidos que VARCHAR
Geolocalização agregada por média de coordenadas por CEP — elimina 98% das duplicatas
dim_tempo gerada via Python com pd.date_range() — suporte nativo a filtros de calendário no Power BI
Métricas calculadas no ETL e não no DAX — dias_para_entregar e dias_de_atraso para melhor performance
📊 SQL Avançado — Queries de Negócio

Arquivo: sql/analises_negocio.sql

Query	Técnica SQL	Insight encontrado
Faturamento mensal	GROUP BY + JOIN	Black Friday 2017: +52% em novembro
Top 10 categorias	JOIN multitabela + TOP N	health_beauty lidera; bed_bath_table tem nota mais baixa
Performance por estado	JOIN + agregações	SP: frete R$15 e 8 dias vs MA: frete R$38 e 21 dias
Top 10 vendedores	CTE	Lauro de Freitas-BA: ticket médio de R$543
Ranking por estado	CTE + RANK() OVER PARTITION BY	Top vendedor de cada UF em uma query
Faturamento acumulado	SUM() OVER + LAG()	Crescimento de R$207 para R$13,5Mi em 2 anos

Exemplo — Window Function com CTE:

sql
WITH faturamento_vendedor AS (
    SELECT
        v.estado, v.seller_id, v.cidade,
        ROUND(SUM(f.valor_produto), 2) AS faturamento,
        COUNT(DISTINCT f.order_id)     AS total_pedidos
    FROM fato_pedidos f
    JOIN dim_vendedores v ON f.sk_vendedor = v.sk_vendedor
    WHERE f.status_pedido NOT IN ('canceled', 'unavailable')
    GROUP BY v.estado, v.seller_id, v.cidade
)
SELECT *,
    RANK() OVER (
        PARTITION BY estado
        ORDER BY faturamento DESC
    ) AS ranking_no_estado
FROM faturamento_vendedor
ORDER BY estado, ranking_no_estado;
📈 Dashboard Power BI — 4 Páginas
Página 1 — Visão Geral

KPIs principais · faturamento mensal por ano com anotação da Black Friday · top 10 categorias · filtros por ano e estado · 2 tooltips interativos (detalhes do mês e da categoria)
![Visão Geral](prints/01_visao_geral.png)

Página 2 — Produtos

Faturamento e nota por categoria · comparativo de ticket médio · tabela detalhada com classificação de status · filtro por categoria
![Produtos](prints/02_produtos.png)

Página 3 — Logística

Mapa de bolhas por estado · gráfico de dispersão prazo vs satisfação com correlação visual · tabela com badges de performance por estado (Excelente / Bom / Atenção / Crítico)
![Logística](prints/03_logistica.png)

Página 4 — Vendedores

Faturamento por estado do vendedor · top 10 vendedores individuais · tabela completa com nota, prazo e ticket médio · destaque visual para cases de sucesso e alertas
![Vendedores](prints/04_vendedores.png)

Recursos de UX: navegação entre páginas via botões · tooltips de página com dados contextuais · tema dark + laranja consistente em todas as páginas · design responsivo 1280x720

🔍 Principais Insights Encontrados
Sazonalidade e Crescimento
Black Friday 2017: novembro cresceu +52% sobre outubro — primeiro mês a ultrapassar R$ 1 milhão de faturamento
Volume cresceu 813% em 12 meses (jan/2017 → jan/2018) com ticket médio estável entre R$110 e R$133 — crescimento por aquisição de novos clientes, não por desconto
Produtos
health_beauty lidera em volume mas watches_gifts tem maior ticket médio (R$214 vs R$142) — maior potencial de receita por pedido
bed_bath_table tem a nota mais baixa (3,90) com o maior volume — alto impacto negativo no NPS da plataforma
cool_stuff com ticket médio de R$164 e volume baixo — nicho com alto potencial de crescimento
Logística e Regiões
SP concentra 41% dos pedidos com menor frete (R$15,19), menor prazo (8,3 dias) e maior nota (4,13)
Correlação negativa confirmada: SP entrega em 8 dias (nota 4,13) vs MA em 21 dias (nota 3,70)
Nordeste e Norte pagam frete 2-3x maior que SP — evidência direta para política de subsídio regional
Clientes de estados distantes têm ticket médio mais alto — compram apenas quando o produto justifica o custo do frete
Vendedores
Lauro de Freitas-BA: único top 5 fora de SP com R$222k em apenas 358 pedidos e ticket médio de R$543 — case de alto valor unitário
Itaquaquecetuba-SP: R$187k de faturamento mas nota 3,35 e 21,9 dias de prazo — pior experiência do top 10
8 dos top 10 vendedores estão em SP — vantagem logística de proximidade confirmada pelos dados
📁 Estrutura do Repositório
analise-ecommerce-olist/
├── notebooks/
│   ├── 01_exploracao.py         ← EDA das 9 tabelas com análise de qualidade
│   ├── 02_limpeza.py            ← ETL: tratamento, padronização e limpeza
│   └── 03_carga_sql.py          ← Modelagem dimensional + carga no SQL Server
├── sql/
│   └── analises_negocio.sql     ← 6 queries (CTEs, Window Functions, JOINs)
├── prints/
│   ├── 01_visao_geral.png
│   ├── 02_produtos.png
│   ├── 03_logistica.png
│   └── 04_vendedores.png
├── tema_olist.json              ← Tema dark + laranja para Power BI
├── analise-ecommerce-olist.pbix ← Dashboard Power BI completo
├── .gitignore
└── README.md
▶️ Como Reproduzir o Projeto

Pré-requisitos: Python 3.10+, SQL Server Developer Edition (gratuito), Power BI Desktop (gratuito)

bash
# 1. Clonar o repositório
git clone https://github.com/BrendonSantos7/analise-ecommerce-olist.git
cd analise-ecommerce-olist

# 2. Instalar dependências Python
pip install pandas sqlalchemy pyodbc

# 3. Baixar o dataset (gratuito, sem login)
# https://github.com/olist/work-at-olist-data
# Extrair os 9 CSVs em data/raw/

# 4. Executar o pipeline na ordem
python notebooks/01_exploracao.py
python notebooks/02_limpeza.py
python notebooks/03_carga_sql.py

# 5. Abrir o dashboard
# Abrir analise-ecommerce-olist.pbix no Power BI Desktop
# Atualizar a conexão: localhost > olist_dw > Autenticação Windows
🎓 Competências Demonstradas
✅ Python para ETL e análise exploratória (pandas, SQLAlchemy, pathlib)
✅ Modelagem dimensional — Esquema Estrela (fato + 4 dimensões)
✅ SQL Server / T-SQL avançado (CTEs, Window Functions, JOINs, Views)
✅ Pipeline de dados ponta a ponta: raw → clean → dimensional → visual
✅ Power BI: modelagem, 15 medidas DAX, dashboard executivo
✅ Inteligência de tempo em DAX (YoY, MoM, YTD, variação acumulada)
✅ Tooltips de página personalizados e navegação interativa
✅ Storytelling de dados com raciocínio de negócio
✅ Documentação técnica profissional e Git/GitHub
✅ Análise de dados reais com insights acionáveis para tomada de decisão
👨‍💻 Autor

Brendon Santos Profissional em transição de carreira para Análise de Dados, com experiência prévia em SQL Server, Excel e Power BI. Este projeto foi desenvolvido integralmente para demonstrar competências práticas no ciclo completo de dados: ingestão, limpeza, modelagem, análise e visualização.

Mostrar Imagem Mostrar Imagem

<div align="center">

Dataset: Olist — work-at-olist-data · Dados reais de e-commerce brasileiro (2016–2018)

</div>