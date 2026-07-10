import pandas as pd
from pathlib import Path

# ============================================================
# DEFININDO O CAMINHO BASE DO PROJETO
# ============================================================
# __file__ = o caminho completo deste arquivo .py
# .parent   = a pasta onde ele está (notebooks/)
# .parent   = volta mais uma pasta (projeto-olist/)
# Assim o código funciona em qualquer máquina, sem caminho fixo.

BASE_DIR = Path(__file__).parent.parent
RAW_DIR  = BASE_DIR / 'data' / 'raw'

print(f"Pasta do projeto: {BASE_DIR}")
print(f"Pasta dos dados:  {RAW_DIR}")

# ============================================================
# CARREGANDO AS 9 TABELAS
# ============================================================

orders      = pd.read_csv(RAW_DIR / 'olist_orders_dataset.csv')
customers   = pd.read_csv(RAW_DIR / 'olist_customers_dataset.csv')
items       = pd.read_csv(RAW_DIR / 'olist_order_items_dataset.csv')
payments    = pd.read_csv(RAW_DIR / 'olist_order_payments_dataset.csv')
reviews     = pd.read_csv(RAW_DIR / 'olist_order_reviews_dataset.csv')
products    = pd.read_csv(RAW_DIR / 'olist_products_dataset.csv')
sellers     = pd.read_csv(RAW_DIR / 'olist_sellers_dataset.csv')
geolocation = pd.read_csv(RAW_DIR / 'olist_geolocation_dataset.csv')
translation = pd.read_csv(RAW_DIR / 'product_category_name_translation.csv')

print("\nTodas as tabelas carregadas com sucesso!")

# ============================================================
# FUNÇÃO DE EXPLORAÇÃO
# ============================================================

def explorar_tabela(nome, df):
    print("\n" + "="*60)
    print(f"TABELA: {nome}")
    print(f"Tamanho: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
    print("\n--- Primeiras 3 linhas ---")
    print(df.head(3).to_string())
    print("\n--- Tipos de dados e nulos ---")
    info = pd.DataFrame({
        'tipo'  : df.dtypes,
        'nulos' : df.isnull().sum(),
        '% nulo': (df.isnull().sum() / len(df) * 100).round(1)
    })
    print(info)

# Rodando para cada tabela
explorar_tabela("orders",      orders)
explorar_tabela("customers",   customers)
explorar_tabela("items",       items)
explorar_tabela("payments",    payments)
explorar_tabela("reviews",     reviews)
explorar_tabela("products",    products)
explorar_tabela("sellers",     sellers)
explorar_tabela("geolocation", geolocation)
explorar_tabela("translation", translation)