# Resumo do Projeto e Etapas Concluídas

**Objetivo Principal:**
Corrigir erros de formatação em 260 posts que foram migrados do WordPress para o Wix. O desafio central é a conversão de conteúdo HTML para o formato `rich_content` do Wix, resolvendo problemas específicos como vídeos do YouTube incorporados como texto e parágrafos quebrados.

**Estratégia Definida:**
Após avaliarmos diferentes abordagens (JSON vs. Banco de Dados), decidimos utilizar uma solução robusta e escalável com um banco de dados **DuckDB**. Esta abordagem permitirá análises de dados e consultas complexas para identificar e corrigir os erros de forma eficiente.

**Etapas Concluídas até Agora:**

1. **Configuração do Ambiente:**
    * Ativamos o ambiente virtual Python (`.venv`) para isolar as dependências do projeto.
    * Instalamos as bibliotecas necessárias: `pandas` para manipulação de dados tabulares (CSV) e `duckdb` para o gerenciamento do banco de dados.

2. **Criação e População do Banco de Dados:**
    * Desenvolvemos o script `scripts/initialize_database.py`, que lê o arquivo `docs/posts-otimize - Página1.csv` e cria uma tabela `posts` no banco de dados `data/migration.duckdb`, populando-a com os 264 registros dos posts originais do WordPress.

3. **Desenvolvimento dos Scripts de Coleta de Dados do Wix:**
    * Criamos o script `scripts/refresh_token.py` para automatizar a renovação do token de autenticação da API do Wix.
    * Criamos e refinamos o script `scripts/get_wix_post.py`, que busca as informações de um post específico na API do Wix.
    * Criamos o script orquestrador `scripts/fetch_wix_posts.py` para buscar o conteúdo JSON de cada post migrado no Wix.

4. **Diagnóstico e Correção de Rota:**
    * Identificamos que a busca de posts na API do Wix falhava porque os IDs do WordPress não correspondiam aos do Wix.
    * Ajustamos a estratégia para utilizar um mapeamento entre os sistemas, definindo a necessidade de uma coluna `wix_post_id` para correlacionar os dados corretamente.

---

## Próximas Etapas do Projeto

Com a base de dados e os scripts de coleta prontos, o plano para prosseguir é o seguinte:

1. **Adicionar Coluna de Mapeamento:**
    * Executar o script `scripts/add_wix_id_column.py` para adicionar a coluna `wix_post_id` à tabela `posts` em nosso banco de dados DuckDB.

2. **Popular a Coluna de Mapeamento:**
    * **(Ação do Usuário)** Você executará seu script em desenvolvimento para obter os IDs dos posts do Wix e populará a coluna `wix_post_id` no banco de dados.

3. **Coletar o Conteúdo `rich_content` do Wix:**
    * Após o mapeamento ser concluído, executaremos o script `scripts/fetch_wix_posts.py` para buscar o conteúdo JSON de cada post do Wix e salvá-lo na coluna `wix_content_json`.

4. **Análise e Correção dos Posts:**
    * Com todos os dados centralizados, desenvolveremos scripts para se conectar ao DuckDB, usar SQL para filtrar os posts com erros, e aplicar a lógica de correção, atualizando os posts diretamente na plataforma Wix via API.
