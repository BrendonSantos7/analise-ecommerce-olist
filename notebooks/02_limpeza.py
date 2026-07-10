import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR /'data'/'raw'
CLEAN_DIR = BASE_DIR /'data'/'clean' 

# Cria a pasta clean automaticamente se nao existir
# exit_ok=True siginifica: se ja existir, nao da erro
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

print("Carregando tabelas brutas..")

orders      = pd.read_csv(RAW_DIR / 'olist_orders_dataset.csv')
customers   = pd.read_csv(RAW_DIR / 'olist_customers_dataset.csv')
items       = pd.read_csv(RAW_DIR / 'olist_order_items_dataset.csv')
payments    = pd.read_csv(RAW_DIR / 'olist_order_payments_dataset.csv')
reviews     = pd.read_csv(RAW_DIR / 'olist_order_reviews_dataset.csv')
products    = pd.read_csv(RAW_DIR / 'olist_products_dataset.csv')
sellers     = pd.read_csv(RAW_DIR / 'olist_sellers_dataset.csv')
geolocation = pd.read_csv(RAW_DIR / 'olist_geolocation_dataset.csv')
translation = pd.read_csv(RAW_DIR / 'product_category_name_translation.csv')

print("Tabelas carregadas!")

# ============================================================
# ORDERS — converter datas de texto para datetime
# ============================================================
# No 01_exploracao vimos que todas as datas vieram como str (texto)
# pd.to_datetime() converte texto para data de verdade
# Sem isso nao conseguimos calcular: "quantos dias demorou a entrega?"
# errors='coerce' -> se encontrar data invalida, coloca NaT (nulo de data)
#                    em vez de travar o script com erro
# Equivalente SQL: CAST(coluna AS DATETIME)

print("\nLimpando orders...")

colunas_data_orders = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

for col in colunas_data_orders:
    orders[col] = pd.to_datetime(orders[col], errors='coerce')

print(" -> datas convertidas de texto para datetime")
print(f" -> tipos apos conversao: {orders[colunas_data_orders].dtypes.unique()}")

# ============================================================
# ITEMS — converter shipping_limit_date para datetime
# ============================================================

print("\nLimpando items...")

items['shipping_limit_date'] = pd.to_datetime(
    items['shipping_limit_date'], errors='coerce'
)

print(" -> shipping_limit_date convertida para datetime")

# ============================================================
# REVIEWS — converter datas
# ============================================================

print("\nLimpando reviews...")

reviews['review_creation_date'] = pd.to_datetime(reviews['review_creation_date'], errors='coerce')
reviews['review_answer_timestamp'] = pd.to_datetime(reviews['review_answer_timestamp'], errors='coerce')

print(" -> datas convertidas para datetime")

# ============================================================
# CUSTOMERS — padronizar cidades
# ============================================================
# No 01_exploracao vimos: "sao paulo", "campinas" — tudo minusculo
# .str.title() transforma a primeira letra de cada palavra em maiuscula
# "sao paulo" -> "Sao Paulo"
# "sao bernardo do campo" -> "Sao Bernardo Do Campo"
# Equivalente Excel: funcao PROPER()

print("\nLimpando customers...")

antes = customers['customer_city'].iloc[0]
customers['customer_city'] = customers['customer_city'].str.title()
depois = customers['customer_city'].iloc[0]

print(f" -> cidade antes: '{antes}' | depois '{depois}'")

# ============================================================
# SELLERS — padronizar cidades (mesmo problema)
# ============================================================

print("\n Limpando sellers...")

antes = sellers['seller_city'].iloc[0]
sellers['seller_city'] = sellers['seller_city'].str.title()
depois = sellers['seller_city'].iloc[0]

print(f" -> cidade antes: '{antes}' | depois: '{depois}'")

# ============================================================
# PRODUCTS — 3 correcoes
# ============================================================

print("\nLimpando products...")

# CORRECAO 1: renomear colunas com erro de digitacao
# 'lenght' esta errado — o correto e 'length'
# Isso veio assim no dataset original da Olist
# .rename() com dicionario: {'nome_antigo': 'nome_novo'}
# Equivalente SQL: sp_rename 'tabela.coluna_antiga', 'coluna_nova', 'COLUMN'

products = products.rename(columns={
    'product_name_lenght' : 'product_name_length',
    'product_description_lenght' : 'product_description_length'
})

print(" -> colunas renomeadas: lenght -> length")

# CORRECAO 2: preencher 610 produtos sem categoria
# .fillna() substitui valores nulos por um valor fixo
# Equivalente SQL: ISNULL(product_category_name, 'sem_categoria')
# Equivalente Excel: =SE(ÉCÉL.VAZIA(A1),"sem_categoria",A1)

nulos_antes = products['product_category_name'].isnull().sum()
products['product_category_name'] = products['product_category_name'].fillna('sem cateogria')
nulos_depois = products['product_category_name'].isnull().sum()

print(f" -> categorias nulas: {nulos_antes} antes | {nulos_depois} depois")

# CORRECAO 3: preencher 2 produtos sem dimensoes/peso com a mediana
# Mediana e mais robusta que media quando ha outliers
# Ex: se um produto pesa 1g e outro pesa 50kg, a media puxa para cima
#     a mediana pega o valor do meio, mais representativo
# .median() calcula a mediana da coluna ignorando nulos

colunas_dimensao = [
    'product_weight_g',
    'product_length_cm',
    'product_height_cm',
    'product_width_cm'
]

for col in colunas_dimensao:
    mediana = products[col].median()
    products[col] = products[col].fillna(mediana)

print(" -> 2 produtos sem dimensoes preenchidos com a mediana")

# ============================================================
# GEOLOCATION — reduzir de 1 milhao para 1 linha por CEP
# ============================================================
# No 01_exploracao vimos: 1.000.163 linhas para representar CEPs
# Isso porque tem multiplas coordenadas por CEP
# Se deixarmos assim, qualquer JOIN vai gerar linhas duplicadas
#
# Solucao: agrupar por CEP e calcular a media de lat/lng
# .groupby() agrupa as linhas pelo campo informado
# .agg() define o que fazer com cada coluna dentro do grupo
# Equivalente SQL:
#   SELECT zip, AVG(lat), AVG(lng), MAX(city), MAX(state)
#   FROM geolocation
#   GROUP BY zip

print("\nLimpando geolocation...")

linhas_antes = len(geolocation)

geo_clean = geolocation.groupby(
    'geolocation_zip_code_prefix',
    as_index=False   # mantem a coluna de agrupamento como coluna normal
).agg(
    geolocation_lat = ('geolocation_lat', 'mean'),
    geolocation_lng = ('geolocation_lat', 'mean'),
    geolocation_city = ('geolocation_lat', 'first'),
    geolocation_state = ('geolocation_lat', 'first'),
)

linhas_depois = len(geo_clean)

print(f" -> linhas antes: {linhas_antes:,} | depois: {linhas_depois}")
print(f" -> reducao de {((linhas_antes - linhas_depois) / linhas_antes * 100):.1f}%")

# ============================================================
# SALVAR OS DADOS LIMPOS EM data/clean/
# ============================================================
# Salvamos em arquivos CSV separados para usar nas proximas fases
# index=False evita salvar o numero da linha como coluna extra
# Equivalente SQL: SELECT * INTO tabela_clean FROM tabela_tratada

print("\nSalvando arquivos limpos em data/clean/ ...")

orders.to_csv(      CLEAN_DIR / 'orders.csv',       index=False)
customers.to_csv(   CLEAN_DIR / 'customers.csv',    index=False)
items.to_csv(       CLEAN_DIR / 'items.csv',         index=False)
payments.to_csv(    CLEAN_DIR / 'payments.csv',      index=False)
reviews.to_csv(     CLEAN_DIR / 'reviews.csv',       index=False)
products.to_csv(    CLEAN_DIR / 'products.csv',      index=False)
sellers.to_csv(     CLEAN_DIR / 'sellers.csv',       index=False)
geo_clean.to_csv(   CLEAN_DIR / 'geolocation.csv',  index=False)
translation.to_csv( CLEAN_DIR / 'translation.csv',  index=False)

print("\n" + "="*50)
print("LIMPEZA CONCLUIDA COM SUCESSO!")
print("="*50)
print(f"\nArquivos salvos em: {CLEAN_DIR}")
print("\nResumo final:")
print(f"  orders:      {len(orders):>8,} linhas")
print(f"  customers:   {len(customers):>8,} linhas")
print(f"  items:       {len(items):>8,} linhas")
print(f"  payments:    {len(payments):>8,} linhas")
print(f"  reviews:     {len(reviews):>8,} linhas")
print(f"  products:    {len(products):>8,} linhas")
print(f"  sellers:     {len(sellers):>8,} linhas")
print(f"  geolocation: {len(geo_clean):>8,} linhas")
print(f"  translation: {len(translation):>8,} linhas")