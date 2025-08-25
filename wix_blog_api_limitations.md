# Limitações e Erros da API de Blog do Wix

Este documento detalha os limites de transação e os possíveis erros ao usar a API REST do Blog do Wix.

## Limites de Requisição (Rate Limits)

A API do Wix, incluindo os endpoints do Blog, possui um limite de taxa padrão para garantir a estabilidade da plataforma.

*   **Limite Geral:** 200 requisições por minuto (RPM) por instância de aplicativo.

Exceder esse limite resultará em um erro `429 Too Many Requests`.

## Limites Específicos da API do Blog

Além do limite geral de RPM, existem limitações específicas para as entidades do Blog:

### Posts
*   **Busca de Posts:** É possível recuperar um máximo de **100 posts** por chamada nos endpoints `List Posts` ou `Query Posts`.
*   **Tags por Post:** Cada post pode ter no máximo **30 tags** associadas.
*   **Tamanho da Tag:** Cada tag é limitada a **50 caracteres**.

### Categorias
*   **Total de Categorias:** Um site pode ter no máximo **100 categorias** por idioma.
*   **Categorias por Post:** Cada post pode ser associado a no máximo **10 categorias**.

## Possíveis Erros da API (Códigos de Status HTTP)

Abaixo estão os códigos de status HTTP mais comuns e seus significados no contexto da API do Wix.

*   `200 OK`: A requisição foi bem-sucedida.
*   `400 Bad Request`: A requisição está malformada. Isso geralmente ocorre devido a JSON inválido ou campos obrigatórios ausentes no corpo da requisição. A resposta da API geralmente contém detalhes sobre o erro específico.
*   `401 Unauthorized`: O token de acesso é inválido, expirou ou não tem as permissões necessárias para realizar a ação.
*   `403 Forbidden`: O token de acesso é válido, mas não tem permissão para acessar o recurso específico (por exemplo, tentar editar um post sem as permissões de "Editor de Blog").
*   `404 Not Found`: O recurso solicitado (como um post de blog com um ID específico) não foi encontrado.
*   `429 Too Many Requests`: Você excedeu o limite de taxa da API (200 RPM). Reduza a frequência de suas chamadas.
*   `500 Internal Server Error`: Ocorreu um erro inesperado no servidor do Wix. Se este erro persistir, é recomendado verificar a página de status do Wix ou contatar o suporte.
