import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist_dw;"
    "Trusted_Connection=yes;"  # usa autenticacao Windows, sem senha
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME() AS banco_atual, GETDATE() AS agora")
    row = cursor.fetchone()
    print(f"Conectado com sucesso!")
    print(f"Banco: {row.banco_atual}")
    print(f"Data/hora do servidor: {row.agora}")
    conn.close()
except Exception as e:
    print(f"Erro na conexao: {e}")