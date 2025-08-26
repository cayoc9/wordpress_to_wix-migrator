import requests

# The official App ID for the Wix Blog application
WIX_BLOG_APP_ID = "14ce1214-b26c-423b-9a75-574219000002"

class PreFlightCheckError(Exception):
    """Custom exception for pre-flight check failures."""
    pass

def run_wix_pre_flight_checks(config: dict):
    """
    Verifies that the Wix environment is correctly configured for migration.

    Args:
        config: The application configuration dictionary.

    Raises:
        PreFlightCheckError: If any check fails.
    """
    print("[INFO] Running pre-flight checks...")
    
    access_token = config.get("wix", {}).get("access_token")
    base_url = config.get("wix", {}).get("base_url", "https://www.wixapis.com")

    if not access_token:
        raise PreFlightCheckError("Token de acesso do Wix não encontrado no arquivo de configuração.")

    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    # Check 1: Verify access token and Members API
    members_url = f"{base_url}/members/v1/members"
    try:
        response = requests.get(members_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            raise PreFlightCheckError("O token de acesso fornecido é inválido ou expirou.")
        else:
            raise PreFlightCheckError(f"Erro inesperado ao verificar a API de Membros: {e}")
    except requests.RequestException as e:
        raise PreFlightCheckError(f"Erro de rede ao tentar se conectar com a API de Membros do Wix: {e}")

    # Check 2: Verify Blog API
    blog_url = f"{base_url}/blog/v3/blog"
    try:
        response = requests.get(blog_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            raise PreFlightCheckError("O aplicativo 'Wix Blog' não está instalado neste site ou a API do Blog não está acessível.")
        else:
            raise PreFlightCheckError(f"Erro inesperado ao verificar a API do Blog: {e}")
    except requests.RequestException as e:
        raise PreFlightCheckError(f"Erro de rede ao tentar se conectar com a API do Blog do Wix: {e}")

    print("[INFO] Pre-flight checks passed successfully.")
