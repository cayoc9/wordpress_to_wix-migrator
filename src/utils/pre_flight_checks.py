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
    
    site_id = config.get("wix", {}).get("site_id")
    api_key = config.get("wix", {}).get("api_key")
    base_url = config.get("wix", {}).get("base_url", "https://www.wixapis.com")

    if not site_id or not api_key:
        raise PreFlightCheckError("Wix Site ID ou API Key não encontrados no arquivo de configuração.")

    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
    }
    
    # Check 1: API Key validity and Site ID correctness by calling a simple endpoint
    apps_url = f"{base_url}/v1/apps"
    try:
        response = requests.get(apps_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            raise PreFlightCheckError("A Wix API Key fornecida é inválida ou expirou. Verifique a Etapa B das instruções.")
        elif e.response.status_code == 404:
            raise PreFlightCheckError("O Wix Site ID fornecido está incorreto. Verifique a Etapa A das instruções.")
        else:
            raise PreFlightCheckError(f"Erro inesperado ao verificar as credenciais: {e}")
    except requests.RequestException as e:
        raise PreFlightCheckError(f"Erro de rede ao tentar se conectar com a API do Wix: {e}")

    # Check 2: Wix Blog app installation
    installed_apps = response.json().get("apps", [])
    is_blog_installed = any(app.get("id") == WIX_BLOG_APP_ID for app in installed_apps)

    if not is_blog_installed:
        raise PreFlightCheckError("O aplicativo 'Wix Blog' não está instalado neste site. Por favor, adicione-o pela App Market do Wix para continuar.")

    print("[INFO] Pre-flight checks passed successfully.")
