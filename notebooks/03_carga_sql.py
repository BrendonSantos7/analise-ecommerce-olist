import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine

BASE_DIR  = Path(__file__).parent.parent
CLEAN_DIR = BASE_DIR / 'data' / 'clean'

# ============================================================
# CONEXAO COM SQL SERVER
# ============================================================
# create_engine monta a "ponte" permanente entre Python e SQL Server
# Equivalente a abrir o SSMS e conectar na instancia
# mssql+pyodbc = dialeto SQL Server usando pyodbc como driver

print("Conectando ao SQL Server...")
engine = create_engine(
    "mssql+pyodbc://localhost/olist_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)
print("Conexao OK!")

# ============================================================
# CARREGAR DADOS LIMPOS
# ============================================================
# parse_dates avisa ao pandas quais colunas sao datas
# Equivalente ao que fizemos no 02_limpeza, mas agora lendo
# diretamente ja convertendo — economiza uma etapa

print("\nCarregando dados limpos...")

colunas_data_orders = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

orders      = pd.read_csv(CLEAN_DIR / 'orders.csv',      parse_dates=colunas_data_orders)
customers   = pd.read_csv(CLEAN_DIR / 'customers.csv')
items       = pd.read_csv(CLEAN_DIR / 'items.csv',        parse_dates=['shipping_limit_date'])
payments    = pd.read_csv(CLEAN_DIR / 'payments.csv')
reviews     = pd.read_csv(CLEAN_DIR / 'reviews.csv',      parse_dates=['review_creation_date','review_answer_timestamp'])
products    = pd.read_csv(CLEAN_DIR / 'products.csv')
sellers     = pd.read_csv(CLEAN_DIR / 'sellers.csv')
translation = pd.read_csv(CLEAN_DIR / 'translation.csv')

print("Dados carregados!")

# ============================================================
# 1. DIM_TEMPO
# ============================================================
# Nao existe uma tabela de tempo no dataset original
# Precisamos GERAR todas as datas entre a primeira e ultima compra
# pd.date_range() cria uma sequencia de datas com frequencia diaria (freq='D')
# Equivalente SQL: seria uma recursao com CTE ou uma tabela de calendario

print("\n[1/5] Criando dim_tempo...")

data_min = orders['order_purchase_timestamp'].min().date()
data_max = orders['order_purchase_timestamp'].max().date()
datas    = pd.date_range(start=data_min, end=data_max, freq='D')

print(f"  -> periodo: {data_min} ate {data_max} ({len(datas)} dias)")

nomes_mes = {
    1:'Janeiro', 2:'Fevereiro', 3:'Marco',    4:'Abril',
    5:'Maio',    6:'Junho',     7:'Julho',     8:'Agosto',
    9:'Setembro',10:'Outubro',  11:'Novembro', 12:'Dezembro'
}
nomes_dia = {
    0:'Segunda-feira', 1:'Terca-feira',  2:'Quarta-feira',
    3:'Quinta-feira',  4:'Sexta-feira',  5:'Sabado', 6:'Domingo'
}

dim_tempo = pd.DataFrame({
    # sk_tempo no formato YYYYMMDD: ex 20170902
    # Isso facilita filtros de data no SQL: WHERE sk_tempo BETWEEN 20170101 AND 20171231
    'sk_tempo'         : datas.strftime('%Y%m%d').astype(int),
    'data_completa'    : datas.date,
    'ano'              : datas.year,
    'trimestre'        : datas.quarter,
    'mes'              : datas.month,
    'nome_mes'         : datas.month.map(nomes_mes),
    'semana_do_ano'    : datas.isocalendar().week.astype(int),
    'dia'              : datas.day,
    'dia_da_semana'    : datas.dayofweek,       # 0=segunda, 6=domingo
    'nome_dia_semana'  : datas.dayofweek.map(nomes_dia),
    # BIT no SQL Server = 0 ou 1, por isso astype(int)
    'eh_fim_de_semana' : (datas.dayofweek >= 5).astype(int)
})

# .to_sql() insere o DataFrame inteiro na tabela do SQL Server
# if_exists='append' = adiciona linhas sem apagar a tabela (que ja criamos com DDL)
# index=False = nao insere o indice do pandas como coluna extra
# chunksize=1000 = insere de 1000 em 1000 linhas (evita timeout)
dim_tempo.to_sql('dim_tempo', engine, if_exists='append', index=False, chunksize=1000)
print(f"  -> {len(dim_tempo):,} linhas inseridas em dim_tempo")

# ============================================================
# 2. DIM_CLIENTES
# ============================================================
# .copy() cria uma copia independente do DataFrame original
# Sem isso, modificacoes aqui afetariam o DataFrame 'customers' original
# Equivalente SQL: SELECT ... INTO #temp FROM customers

print("\n[2/5] Criando dim_clientes...")

dim_clientes = customers[[
    'customer_id',
    'customer_unique_id',
    'customer_city',
    'customer_state',
    'customer_zip_code_prefix'
]].copy()

# drop_duplicates garante uma linha por cliente
# subset='customer_id' = considera duplicado quem tem o mesmo customer_id
# reset_index(drop=True) reinicia a numeracao de 0, 1, 2...
dim_clientes = dim_clientes.drop_duplicates(subset='customer_id').reset_index(drop=True)

# Criar surrogate key: index comeca em 0, somamos 1 para comecar em 1
# .insert(0, ...) adiciona a coluna na posicao 0 (primeira coluna)
dim_clientes.insert(0, 'sk_cliente', dim_clientes.index + 1)

# Renomear colunas para bater com o DDL que criamos no SQL Server
dim_clientes.columns = [
    'sk_cliente', 'customer_id', 'customer_unique_id',
    'cidade', 'estado', 'cep_prefixo'
]

dim_clientes.to_sql('dim_clientes', engine, if_exists='append', index=False, chunksize=1000)
print(f"  -> {len(dim_clientes):,} linhas inseridas em dim_clientes")

# ============================================================
# 3. DIM_PRODUTOS
# ============================================================
# Aqui fazemos um JOIN com a tabela de traducao para ter
# o nome da categoria em ingles — mais profissional no dashboard
# .merge() e o equivalente ao JOIN do SQL:
#   SELECT p.*, t.product_category_name_english
#   FROM products p LEFT JOIN translation t ON p.product_category_name = t.product_category_name

print("\n[3/5] Criando dim_produtos...")

dim_produtos = products.merge(
    translation,
    on='product_category_name',
    how='left'      # LEFT JOIN: mantem todos os produtos mesmo sem traducao
)

# Preencher categorias sem traducao com 'unknown'
dim_produtos['product_category_name_english'] = (
    dim_produtos['product_category_name_english'].fillna('unknown')
)

dim_produtos = dim_produtos[[
    'product_id',
    'product_category_name',
    'product_category_name_english',
    'product_weight_g',
    'product_length_cm',
    'product_height_cm',
    'product_width_cm'
]].copy()

dim_produtos = dim_produtos.drop_duplicates(subset='product_id').reset_index(drop=True)
dim_produtos.insert(0, 'sk_produto', dim_produtos.index + 1)

dim_produtos.columns = [
    'sk_produto', 'product_id', 'categoria', 'categoria_ingles',
    'peso_gramas', 'comprimento_cm', 'altura_cm', 'largura_cm'
]

dim_produtos.to_sql('dim_produtos', engine, if_exists='append', index=False, chunksize=1000)
print(f"  -> {len(dim_produtos):,} linhas inseridas em dim_produtos")

# ============================================================
# 4. DIM_VENDEDORES
# ============================================================

print("\n[4/5] Criando dim_vendedores...")

dim_vendedores = sellers[[
    'seller_id', 'seller_city', 'seller_state', 'seller_zip_code_prefix'
]].copy()

dim_vendedores = dim_vendedores.drop_duplicates(subset='seller_id').reset_index(drop=True)
dim_vendedores.insert(0, 'sk_vendedor', dim_vendedores.index + 1)

dim_vendedores.columns = ['sk_vendedor', 'seller_id', 'cidade', 'estado', 'cep_prefixo']

dim_vendedores.to_sql('dim_vendedores', engine, if_exists='append', index=False, chunksize=1000)
print(f"  -> {len(dim_vendedores):,} linhas inseridas em dim_vendedores")

# ============================================================
# 5. FATO_PEDIDOS
# ============================================================
# Essa e a etapa mais complexa:
# 1. Agrega pagamentos por pedido (um pedido pode ter varios pagamentos)
# 2. Agrega reviews por pedido
# 3. Junta tudo em nivel de item de pedido
# 4. Calcula metricas de entrega
# 5. Substitui chaves originais pelas surrogate keys das dimensoes

print("\n[5/5] Criando fato_pedidos...")

# PASSO A: agregar pagamentos por pedido
# Um pedido pode ter cartao + voucher, por exemplo
# Somamos o valor total pago e pegamos o tipo do pagamento principal (sequential=1)
# Equivalente SQL:
#   SELECT order_id, SUM(payment_value), MAX(payment_installments), ...
#   FROM payments GROUP BY order_id

payments_principais = payments[payments['payment_sequential'] == 1][[
    'order_id', 'payment_type', 'payment_installments'
]]

payments_agg = payments.groupby('order_id').agg(
    valor_pago = ('payment_value', 'sum')
).reset_index()

payments_agg = payments_agg.merge(payments_principais, on='order_id', how='left')
payments_agg.columns = ['order_id', 'valor_pago', 'tipo_pagamento', 'parcelas']

# PASSO B: pegar nota de avaliacao por pedido
# Cada pedido tem no maximo 1 review — mas usamos first() para garantir
reviews_agg = reviews.groupby('order_id').agg(
    nota_avaliacao = ('review_score', 'first')
).reset_index()

# PASSO C: construir a fato juntando tudo
# Comecar pelos itens (nivel mais granular do negocio: 1 linha por produto vendido)
fato = items.copy()

# JOIN com orders: pegar datas, status e customer_id
# Equivalente SQL: FROM items i JOIN orders o ON i.order_id = o.order_id
fato = fato.merge(
    orders[[
        'order_id', 'customer_id', 'order_status',
        'order_purchase_timestamp',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]],
    on='order_id', how='left'
)

# JOIN com pagamentos agregados
fato = fato.merge(payments_agg, on='order_id', how='left')

# JOIN com reviews
fato = fato.merge(reviews_agg, on='order_id', how='left')

# PASSO D: calcular metricas
# .dt.days extrai o numero de dias de um timedelta (diferenca entre datas)
# Equivalente SQL: DATEDIFF(DAY, order_purchase_timestamp, order_delivered_customer_date)

fato['dias_para_entregar'] = (
    fato['order_delivered_customer_date'] - fato['order_purchase_timestamp']
).dt.days

# Negativo = entregou antes do prazo | Positivo = entregou depois (atraso)
fato['dias_de_atraso'] = (
    fato['order_delivered_customer_date'] - fato['order_estimated_delivery_date']
).dt.days

# Valor total do item = produto + frete
fato['valor_total_item'] = fato['price'] + fato['freight_value']

# PASSO E: criar sk_tempo no formato YYYYMMDD para fazer JOIN com dim_tempo
fato['sk_tempo'] = fato['order_purchase_timestamp'].dt.strftime('%Y%m%d').astype(int)

# PASSO F: substituir chaves originais pelas surrogate keys
# Equivalente SQL: LEFT JOIN dim_clientes ON fato.customer_id = dim_clientes.customer_id
fato = fato.merge(dim_clientes[['sk_cliente', 'customer_id']],  on='customer_id',  how='left')
fato = fato.merge(dim_produtos[['sk_produto', 'product_id']],   on='product_id',   how='left')
fato = fato.merge(dim_vendedores[['sk_vendedor', 'seller_id']], on='seller_id',    how='left')

# PASSO G: selecionar apenas as colunas que vao para a tabela fato
fato_final = fato[[
    'sk_tempo', 'sk_cliente', 'sk_produto', 'sk_vendedor',
    'order_id', 'order_item_id',
    'price', 'freight_value', 'valor_total_item',
    'valor_pago', 'parcelas', 'tipo_pagamento',
    'dias_para_entregar', 'dias_de_atraso',
    'nota_avaliacao', 'order_status'
]].copy()

fato_final.columns = [
    'sk_tempo', 'sk_cliente', 'sk_produto', 'sk_vendedor',
    'order_id', 'order_item_id',
    'valor_produto', 'valor_frete', 'valor_total_item',
    'valor_pago', 'parcelas', 'tipo_pagamento',
    'dias_para_entregar', 'dias_de_atraso',
    'nota_avaliacao', 'status_pedido'
]

# PASSO H: remover linhas com surrogate keys nulas
# Isso acontece quando um pedido nao encontra match em alguma dimensao
# Equivalente SQL: WHERE sk_cliente IS NOT NULL AND sk_produto IS NOT NULL ...
# PASSO G2: tratar nulos em colunas NOT NULL da fato
# Alguns pedidos nao tem pagamento registrado — preenchemos com valores padrao
# Equivalente SQL: ISNULL(parcelas, 0), ISNULL(tipo_pagamento, 'unknown')
fato_final['parcelas']       = fato_final['parcelas'].fillna(0).astype(int)
fato_final['tipo_pagamento'] = fato_final['tipo_pagamento'].fillna('unknown')
fato_final['valor_pago']     = fato_final['valor_pago'].fillna(0)

# Converter metricas numericas para os tipos corretos
# float com .0 no final vira int limpo
fato_final['dias_para_entregar'] = fato_final['dias_para_entregar'].astype('Int64')
fato_final['dias_de_atraso']     = fato_final['dias_de_atraso'].astype('Int64')
fato_final['nota_avaliacao']     = fato_final['nota_avaliacao'].astype('Int64')

# PASSO H: remover linhas com surrogate keys nulas
antes = len(fato_final)
fato_final = fato_final.dropna(subset=['sk_tempo', 'sk_cliente', 'sk_produto', 'sk_vendedor'])

depois = len(fato_final)

if antes != depois:
    print(f"  -> {antes - depois:,} linhas removidas por SKs nulos")

# Converter surrogate keys para inteiro
for col in ['sk_tempo', 'sk_cliente', 'sk_produto', 'sk_vendedor']:
    fato_final[col] = fato_final[col].astype(int)

fato_final.to_sql('fato_pedidos', engine, if_exists='append', index=False, chunksize=1000)
print(f"  -> {len(fato_final):,} linhas inseridas em fato_pedidos")

# ============================================================
# VALIDACAO FINAL — contar linhas no SQL Server
# ============================================================
# Confirma que o que Python inseriu e o que o SQL Server recebeu
# text() e necessario para rodar SQL puro dentro do SQLAlchemy

print("\n" + "="*50)
print("CARGA CONCLUIDA! Validando no SQL Server...")
print("="*50)

with engine.connect() as conn:
    for tabela in ['dim_tempo','dim_clientes','dim_produtos','dim_vendedores','fato_pedidos']:
        from sqlalchemy import text
        resultado = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).fetchone()
        print(f"  {tabela:<20} -> {resultado[0]:>10,} linhas no SQL Server")