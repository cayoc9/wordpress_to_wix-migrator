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
cd wix_migration_tool

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

### 4. Configure as Credenciais da API do Wix

As credenciais da API do Wix são necessárias para que a ferramenta possa se comunicar com seu site Wix.

1. Abra o arquivo `config/migration_config.json`.
2. Localize a seção `"wix"` e preencha com seu `site_id` e `api_key`:

    ```json
    "wix": {
      "site_id": "SEU_WIX_SITE_ID_AQUI",
      "api_key": "SUA_WIX_API_KEY_AQUI",
      "base_url": "https://www.wixapis.com"
    },
    ```

    - **Como obter seu Wix Site ID:** Faça login no seu painel Wix, selecione o site e o ID estará na URL do navegador (ex: `https://manage.wix.com/dashboard/SEU_SITE_ID_AQUI/home`).
    - **Como gerar sua Wix API Key:** No painel do seu site Wix, vá em `Configurações` > `Desenvolvimento Avançado` > `Headless` > `API Keys`. Gere uma nova chave e certifique-se de conceder a permissão `Manage Posts` para o `Wix Blog`.

## Como Usar

Após a configuração, você pode executar o script de migração.

```bash
# Certifique-se de que seu ambiente virtual está ativado
# Navegue até a pasta do projeto
cd wix_migration_tool

# Execute o script principal
python3 main.py
```

O script irá processar os arquivos de exportação do WordPress (`.xml` e `.csv`) localizados na pasta `docs/` e tentará migrar os posts para o seu site Wix. O progresso e quaisquer erros serão registrados no console e em `reports/migration/migration.log`.

Um arquivo `reports/redirect_map.csv` será gerado com o mapeamento das URLs antigas do WordPress para as novas URLs do Wix, útil para configurar redirecionamentos 301.

## Scripts

- `scripts/update_wix_post.js`: Atualiza um post do Wix Blog via API REST.
  - Requisitos: Node 18+, `WIX_API_KEY`, `WIX_SITE_ID`.
  - Uso básico:
    - Atualizar rascunho:
      `node scripts/update_wix_post.js --post-id <uuid> --file data/posts/<arquivo>.json`
    - Atualizar e publicar:
      `node scripts/update_wix_post.js --post-id <uuid> --file data/posts/<arquivo>.json --publish`
  - Fluxo adotado:
    1) Busca o post e obtém `revision`.
    2) Se está publicado, garante rascunho (create-draft quando disponível).
    3) Envia `PATCH` com os campos presentes no JSON local e `revision` atual.
    4) Se `--publish`, chama `publish` ao final.
  - Observações:
    - O ID do post é estável entre rascunho e publicado.
    - A API usa controle por `revision`. Se desatualizada, a API retorna erro de concorrência.
    - É necessário conceder escopo `wix-blog.manage-posts` à API Key.

- `scripts/update_wix_post.py`: Versão equivalente em Python do atualizador de posts.
  - Requisitos: Python 3.8+, `requests`, `WIX_API_KEY`, `WIX_SITE_ID`.
  - Uso básico:
    - Atualizar rascunho:
      `python scripts/update_wix_post.py --post-id <uuid> --file data/posts/<arquivo>.json`
    - Atualizar e publicar:
      `python scripts/update_wix_post.py --post-id <uuid> --file data/posts/<arquivo>.json --publish`
  - Fluxo e observações: idênticos ao script em Node.
