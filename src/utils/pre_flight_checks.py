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
    
    site_id = (config.get("wix", {}).get("site_id") or "").strip()
    api_key = (config.get("wix", {}).get("api_key") or "").strip()
    base_url = (config.get("wix", {}).get("base_url", "https://www.wixapis.com") or "").strip()

    if not site_id or not api_key:
        raise PreFlightCheckError("Wix Site ID ou API Key não encontrados no arquivo de configuração.")

    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
    }
    
    # Check 1: Validate API Key, Site ID scope and Blog availability using a real Blog endpoint
    blog_tags_url = f"{base_url.rstrip('/')}/blog/v3/tags"
    try:
        response = requests.get(blog_tags_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as e:
        status = e.response.status_code
        if status == 401:
            raise PreFlightCheckError("A Wix API Key fornecida é inválida ou expirou. Verifique a Etapa B das instruções.")
        elif status == 403:
            raise PreFlightCheckError("A chave de API não possui as permissões necessárias (ex.: Manage Posts/Publish Post) ou não está autorizada para este site.")
        elif status == 404:
            # 404 aqui normalmente indica que o app de Blog não está instalado neste site
            raise PreFlightCheckError("O aplicativo 'Wix Blog' não está instalado neste site OU o Site ID não corresponde ao site da chave de API. Verifique a Etapa A e garanta que o app Blog esteja instalado.")
        else:
            raise PreFlightCheckError(f"Erro inesperado ao verificar as credenciais: {e}")
    except requests.RequestException as e:
        raise PreFlightCheckError(f"Erro de rede ao tentar se conectar com a API do Wix: {e}")

    # If we reached here, the Blog endpoint is accessible, which implies the Blog app is installed
    print("[INFO] Pre-flight checks passed successfully.")
