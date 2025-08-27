import duckdb
import pandas as pd
import os

# Define o caminho para o banco de dados e para o CSV
db_path = 'data/migration.duckdb'
csv_path = 'docs/posts-otimize - Página1.csv'
table_name = 'posts'

def initialize_database():
    """
    Inicializa o banco de dados DuckDB, cria a tabela de posts
    e a popula com os dados do arquivo CSV.
    """
    # Garante que o diretório de dados exista
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Conecta ao banco de dados DuckDB (cria o arquivo se não existir)
    con = duckdb.connect(database=db_path, read_only=False)

    try:
        # Verifica se a tabela já existe
        existing_tables = con.execute("SHOW TABLES;").fetchall()
        if (table_name,) in existing_tables:
            print(f"A tabela '{table_name}' já existe. Nenhuma ação foi tomada.")
            return

        # Lê o arquivo CSV usando pandas
        print(f"Lendo o arquivo CSV de: {csv_path}")
        df = pd.read_csv(csv_path)

        # Limpa os nomes das colunas para serem compatíveis com SQL
        df.columns = [col.strip().replace(' ', '_').replace('-', '_').lower() for col in df.columns]

        # Cria a tabela 'posts' a partir do DataFrame do pandas
        print(f"Criando a tabela '{table_name}' e inserindo os dados...")
        con.register('df_temp', df)
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_temp")

        print(f"Tabela '{table_name}' criada com sucesso com {len(df)} registros.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        # Fecha a conexão com o banco de dados
        con.close()
        print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    initialize_database()