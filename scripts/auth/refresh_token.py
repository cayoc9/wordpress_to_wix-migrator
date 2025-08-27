import json
import os
import subprocess
import sys
from pathlib import Path

def refresh_wix_token():
    """
    Executes the token generation script and updates the main configuration file.
    """
    # Caminho para o script de geração de token
    token_script_path = Path(__file__).parent / "generate_token.py"
    config_path = Path(__file__).parent.parent / "config" / "migration_config.json"
    temp_token_file = Path(__file__).parent.parent / "wix_token.json"

    try:
        # Execute o script Python para gerar o novo token
        print("Gerando novo token do Wix...")
        result = subprocess.run([sys.executable, str(token_script_path)], 
                              cwd=token_script_path.parent.parent,
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Erro ao executar o script de geração de token: {result.stderr}")
            return

        # Verifique se o arquivo de token foi criado
        if not temp_token_file.exists():
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
        if not config_path.exists():
            print(f"Erro: Arquivo de configuração não encontrado em {config_path}")
            return
            
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
        if temp_token_file.exists():
            temp_token_file.unlink()
            print(f"Arquivo temporário '{temp_token_file}' removido.")

if __name__ == "__main__":
    refresh_wix_token()