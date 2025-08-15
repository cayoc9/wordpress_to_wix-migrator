# Guia de Solução de Problemas - WordPress to Wix Migration

## Erro: "Acesso negado pela API do Wix"

Se você está recebendo este erro, isso significa que há um problema com suas credenciais do Wix. Aqui estão as soluções:

### 1. Como obter o Site ID correto

O Site ID do Wix pode ser encontrado de várias maneiras:

**Método 1 - URL do Painel Wix:**
1. Faça login no seu painel Wix (manage.wix.com)
2. Selecione seu site
3. Na URL do navegador, você verá algo como: `https://manage.wix.com/dashboard/SEU_SITE_ID_AQUI/home`
4. O Site ID é a parte longa no meio da URL (geralmente um UUID como `12345678-1234-1234-1234-123456789012`)

**Método 2 - Configurações do Site:**
1. No painel Wix, vá em Configurações > Geral
2. O Site ID estará listado nas informações do site

### 2. Como obter/gerar a API Key

**Para obter uma API Key válida:**
1. Acesse o [Wix Developers](https://dev.wix.com/)
2. Faça login com sua conta Wix
3. Vá em "My Apps" ou "Minhas Aplicações"
4. Crie uma nova aplicação ou use uma existente
5. Gere uma API Key com as permissões necessárias:
   - Leitura de conteúdo do site
   - Gerenciamento de blog (se aplicável)
   - Gerenciamento de aplicativos

### 3. Verificação das Credenciais

**Site ID deve:**
- Ter formato UUID (8-4-4-4-12 caracteres)
- Exemplo: `12345678-1234-1234-1234-123456789012`
- Não conter espaços ou caracteres especiais além de hífens

**API Key deve:**
- Ser uma string longa (geralmente 50+ caracteres)
- Começar com prefixos específicos do Wix
- Não estar expirada
- Ter as permissões corretas

### 4. Permissões Necessárias

Certifique-se de que sua API Key tem as seguintes permissões:
- `sites.read` - Para ler informações do site
- `apps.read` - Para verificar aplicativos instalados
- `blog.read` e `blog.write` - Para migração de posts do blog

### 5. Aplicativos Necessários

Certifique-se de que os seguintes aplicativos estão instalados no seu site Wix:
- **Wix Blog** - Necessário para migração de posts
- Outros aplicativos relacionados ao conteúdo que você deseja migrar

### 6. Testando as Credenciais

Você pode testar suas credenciais manualmente usando curl:

```bash
curl -H "Authorization: Bearer SUA_API_KEY_AQUI" \
     -H "wix-site-id: SEU_SITE_ID_AQUI" \
     "https://www.wixapis.com/apps/v1/instance"
```

**Respostas esperadas:**
- `200 OK` - Credenciais válidas
- `401 Unauthorized` - API Key inválida ou expirada
- `403 Forbidden` - API Key válida mas sem permissões ou Site ID incorreto
- `404 Not Found` - Endpoint incorreto (problema no código)

### 7. Problemas Comuns

**Site ID incorreto:**
- Verifique se você copiou o ID completo
- Certifique-se de que não há espaços extras
- Confirme que é o site correto

**API Key sem permissões:**
- Regenere a API Key com todas as permissões necessárias
- Certifique-se de que você é administrador do site

**API Key expirada:**
- Gere uma nova API Key
- Configure a expiração para um período adequado

### 8. Configuração do arquivo config/migration_config.json

Exemplo de configuração correta:

```json
{
  "wix": {
    "site_id": "12345678-1234-1234-1234-123456789012",
    "api_key": "sua_api_key_muito_longa_aqui",
    "base_url": "https://www.wixapis.com"
  },
  "migration": {
    "dry_run": false,
    "limit": null,
    "wordpress_domain": "meublog.wordpress.com",
    "wix_site_url": "https://www.meusite.com"
  }
}
```

### 9. Contato para Suporte

Se você continuar tendo problemas:
1. Verifique a documentação oficial do Wix Developers
2. Consulte os fóruns da comunidade Wix
3. Entre em contato com o suporte do Wix se necessário

---

**Nota:** Este erro de "Site ID incorreto" na verdade se refere a problemas de autenticação/autorização, não necessariamente ao formato do Site ID. As melhorias neste código agora fornecem mensagens de erro mais precisas.