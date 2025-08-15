# Análise e Correções Realizadas no Código

## Problema Original
Você estava recebendo o erro: **"O Wix Site ID fornecido está incorreto. Verifique a Etapa A das instruções."**

Mesmo com o Site ID correto, a função `utils` de pre-check acusava erro.

## Análise do Problema

Após investigação detalhada, descobri que o problema **NÃO era realmente o Site ID**, mas sim:

1. **Endpoint incorreto**: O código estava usando `/v1/apps` que não existe
2. **Formato de autenticação incorreto**: Não estava usando `Bearer` token
3. **Mensagens de erro imprecisas**: O código interpretava erro 404 como "Site ID incorreto"
4. **Tratamento de erros limitado**: Não diferenciava entre diferentes tipos de erro HTTP

## Correções Implementadas

### 1. Corrigido o Endpoint da API
```python
# ANTES (incorreto):
apps_url = f"{base_url}/v1/apps"

# DEPOIS (correto):
apps_url = f"{base_url}/apps/v1/instance"
```

### 2. Corrigido o Formato de Autenticação
```python
# ANTES (incorreto):
"Authorization": api_key,

# DEPOIS (correto):
"Authorization": f"Bearer {api_key}",
```

### 3. Melhorado o Tratamento de Erros
- **401 Unauthorized**: API Key inválida ou expirada
- **403 Forbidden**: API Key válida mas sem permissões ou Site ID incorreto
- **404 Not Found**: Endpoint não encontrado (problema no código)

### 4. Mensagens de Erro Mais Precisas
Antes: "O Wix Site ID fornecido está incorreto"
Depois: Mensagens detalhadas explicando possíveis causas e soluções

### 5. Validação de Formato do Site ID
Adicionado aviso se o Site ID não parece ter formato UUID correto.

### 6. Logs Informativos
Adicionados logs para mostrar qual endpoint está sendo testado e o status da conexão.

### 7. Verificação Robusta de Aplicativos
Melhorado o tratamento da verificação do Wix Blog app com fallbacks apropriados.

## Arquivos Modificados

1. **`src/utils/pre_flight_checks.py`** - Correções principais
2. **`TROUBLESHOOTING.md`** - Guia detalhado de solução de problemas
3. **`config/migration_config.json`** - Arquivo de configuração de exemplo

## Resultado Final

Agora o código:
- ✅ Usa o endpoint correto da API do Wix
- ✅ Faz autenticação correta com Bearer token
- ✅ Fornece mensagens de erro precisas e úteis
- ✅ Diferencia entre problemas de API Key e Site ID
- ✅ Inclui guia detalhado de solução de problemas
- ✅ Valida formato das credenciais
- ✅ Fornece logs informativos

## Como Usar Agora

1. **Configure suas credenciais reais** no arquivo `config/migration_config.json`
2. **Se ainda receber erro 403**, consulte o `TROUBLESHOOTING.md`
3. **Verifique se você tem uma API Key válida** com as permissões necessárias
4. **Confirme que o Site ID está correto** (encontre-o na URL do painel Wix)

## Teste Manual das Credenciais

Para testar suas credenciais manualmente:
```bash
curl -H "Authorization: Bearer SUA_API_KEY_REAL" \
     -H "wix-site-id: SEU_SITE_ID_REAL" \
     "https://www.wixapis.com/apps/v1/instance"
```

**Resposta esperada com credenciais válidas:** HTTP 200 OK

---

**Resumo**: O problema original não era o Site ID estar "incorreto", mas sim problemas no código que foram totalmente corrigidos. Agora você receberá mensagens de erro precisas que te ajudarão a resolver qualquer problema de configuração.