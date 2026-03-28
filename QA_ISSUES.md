# QA Issues — Artificiall Ops Manager

**Projeto:** Artificiall Ops Manager
**Data:** 27/03/2026
**QA Responsável:** Quinn (@qa)

---

## 🎯 Hotfix 28/03/2026 - Issues Críticos Corrigidos

**Data da Correção:** 28/03/2026
**Dev Responsável:** Dex (@dev)
**Status:** ✅ CONCLUÍDO
**Testes:** ✅ 31/31 PASSED

### Resumo das Correções

| Issue | Status | Correção |
|-------|--------|----------|
| **QA-C01** | ✅ RESOLVIDO | Implementado `/register_me` + `pending_{username}` + métodos `update_employee_telegram_id()` e `get_employee_by_pending_id()` |
| **QA-C02** | ✅ RESOLVIDO | Removido `decision_text` do log, mantido apenas `text_length` para auditoria sem expor conteúdo |
| **QA-C03** | ✅ RESOLVIDO | Substituído `datetime.strptime()` por `timezone(timedelta(hours=-3))` para compatibilidade Windows |

### Arquivos Modificados

- `handlers/register.py` - Adicionado `handle_register_me()` e lógica de pending ID
- `handlers/decision.py` - Removido texto completo da decisão do log
- `middleware/logger.py` - Corrigido `_get_timestamp()` para Windows
- `integrations/google_sheets.py` - Adicionados métodos `update_employee_telegram_id()` e `get_employee_by_pending_id()`
- `models/employee.py` - Corrigido `to_row()` para retornar `"TRUE"`/`"FALSE"` (string boolean)
- `handlers/__init__.py` - Exportado `handle_register_me`
- `bot.py` - Registrado handler `/register_me`

### Validação

```bash
pytest tests/ -v
# Resultado: 31 passed in 0.40s
```

### Próximos Passos

- [ ] QA validar correções em homologação
- [ ] Atualizar README.md com novo comando `/register_me`
- [ ] Migrar registros "pending" existentes (script futuro)

---

## 🔴 Issues Críticos (Bloqueantes)

### QA-C01: Funcionário registrado com telegram_id="pending"

**Severidade:** CRÍTICO
**Status:** ✅ RESOLVIDO em 28/03/2026 (Hotfix)
**Localização:** `handlers/register.py:142`

#### Descrição

O handler `/registrar` cria um funcionário com `telegram_id = "pending"` como placeholder, pois o Telegram não permite obter o ID de um usuário apenas pelo username. Isso significa que:

1. O funcionário registrado **nunca será identificado** corretamente
2. Quando o funcionário usar `/cheguei`, o bot não encontrará o registro
3. O sistema retornará "Você não está cadastrado" mesmo após registro

#### Solução Implementada (Hotfix 28/03/2026)

**Comando `/register_me` implementado** - Funcionário captura seu próprio telegram_id:

1. Admin registra funcionário com `/registrar @username ...` → cria registro com `telegram_id="pending_{username}"`
2. Funcionário executa `/register_me` → sistema atualiza `pending_{username}` para telegram_id real
3. Funcionário agora pode usar `/cheguei`, `/fui`, `/reuniao` normalmente

**Métodos novos em `google_sheets.py`:**
- `update_employee_telegram_id(pending_id, telegram_id)` - Atualiza ID pendente para real
- `get_employee_by_pending_id(pending_id)` - Busca registro pendente por username

#### Código Problemático

```python
# handlers/register.py:142
telegram_id = "pending"  # Placeholder - NUNCA É ATUALIZADO

employee = Employee(
    telegram_id=telegram_id,  # ❌ SEMPRE SERÁ "pending"
    nome=parsed["nome"],
    numero=parsed["numero"],
    ...
)
```

#### Impacto

- **Funcionalidade afetada:** CA-04 (Registro de funcionário)
- **Usuários afetados:** Todos os novos funcionários
- **Workaround:** Funcionário precisa ser re-registrado manualmente após primeiro contato

#### Reprodução

1. Admin executa: `/registrar @joao João Silva +5511999998888 Desenvolvedor`
2. Bot responde: "✅ Funcionário João Silva registrado com sucesso..."
3. Funcionário (@joao) executa: `/cheguei`
4. Bot responde: "❌ Você não está cadastrado..."

#### Solução Recomendada

**Opção A (Recomendada):** Implementar comando `/register_me` para auto-registro

```python
# handlers/register.py (novo handler)
async def handle_register_me(update, context, sheets, auth, op_logger, tz):
    """Handle /register_me - Self-registration."""
    telegram_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # Check if already registered
    existing = sheets.get_employee(telegram_id)
    if existing:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Você já está cadastrado como {existing.nome}."
        )
        return
    
    # Send registration form/link or notify admin
    message = (
        f"📋 {user_name}, seu ID foi capturado.\n\n"
        f"Um administrador deve completar seu cadastro.\n"
        f"Seu ID: `{telegram_id}`"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode="Markdown"
    )
    # Notify admins
    # ...
```

**Opção B (Quick Fix):** Admin obtém ID manualmente e atualiza

```python
# scripts/update_employee_telegram_id.py
telegram_id = "123456789"  # Obtido via /id bot
sheets.update_employee_telegram_id("pending", telegram_id)
```

**Opção C (Workaround Documentado):** Instruir admin a registrar após funcionário enviar mensagem

---

### QA-C02: Log de decisão expõe texto sensível

**Severidade:** CRÍTICO
**Status:** ✅ RESOLVIDO em 28/03/2026 (Hotfix)
**Localização:** `handlers/decision.py:147`, `middleware/logger.py`

#### Descrição

Decisões executivas são logadas com o **texto completo** da decisão no arquivo `operations.log`. Isso pode expor informações confidenciais como:

- Contratações/demissões
- Salários e benefícios
- Estratégias de negócio
- Dados financeiros

#### Solução Implementada (Hotfix 28/03/2026)

**Texto completo removido do log** - Apenas metadados são logados:

```python
# handlers/decision.py (atualizado)
op_logger.log_critical(
    command="decisao",
    telegram_id=telegram_id,
    user_name="Gean Santos",
    message="Executive decision registered",
    details={
        "decision_id": decision.id,
        "categoria": categoria or "Geral",
        "ceo_telegram_id": telegram_id,
        "text_length": len(decisao_texto),  # Apenas tamanho, não conteúdo
        # SECURITY: decision_text is NOT logged
    },
)
```

#### Código Problemático

```python
# handlers/decision.py:147
op_logger.log_critical(
    command="decisao",
    telegram_id=telegram_id,
    user_name="Gean Santos",
    message="Executive decision registered",
    details={
        "decision_id": decision.id,
        "decision_text": decisao_texto,  # ❌ TEXTO COMPLETO NO LOG
        "categoria": categoria or "Geral",
        "ceo_telegram_id": telegram_id,
    },
)
```

#### Impacto

- **Segurança:** Vazamento de informações confidenciais
- **Compliance:** Potencial violação de LGPD
- **Usuários afetados:** Todos que acessam logs

#### Reprodução

1. CEO executa: `/decisao Aprovo aumento de 30% para João Silva`
2. Arquivo `logs/operations.log` contém:
```json
{
  "timestamp": "2026-03-27T14:30:00-03:00",
  "level": "CRITICAL",
  "command": "decisao",
  "details": {
    "decision_text": "Aprovo aumento de 30% para João Silva",
    ...
  }
}
```

#### Solução Recomendada

**Opção A (Recomendada):** Não logar texto completo, apenas metadados

```python
# handlers/decision.py
op_logger.log_critical(
    command="decisao",
    telegram_id=telegram_id,
    user_name="Gean Santos",
    message="Executive decision registered",
    details={
        "decision_id": decision.id,
        "categoria": categoria or "Geral",
        "ceo_telegram_id": telegram_id,
        "text_length": len(decisao_texto),  # Apenas tamanho, não conteúdo
        # ❌ REMOVER: "decision_text": decisao_texto,
    },
)
```

**Opção B:** Criar log separado com acesso restrito

```python
# middleware/logger.py
def log_critical_decision(self, ...):
    """Log decisões em arquivo separado com permissões restritas."""
    # Log em arquivo com chmod 600
    pass
```

**Opção C (Workaround Imediato):** Restringir acesso ao arquivo de log

```bash
# Produção: chmod 600 logs/operations.log
# Apenas root e gean podem ler
```

---

### QA-C03: Timezone middleware pode falhar em Windows

**Severidade:** CRÍTICO
**Status:** ✅ RESOLVIDO em 28/03/2026 (Hotfix)
**Localização:** `middleware/logger.py:67`

#### Descrição

O método `_get_timestamp()` usa `datetime.strptime("-03:00", "%z").tzinfo` que pode não funcionar corretamente em todos os sistemas operacionais, especialmente Windows.

#### Solução Implementada (Hotfix 28/03/2026)

**Substituído strptime por timedelta** - Compatível com Windows:

```python
# middleware/logger.py (atualizado)
def _get_timestamp(self) -> str:
    """Get current timestamp in ISO 8601 format with timezone."""
    from datetime import timezone, timedelta

    # Fixed offset for America/Sao_Paulo (BRT = UTC-3)
    # Using timedelta instead of strptime for better Windows compatibility
    # Note: Does not handle DST, but acceptable for logging purposes
    tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).isoformat()
```

```python
# middleware/logger.py
def _get_timestamp(self) -> str:
    """Get current timestamp in ISO 8601 format with timezone."""
    from datetime import timezone, timedelta
    
    # Fixed offset for America/Sao_Paulo (BRT = UTC-3)
    # Note: Does not handle DST, but acceptable for logging
    tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).isoformat()
```

**Ou melhor ainda:**

```python
def _get_timestamp(self) -> str:
    """Get current timestamp in ISO 8601 format with timezone."""
    from datetime import timezone
    
    # Use pytz timezone from middleware
    tz = pytz.timezone(self.TIMEZONE_NAME)
    return datetime.now(tz).isoformat()
```

---

## 🟠 Issues Majors

### QA-M01: Sem retry automático para Zoom API

**Severidade:** MAJOR  
**Localização:** `integrations/zoom_api.py`

#### Descrição

A integração Zoom API não implementa retry automático para falhas de rede, violando o critério **CNF-05**.

#### Solução

```python
# integrations/zoom_api.py
from tenacity import retry, stop_after_attempt, wait_exponential

class ZoomAPIIntegration:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        # Existing code...
```

---

### QA-M02: Sem validação de funcionário duplicado

**Severidade:** MAJOR  
**Localização:** `handlers/register.py`

#### Descrição

O sistema não verifica se funcionário já existe antes de criar novo registro.

#### Solução

```python
# handlers/register.py
# Antes de criar, verificar por nome ou telefone
existing = sheets.get_employee_by_nome(parsed["nome"])
if existing:
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚠️ Funcionário {parsed['nome']} já está cadastrado."
    )
    return
```

---

### QA-M03: Teste de integração Zoom pendente

**Severidade:** MAJOR  
**Localização:** `tests/test_handlers.py`

#### Descrição

HANDOFF_QA.md marca teste de integração Zoom como "Pendente".

#### Solução

```python
# tests/test_handlers.py
class TestMeetingHandler:
    @pytest.mark.asyncio
    async def test_reuniao_creates_zoom_meeting(self, mock_dependencies):
        """Testar /reuniao cria reunião Zoom."""
        mock_dependencies["zoom"].create_meeting.return_value = {
            "join_url": "https://zoom.us/j/123",
            "id": "123"
        }
        # Test implementation...
```

---

### QA-M04: Logs podem expor telegram_id em erro

**Severidade:** MAJOR  
**Localização:** `middleware/logger.py`

#### Descrição

Em caso de erro, o telegram_id é logado junto com stack trace, potencialmente expondo dados em sistemas de log externos.

#### Solução

Implementar filtro de dados sensíveis no logger.

---

### QA-M05: Inconsistência: meeting.py não verifica cadastro

**Severidade:** MINOR  
**Localização:** `handlers/meeting.py:52`

#### Descrição

`/reuniao` permite que usuários não cadastrados criem reuniões, enquanto `/cheguei` não permite.

#### Solução

```python
# handlers/meeting.py
if not employee:
    message = "⚠️ Você não está cadastrado. Reunião será criada mas não será associada ao seu registro."
    # Ou bloquear completamente como checkpoint
```

---

## 🟡 Issues Minors

| ID | Issue | Localização | Prioridade |
|----|-------|-------------|------------|
| **QA-m01** | Validação incompleta em settings.py | `config/settings.py:52` | Baixa |
| **QA-m02** | Type hint inconsistente em TimesheetEntry | `models/timesheet.py:57` | Baixa |
| **QA-m03** | Docstring faltando em `__init__.py` | `handlers/__init__.py` | Baixa |
| **QA-m04** | Hardcode de CEO name | `handlers/decision.py:98` | Baixa |

---

## 📊 Resumo

| Severidade | Quantidade | Bloqueante |
|------------|------------|------------|
| **Crítico** | 3 | ✅ Sim |
| **Major** | 5 | ❌ Não |
| **Minor** | 4 | ❌ Não |
| **Total** | **12** | **3 bloqueantes** |

---

## ✅ Critérios de Resolução

Um issue é considerado **resolvido** quando:

1. ✅ Código foi corrigido
2. ✅ Teste foi adicionado (se aplicável)
3. ✅ QA validou a correção
4. ✅ Documentação foi atualizada (se necessário)

---

**Documento criado por:** Quinn (@qa)  
**Data:** 27/03/2026  
**Próxima atualização:** Após hotfixes
