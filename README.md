# Ferramenta de Migração de Blog: WordPress para Wix

Esta ferramenta foi projetada para automatizar a migração de posts de blog de uma exportação do WordPress para um site na plataforma Wix, com foco na preservação de conteúdo e SEO.

## Funcionalidades Atuais

- Extração de posts de arquivos de exportação do WordPress (`.xml` e `.csv`).
- Migração de título, conteúdo rico (parágrafos, cabeçalhos, listas, formatação de texto), imagens, URLs (slugs), categorias e tags para o Wix como rascunho.
- Geração de logs detalhados da operação e um mapa de redirecionamento de URLs.

Consulte o arquivo `relatorio_analise.md` para uma análise completa do estado do projeto e dos próximos passos planejados.

## Configuração do Ambiente

Siga os passos abaixo para configurar e executar o projeto localmente.

### 1. Pré-requisitos

- Python 3.8 ou superior
- `pip` (gerenciador de pacotes do Python)

### 2. Crie um Ambiente Virtual

É uma boa prática isolar as dependências do projeto.

```bash
# Navegue até a pasta do projeto
cd migração_wix_wordpress

# Crie o ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
# No macOS/Linux:
source venv/bin/activate
# No Windows:
# venv\Scripts\activate
```

### 3. Instale as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias.

```bash
pip install -r requirements.txt
```

### 4. Configure as Credenciais da API do Wix e Outras Configurações

As credenciais da API do Wix e outras configurações são necessárias para que a ferramenta possa se comunicar com seu site Wix e processar a migração corretamente.

1. Abra o arquivo `config/migration_config.json`.
2. Localize a seção `"wix"` e preencha com seu `site_id` e `api_key`. Localize a seção `"migration"` e preencha com seu `wix_site_url` e `wordpress_domain`:

    ```json
    "wix": {
      "site_id": "SEU_WIX_SITE_ID_AQUI",
      "api_key": "SUA_WIX_API_KEY_AQUI",
      "base_url": "https://www.wixapis.com"
    },
    "migration": {
      "dry_run": false,
      "limit": null,
      "wordpress_domain": "SEU_DOMINIO_WORDPRESS_AQUI",
      "wix_site_url": "SUA_URL_WIX_AQUI"
    }
    ```

    - **Como obter seu Wix Site ID:** Faça login no seu painel Wix, selecione o site e o ID estará na URL do navegador (ex: `https://manage.wix.com/dashboard/SEU_SITE_ID_AQUI/home`).
    - **Como gerar sua Wix API Key:** No painel do seu site Wix, vá em `Configurações` > `Desenvolvimento Avançado` > `Headless` > `API Keys`. Gere uma nova chave e certifique-se de conceder as permissões `Manage Posts` e `Publish Post` para o `Wix Blog`.
    - **Wix Site URL:** A URL completa do seu site Wix (ex: `https://www.meusite.com`).
    - **WordPress Domain:** O domínio do seu antigo blog WordPress (ex: `meublog.wordpress.com` ou `www.meuantigoblog.com`).

## Como Usar

Após a configuração, você pode executar o script de migração.

```bash
# Certifique-se de que seu ambiente virtual está ativado
# Navegue até a pasta do projeto
cd migração_wix_wordpress

# Execute o script de migração
./run_migration.sh
```

O script irá processar os arquivos de exportação do WordPress (`.xml` e `.csv`) localizados na pasta `docs/` e tentará migrar os posts para o seu site Wix. O progresso e quaisquer erros serão registrados no console e em `reports/migration/migration.log`.

Um arquivo `reports/redirect_map.csv` será gerado com o mapeamento das URLs antigas do WordPress para as novas URLs do Wix, útil para configurar redirecionamentos 301.
