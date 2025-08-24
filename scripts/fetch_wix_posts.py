import duckdb
import pandas as pd
import os
import subprocess
import json

# Define o caminho para o banco de dados
db_path = 'data/migration.duckdb'
table_name = 'posts'

def add_wix_content_column():
    """
    Adiciona a coluna 'wix_content_json' à tabela de posts se ela não existir.
    """
    con = duckdb.connect(database=db_path, read_only=False)
    try:
        # Verifica se a coluna já existe
        table_info = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        column_names = [col[1] for col in table_info]

        if 'wix_content_json' not in column_names:
            print("Adicionando a coluna 'wix_content_json' na tabela 'posts'...")
            con.execute(f"ALTER TABLE {table_name} ADD COLUMN wix_content_json VARCHAR;")
            print("Coluna 'wix_content_json' adicionada com sucesso.")
        else:
            print("A coluna 'wix_content_json' já existe.")

    except Exception as e:
        print(f"Ocorreu um erro ao adicionar a coluna: {e}")
    finally:
        con.close()

def fetch_and_update_wix_posts():
    """
    Busca os posts da plataforma Wix e atualiza o banco de dados com o conteúdo JSON.
    """
    add_wix_content_column()
    
    con = duckdb.connect(database=db_path, read_only=False)
    try:
        # Seleciona o ID do WordPress e o wix_post_id dos posts que ainda não têm o conteúdo do Wix
        query = f"SELECT id, wix_post_id FROM {table_name} WHERE wix_content_json IS NULL AND wix_post_id IS NOT NULL"
        posts_to_update = con.execute(query).fetchall()
        
        if not posts_to_update:
            print("Todos os posts já estão atualizados ou não possuem wix_post_id para busca.")
            return

        print(f"Encontrados {len(posts_to_update)} posts para buscar no Wix...")

        for wordpress_id, wix_id in posts_to_update:
            print(f"Buscando post com Wix ID: {wix_id} (Wordpress ID: {wordpress_id})")
            
            try:
                # Executa o script get_wix_post.py para buscar o post pelo Wix ID
                result = subprocess.run(
                    ['python3', 'scripts/get_wix_post.py', wix_id],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                wix_content_str = result.stdout
                # Valida se o retorno é um JSON válido antes de inserir
                json.loads(wix_content_str)

                # Atualiza o banco de dados com o conteúdo JSON
                con.execute(f"UPDATE {table_name} SET wix_content_json = ? WHERE id = ?", (wix_content_str, wordpress_id))
                print(f"Post com Wix ID '{wix_id}' (Wordpress ID: {wordpress_id}) atualizado com sucesso.")

            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar o script para o Wix ID '{wix_id}': {e.stderr}")
            except json.JSONDecodeError:
                print(f"Erro: A saída para o Wix ID '{wix_id}' não é um JSON válido.")
            except Exception as e:
                print(f"Um erro inesperado ocorreu para o Wix ID '{wix_id}': {e}")

    except Exception as e:
        print(f"Ocorreu um erro durante a busca e atualização: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    fetch_and_update_wix_posts()