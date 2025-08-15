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

    # Validate Site ID format (should be a UUID-like string)
    if len(site_id) < 32 or not any(c in site_id for c in ['-']):
        print("[WARNING] O Site ID parece estar em um formato inválido. Site IDs do Wix são geralmente UUIDs longos.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "wix-site-id": site_id,
    }
    
    # Check 1: API Key validity and Site ID correctness by calling a simple endpoint
    apps_url = f"{base_url}/apps/v1/instance"
    try:
        print(f"[INFO] Testando conexão com: {apps_url}")
        response = requests.get(apps_url, headers=headers, timeout=10)
        response.raise_for_status()
        print("[INFO] Conexão com a API do Wix estabelecida com sucesso!")
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            raise PreFlightCheckError(
                "A Wix API Key fornecida é inválida ou expirou.\n"
                "Soluções possíveis:\n"
                "1. Verifique se a API Key está correta\n"
                "2. Gere uma nova API Key no painel do Wix\n"
                "3. Certifique-se de que a API Key não expirou"
            )
        elif e.response.status_code == 403:
            raise PreFlightCheckError(
                "Acesso negado pela API do Wix.\n"
                "Possíveis causas:\n"
                "1. A API Key não tem as permissões necessárias\n"
                "2. O Site ID pode estar incorreto\n"
                "3. O site pode não existir ou não estar acessível\n"
                "4. Você pode não ter acesso a este site\n\n"
                "Para soluções detalhadas, consulte o arquivo TROUBLESHOOTING.md\n"
                "Soluções rápidas:\n"
                "1. Verifique se o Site ID está correto (encontre-o na URL do painel Wix)\n"
                "2. Certifique-se de que você tem permissões de administrador no site\n"
                "3. Verifique se a API Key foi gerada para o site correto"
            )
        elif e.response.status_code == 404:
            raise PreFlightCheckError("O endpoint da API não foi encontrado. Verifique se a URL base está correta.")
        else:
            raise PreFlightCheckError(f"Erro inesperado ao verificar as credenciais (HTTP {e.response.status_code}): {e}")
    except requests.RequestException as e:
        raise PreFlightCheckError(f"Erro de rede ao tentar se conectar com a API do Wix: {e}")

    # Check 2: Wix Blog app installation (optional check)
    try:
        response_data = response.json()
        if "apps" in response_data:
            installed_apps = response_data.get("apps", [])
            is_blog_installed = any(app.get("id") == WIX_BLOG_APP_ID for app in installed_apps)

            if not is_blog_installed:
                print("[WARNING] Não foi possível verificar se o aplicativo 'Wix Blog' está instalado.")
                print("[WARNING] Certifique-se de que o aplicativo 'Wix Blog' está instalado no seu site para que a migração funcione corretamente.")
        else:
            print("[INFO] Informações sobre aplicativos não disponíveis na resposta da API.")
    except (KeyError, ValueError) as e:
        print(f"[WARNING] Não foi possível processar a resposta da API: {e}")
        print("[WARNING] Certifique-se de que o aplicativo 'Wix Blog' está instalado no seu site.")

    print("[INFO] Pre-flight checks concluídos com sucesso!")
    print("[INFO] As credenciais do Wix parecem estar funcionando corretamente.")
