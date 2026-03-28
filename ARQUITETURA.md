# Arquitetura Técnica — Artificiall Ops Manager

**Versão:** 1.0  
**Data:** 27/03/2026  
**Autor:** Aria (Architect)  
**Projeto:** Artificiall Ops Manager  
**Plataforma:** AIOX (Artificiall Intelligence Operations X)

---

## 1. Visão Geral da Arquitetura

Sistema de gestão operacional baseado em bot Telegram, utilizando Google Sheets como banco de dados principal e integração com Zoom API para reuniões. Arquitetura serverless orientada a eventos via webhooks do Telegram.

---

## 2. Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ECOSISTEMA ARTIFICIALL                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Telegram   │         │      AIOX        │         │  Google Sheets  │
│    Users     │◄───────►│   Core Engine    │◄───────►│   (Database)    │
│  (Bot API)   │  Webhook│  (Agent Runtime) │  REST   │                 │
└──────────────┘         └──────────────────┘         └─────────────────┘
       │                          │                          │
       │                          │                          │
       ▼                          ▼                          ▼
┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Comandos:   │         │  Processamento:  │         │  Abas:          │
│  /cheguei    │         │  - Auth & RBAC   │         │  - Funcionários │
│  /fui        │         │  - Parse Command │         │  - Ponto        │
│  /registrar  │         │  - Log Operations│         │  - Decisões     │
│  /reuniao    │         │  - Timezone BR   │         └─────────────────┘
│  /decisao    │         └──────────────────┘
└──────────────┘                  │
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Zoom API      │
                         │  (OAuth 2.0)     │
                         │  Create Meeting  │
                         └──────────────────┘
```

### Fluxo de Dados

```
[Telegram User] 
      │
      │ 1. Envia comando via Telegram Bot
      ▼
[Telegram Bot API]
      │
      │ 2. Webhook POST /webhook/telegram
      ▼
[AIOX Agent Runtime]
      │
      │ 3. Parse message → Extrai comando + parâmetros
      │ 4. Valida autenticação (telegram_id)
      │ 5. Verifica permissão (cargo/role)
      │
      ├─► [Google Sheets] → CRUD operations
      │        │
      │        │ 6. Read/Write rows
      │        ▼
      │   [Response Data]
      │
      ├─► [Zoom API] → Create meeting (apenas /reuniao)
      │        │
      │        │ 7. POST /meetings
      │        ▼
      │   [Meeting URL]
      │
      ▼
[Response Builder]
      │
      │ 8. Formata resposta personalizada
      ▼
[Telegram Bot API] → Envia mensagem de resposta ao usuário
```

---

## 3. Estrutura de Pastas do Projeto

```
Artificiall Ops Manager/
│
├── .aiox-agent/                  # Configuração do agente AIOX
│   ├── agent.json                # Metadata do agente
│   └── system_prompt.md          # Prompt principal (PRD Seção 5)
│
├── config/                       # Configurações do sistema
│   ├── settings.py               # Variáveis de ambiente e constantes
│   ├── timezone.py               # Configuração America/Sao_Paulo
│   └── permissions.json          # Mapeamento de cargos e permissões
│
├── handlers/                     # Handlers de comandos
│   ├── __init__.py
│   ├── checkpoint.py             # /cheguei e /fui
│   ├── register.py               # /registrar
│   ├── meeting.py                # /reuniao
│   └── decision.py               # /decisao
│
├── integrations/                 # Integrações externas
│   ├── __init__.py
│   ├── google_sheets.py          # CRUD Google Sheets API
│   ├── zoom_api.py               # Zoom Meeting API
│   └── telegram_bot.py           # Telegram Bot wrapper
│
├── models/                       # Modelos de dados
│   ├── __init__.py
│   ├── employee.py               # Modelo Funcionário
│   ├── timesheet.py              # Modelo Ponto
│   └── decision.py               # Modelo Decisão
│
├── middleware/                   # Middleware de processamento
│   ├── __init__.py
│   ├── auth.py                   # Autenticação e RBAC
│   ├── logger.py                 # Logger de operações
│   └── timezone.py               # Conversão de timezone
│
├── logs/                         # Logs de operações
│   ├── operations.log            # Log de todas as operações
│   └── errors.log                # Log de erros
│
├── tests/                        # Testes unitários e integração
│   ├── __init__.py
│   ├── test_checkpoint.py
│   ├── test_register.py
│   ├── test_meeting.py
│   └── test_decision.py
│
├── scripts/                      # Scripts utilitários
│   ├── setup_sheets.py           # Cria abas iniciais
│   └── seed_admins.py            # Popula administradores
│
├── .env                          # Variáveis de ambiente (não versionar)
├── .env.example                  # Exemplo de variáveis
├── requirements.txt              # Dependências Python
├── README.md                     # Documentação de uso
└── ARQUITETURA.md                # Este documento
```

---

## 4. Stack Tecnológico Recomendado

### 4.1 Core

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Runtime** | Python 3.10+ | Compatibilidade com AIOX e bibliotecas Google/Zoom |
| **Framework Bot** | python-telegram-bot v20+ | Assíncrono, maduro, bem documentado |
| **Google Sheets** | gspread v5+ + google-auth | API oficial Google, suporte a OAuth 2.0 |
| **Zoom API** | requests + OAuth2Client | Leve, direto à API REST do Zoom |
| **Timezone** | pytz ou zoneinfo | Suporte nativo America/Sao_Paulo |

### 4.2 Dependências (requirements.txt)

```txt
python-telegram-bot>=20.0
gspread>=5.9.0
google-auth>=2.20.0
google-auth-oauthlib>=1.0.0
requests-oauthlib>=1.3.1
pytz>=2023.3
python-dotenv>=1.0.0
aiox-core>=1.0.0
```

### 4.3 Variáveis de Ambiente (.env)

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram

# Google Sheets
GOOGLE_SHEET_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service_account.json

# Zoom API
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
ZOOM_REDIRECT_URI=https://your-domain.com/auth/zoom

# AIOX Core
AIOX_AGENT_ID=artificiall_ops_manager
AIOX_LOG_LEVEL=INFO

# Timezone
TIMEZONE=America/Sao_Paulo

# Admin IDs (Telegram)
ADMIN_TELEGRAM_IDS=123456789,987654321
CEO_TELEGRAM_ID=123456789
```

---

## 5. Modelo de Dados (Google Sheets)

### 5.1 Aba: Funcionários

| Coluna | Campo | Tipo | Obrigatório | Exemplo |
|--------|-------|------|-------------|---------|
| A | `telegram_id` | Texto | Sim | `123456789` |
| B | `nome` | Texto | Sim | `Daniele Silva` |
| C | `numero` | Texto | Sim | `+5511999998888` |
| D | `data_cadastro` | DateTime | Sim | `27/03/2026 10:30:00` |
| E | `cargo` | Texto | Sim | `Analista de Marketing` |
| F | `ativo` | Boolean | Sim | `TRUE` |
| G | `role` | Texto | Sim | `funcionario` |

**Chave primária:** `telegram_id` (coluna A)  
**Índices:** `nome` (coluna B) para busca por nome

### 5.2 Aba: Ponto

| Coluna | Campo | Tipo | Obrigatório | Exemplo |
|--------|-------|------|-------------|---------|
| A | `id` | Texto (UUID) | Sim | `abc123-def456` |
| B | `telegram_id` | Texto | Sim | `123456789` |
| C | `nome` | Texto | Sim | `Daniele Silva` |
| D | `tipo` | Texto | Sim | `Entrada` ou `Saída` |
| E | `timestamp` | DateTime | Sim | `27/03/2026 08:00:00` |
| F | `data` | Date | Sim | `27/03/2026` |
| G | `timezone` | Texto | Sim | `America/Sao_Paulo` |

**Chave primária:** `id` (coluna A)  
**Índices:** `telegram_id` + `data` para consultas diárias

### 5.3 Aba: Decisões

| Coluna | Campo | Tipo | Obrigatório | Exemplo |
|--------|-------|------|-------------|---------|
| A | `id` | Texto (UUID) | Sim | `dec789-xyz012` |
| B | `data` | DateTime | Sim | `27/03/2026 14:30:00` |
| C | `decisao` | Texto (long) | Sim | `Aprovo a contratação de...` |
| D | `registrado_por` | Texto | Sim | `Gean Santos` |
| E | `ceo_telegram_id` | Texto | Sim | `123456789` |
| F | `categoria` | Texto | Opcional | `RH`, `Financeiro`, `Estratégia` |

**Chave primária:** `id` (coluna A)  
**Índices:** `data` para ordenação cronológica

---

## 6. Fluxos de Comandos

### 6.1 `/cheguei` — Registro de Entrada

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO: /cheguei                                             │
└─────────────────────────────────────────────────────────────┘

1. [Telegram] → Usuário envia "/cheguei"
       │
2. [Handler: checkpoint.py] → Parse command
       │
3. [Middleware: auth.py] → Valida telegram_id
       │
4. [Integration: google_sheets.py] → Lookup na aba "Funcionários"
       │
       ├─► [Usuário NÃO encontrado]
       │      │
       │      └─► Resposta: "❌ Você não está cadastrado. 
       │             Peça ao administrador para te registrar 
       │             com /registrar."
       │
       └─► [Usuário encontrado]
              │
5. [Middleware: timezone.py] → Get timestamp (America/Sao_Paulo)
              │
6. [Integration: google_sheets.py] → Create Row na aba "Ponto"
       │      - telegram_id
       │      - nome (da base)
       │      - tipo: "Entrada"
       │      - timestamp: YYYY-MM-DD HH:MM:SS
       │      - data: YYYY-MM-DD
       │
7. [Middleware: logger.py] → Log operação em operations.log
       │
8. [Response] → "✅ Ponto de entrada registrado, {{nome}}! 
                 Horário: {{timestamp}}"
```

### 6.2 `/fui` — Registro de Saída

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO: /fui                                                 │
└─────────────────────────────────────────────────────────────┘

Mesmo fluxo do /cheguei, alterando apenas:
- tipo: "Saída" na aba "Ponto"
- Mensagem: "✅ Ponto de saída registrado, {{nome}}!"
```

### 6.3 `/registrar @user [Nome] [Número] [Cargo]` — Cadastro de Funcionário

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO: /registrar                                           │
└─────────────────────────────────────────────────────────────┘

1. [Telegram] → Admin envia "/registrar @daniele Daniele Silva +5511999998888 Analista"
       │
2. [Handler: register.py] → Parse command + parâmetros
       │
3. [Middleware: auth.py] → Verifica se telegram_id está em ADMIN_TELEGRAM_IDS
       │
       ├─► [NÃO é admin]
       │      │
       │      └─► Resposta: "❌ Você não tem permissão para 
       │             realizar registros."
       │
       └─► [É admin]
              │
4. [Validation] → Valida formato dos parâmetros
       │      - telegram_id: extraído de @user
       │      - nome: string não vazia
       │      - número: formato internacional
       │      - cargo: string não vazia
       │
5. [Integration: google_sheets.py] → Create Row na aba "Funcionários"
       │      - telegram_id
       │      - nome
       │      - numero
       │      - data_cadastro: timestamp atual
       │      - cargo
       │      - ativo: TRUE
       │      - role: "funcionario"
       │
6. [Middleware: logger.py] → Log operação
       │
7. [Response] → "✅ Funcionário {{nome}} registrado com sucesso 
                 na base da Artificiall."
```

### 6.4 `/reuniao [tema]` — Criação de Reunião Zoom

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO: /reuniao                                             │
└─────────────────────────────────────────────────────────────┘

1. [Telegram] → Usuário envia "/reuniao Alinhamento Semanal"
       │
2. [Handler: meeting.py] → Parse command + tema
       │
3. [Middleware: auth.py] → Valida telegram_id (qualquer funcionário)
       │
4. [Integration: google_sheets.py] → Lookup nome na aba "Funcionários"
       │
5. [Integration: zoom_api.py] → OAuth2 token refresh (se necessário)
       │
6. [Integration: zoom_api.py] → POST /meetings
       │      - topic: "Alinhamento Semanal"
       │      - type: 2 (reunião agendada)
       │      - start_time: timestamp atual
       │      - duration: 60 (padrão)
       │      - timezone: America/Sao_Paulo
       │
7. [Zoom API] → Response com join_url
       │
8. [Telegram Bot] → Anúncio no grupo:
       "🎥 @{{nome_solicitante}}, a reunião '{{tema}}' foi iniciada.
        Link: {{join_url}}"
       │
9. [Middleware: logger.py] → Log operação
```

### 6.5 `/decisao [texto]` — Registro de Decisão Executiva

```
┌─────────────────────────────────────────────────────────────┐
│ FLUXO: /decisao                                             │
└─────────────────────────────────────────────────────────────┘

1. [Telegram] → CEO envia "/decisao Aprovo a contratação de..."
       │
2. [Handler: decision.py] → Parse command + texto
       │
3. [Middleware: auth.py] → Verifica se telegram_id == CEO_TELEGRAM_ID
       │
       ├─► [NÃO é CEO]
       │      │
       │      └─► Resposta: "🔒 Apenas o CEO tem autorização 
       │             para registrar decisões."
       │
       └─► [É CEO]
              │
4. [Validation] → Valida texto não vazio (min 10 caracteres)
       │
5. [Integration: google_sheets.py] → Create Row na aba "Decisões"
       │      - id: UUID
       │      - data: timestamp atual
       │      - decisao: texto completo
       │      - registrado_por: "Gean Santos"
       │      - ceo_telegram_id: ID do CEO
       │      - categoria: (opcional, parse do texto)
       │
6. [Middleware: logger.py] → Log operação (nível CRITICAL)
       │
7. [Response] → "✅ Decisão registrada com sucesso no log de 
                 compliance. ID: {{decision_id}}"
```

---

## 7. Segurança e Autenticação

### 7.1 Autenticação

| Mecanismo | Implementação |
|-----------|---------------|
| **Telegram Users** | Validação por `telegram_id` (único e imutável) |
| **Admins** | Lista branca em `ADMIN_TELEGRAM_IDS` (.env) |
| **CEO** | ID único em `CEO_TELEGRAM_ID` (.env) |
| **Google Sheets** | Service Account com escopo limitado (apenas leitura/escrita nas abas do projeto) |
| **Zoom API** | OAuth 2.0 Server-to-Server com refresh token automático |

### 7.2 Autorização (RBAC)

| Cargo | Comandos Permitidos |
|-------|---------------------|
| `funcionario` | `/cheguei`, `/fui`, `/reuniao` |
| `admin` | `/cheguei`, `/fui`, `/reuniao`, `/registrar` |
| `ceo` | Todos os comandos (inclui `/decisao`) |

### 7.3 Proteção de Dados

```python
# Exemplo de middleware de autenticação
async def check_permission(update: Update, required_role: str) -> bool:
    telegram_id = str(update.effective_user.id)
    
    if required_role == "ceo":
        return telegram_id == os.getenv("CEO_TELEGRAM_ID")
    
    if required_role == "admin":
        admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        return telegram_id in admin_ids
    
    return True  # funcionario pode acessar comandos básicos
```

### 7.4 Logs de Segurança

| Evento | Nível de Log | Destino |
|--------|--------------|---------|
| Tentativa de acesso não autorizado | WARNING | operations.log + errors.log |
| Comando /decisao executado | CRITICAL | operations.log (audit trail) |
| Erro de autenticação Zoom | ERROR | errors.log |
| Falha de escrita no Google Sheets | ERROR | errors.log |
| Operação bem-sucedida | INFO | operations.log |

### 7.5 Formato de Log

```json
{
  "timestamp": "2026-03-27T10:30:00-03:00",
  "level": "INFO",
  "command": "/cheguei",
  "telegram_id": "123456789",
  "user_name": "Daniele Silva",
  "action": "timesheet_entry_created",
  "details": {
    "type": "Entrada",
    "sheet_row": 42
  },
  "trace_id": "abc123-def456"
}
```

---

## 8. Critérios de Aceite Técnicos

### 8.1 Funcionais

| ID | Critério | Método de Validação |
|----|----------|---------------------|
| **CA-01** | Bot identifica usuário pelo telegram_id | Teste unitário: lookup na base Funcionários |
| **CA-02** | `/cheguei` registra entrada com timestamp | Teste integração: verifica row criada na aba Ponto |
| **CA-03** | `/fui` registra saída com timestamp | Teste integração: verifica row criada na aba Ponto |
| **CA-04** | `/registrar` cria nova linha em Funcionários | Teste integração: verifica row com todos os campos |
| **CA-05** | `/reuniao` gera link válido do Zoom | Teste manual: clica no link e verifica abertura |
| **CA-06** | `/decisao` só funciona para CEO | Teste de segurança: tenta com ID diferente do CEO |
| **CA-07** | Respostas usam nome do funcionário | Teste unitário: valida template de resposta |
| **CA-08** | Usuários não cadastrados recebem orientação | Teste de fluxo: envia /cheguei sem cadastro prévio |
| **CA-09** | Mensagens sem comando são ignoradas | Teste unitário: handler retorna None |
| **CA-10** | Timestamps em America/Sao_Paulo | Teste unitário: valida timezone do datetime |

### 8.2 Não Funcionais

| ID | Critério | Métrica |
|----|----------|---------|
| **CNF-01** | Latência de resposta | < 2 segundos para comandos simples |
| **CNF-02** | Disponibilidade | 99% (monitoramento via health check) |
| **CNF-03** | Rastreabilidade | 100% das operações logadas |
| **CNF-04** | Concorrência | Suporta 50 requisições simultâneas |
| **CNF-05** | Recuperação de erros | Retry automático (3x) para APIs externas |

### 8.3 Checklist de Deploy

```markdown
- [ ] Planilha Google Sheets criada com 3 abas
- [ ] Service Account Google configurada com permissão de editor
- [ ] Bot Telegram criado e token armazenado em .env
- [ ] Webhook Telegram configurado apontando para AIOX
- [ ] Zoom App criado com OAuth 2.0 credentials
- [ ] Variáveis de ambiente validadas
- [ ] Logs de operações verificados
- [ ] Testes de todos os comandos realizados
- [ ] Admins e CEO cadastrados nas variáveis de ambiente
```

---

## 9. Considerações Finais

### 9.1 Padrões AIOX Adotados

- Estrutura de agentes modular (handlers separados por comando)
- Logs centralizados com trace_id para rastreabilidade
- Integrações encapsuladas em módulos dedicados
- Configurações externalizadas (.env + config/)

### 9.2 Escalabilidade

- Google Sheets: limite de 5 milhões de células (suficiente para ~500k registros de ponto)
- Telegram Bot: limite de 30 mensagens/segundo (adequado para equipe < 100 pessoas)
- Zoom API: limite de 100 reuniões/dia (plano básico)

### 9.3 Evolução Futura

1. **Migração para banco de dados real** (PostgreSQL) quando volume exigir
2. **Dashboard de analytics** (horas trabalhadas, frequência)
3. **Notificações proativas** (lembrete de ponto, reunião prestes a começar)
4. **Integração com sistema de folha de pagamento**

---

**Documento aprovado por:** Aria (Architect)  
**Próximo passo:** Acionar @dev para implementação seguindo esta arquitetura
