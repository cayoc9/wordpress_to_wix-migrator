import json
import os
import subprocess

def refresh_wix_token():
    """
    Executes the token generation script and updates the main configuration file.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'migration_config.json')
    token_script_path = os.path.join(os.path.dirname(__file__), 'generate_wix_token.sh')
    temp_token_file = 'wix_token.json'

    try:
        # Execute o script de shell para gerar o novo token
        print("Gerando novo token do Wix...")
        subprocess.run(['bash', token_script_path], check=True)

        # Verifique se o arquivo de token foi criado
        if not os.path.exists(temp_token_file):
            print("Erro: O arquivo de token 'wix_token.json' não foi gerado.")
            return

        # Leia o novo token do arquivo temporário
        with open(temp_token_file, 'r') as f:
            new_token_data = json.load(f)
            new_access_token = new_token_data.get('access_token')

        if not new_access_token:
            print("Erro: 'access_token' não encontrado no arquivo 'wix_token.json'.")
            return

        # Leia o arquivo de configuração principal
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        # Atualize o token de acesso no objeto de configuração
        if 'wix' in config_data:
            config_data['wix']['access_token'] = new_access_token
        else:
            print("Erro: Seção 'wix' não encontrada no arquivo de configuração.")
            return

        # Salve o arquivo de configuração atualizado
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print("Token de acesso atualizado com sucesso em 'config/migration_config.json'.")

    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o script de geração de token: {e}")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{temp_token_file}' ou '{config_path}' não foi encontrado.")
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON. Verifique o formato dos arquivos.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        # Remova o arquivo de token temporário
        if os.path.exists(temp_token_file):
            os.remove(temp_token_file)
            print(f"Arquivo temporário '{temp_token_file}' removido.")

if __name__ == "__main__":
    refresh_wix_token()