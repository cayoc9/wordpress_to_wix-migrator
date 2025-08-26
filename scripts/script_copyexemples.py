import pandas as pd
import os
import shutil

# Define os caminhos relativos à raiz do projeto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
csv_file_path = os.path.join(project_root, 'data', 'post_exemples', 'posts_formatação_completa.csv')
posts_dir = os.path.join(project_root, 'data', 'posts')
examples_dir = os.path.join(project_root, 'data', 'post_exemples')

def copy_post_examples():
    """
    Lê um arquivo CSV, extrai os 'ID_wix', encontra os arquivos de post correspondentes
    e os copia para um diretório de exemplos.
    """
    # 1. Verificar se o diretório de destino existe, senão, criá-lo
    if not os.path.exists(examples_dir):
        os.makedirs(examples_dir)
        print(f"Diretório criado: {examples_dir}")

    # 2. Acessar o arquivo CSV e ler a coluna 'ID_wix'
    try:
        df = pd.read_csv(csv_file_path)
        if 'ID_wix' not in df.columns:
            print(f"Erro: A coluna 'ID_wix' não foi encontrada em {csv_file_path}")
            return
        
        # Remove valores nulos ou vazios e converte para string
        wix_ids = df['ID_wix'].dropna().astype(str).tolist()
        print(f"{len(wix_ids)} IDs Wix encontrados no CSV.")

    except FileNotFoundError:
        print(f"Erro: O arquivo CSV não foi encontrado em {csv_file_path}")
        return
    except Exception as e:
        print(f"Ocorreu um erro ao ler o CSV: {e}")
        return

    # 3. Iterar sobre os IDs e copiar os arquivos
    copied_count = 0
    for wix_id in wix_ids:
        # O id no CSV pode ser um float (ex: 123.0), removemos o '.0'
        clean_wix_id = wix_id.split('.')[0]
        
        found_file = False
        for filename in os.listdir(posts_dir):
            if clean_wix_id in filename:
                source_path = os.path.join(posts_dir, filename)
                destination_path = os.path.join(examples_dir, filename)
                
                try:
                    shutil.copy2(source_path, destination_path)
                    print(f"Copiado: {filename} -> {examples_dir}/")
                    copied_count += 1
                    found_file = True
                    break # Para de procurar arquivos para este ID após encontrar o primeiro
                except Exception as e:
                    print(f"Erro ao copiar {filename}: {e}")
        
        if not found_file:
            print(f"Aviso: Nenhum arquivo de post encontrado para o ID Wix: {clean_wix_id}")

    print(f"\nProcesso concluído. {copied_count} arquivos copiados para {examples_dir}.")

if __name__ == "__main__":
    copy_post_examples()
