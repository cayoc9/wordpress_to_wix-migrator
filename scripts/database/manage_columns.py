import duckdb
import os

# Define o caminho para o banco de dados
db_path = 'data/migration.duckdb'
table_name = 'posts'

def add_wix_post_id_column():
    """
    Adiciona a coluna 'wix_post_id' à tabela de posts se ela não existir.
    """
    if not os.path.exists(db_path):
        print(f"Erro: O arquivo de banco de dados '{db_path}' não foi encontrado.")
        return

    con = duckdb.connect(database=db_path, read_only=False)
    try:
        # Verifica se a coluna já existe
        table_info = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        column_names = [col[1] for col in table_info]

        if 'wix_post_id' not in column_names:
            print(f"Adicionando a coluna 'wix_post_id' na tabela '{table_name}'...")
            con.execute(f"ALTER TABLE {table_name} ADD COLUMN wix_post_id VARCHAR;")
            print("Coluna 'wix_post_id' adicionada com sucesso.")
        else:
            print("A coluna 'wix_post_id' já existe.")

    except Exception as e:
        print(f"Ocorreu um erro ao adicionar a coluna: {e}")
    finally:
        con.close()
        print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    add_wix_post_id_column()