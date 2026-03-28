# Artificiall Ops Manager

**Bot de Gestão Operacional via Telegram + AIOX**

---

## 📋 Visão Geral

O **Artificiall Ops Manager** é um agente de inteligência artificial integrado ao Telegram cuja missão é digitalizar e automatizar a gestão operacional interna da Artificiall LTDA.

### Funcionalidades

- ✅ **Ponto Eletrônico** - Registro de entrada (`/cheguei`) e saída (`/fui`)
- 👥 **Cadastro de Funcionários** - Registro via `/registrar` (admins)
- 🎥 **Reuniões Zoom** - Criação automática com `/reuniao [tema]`
- 📋 **Log de Decisões** - Registro de decisões executivas (`/decisao`) - CEO apenas

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.10+
- Telegram Bot Token (obtido via BotFather)
- Google Sheets API configurada (Service Account)
- Zoom API credentials (OAuth 2.0)

### Passo 1: Clonar/Configurar

```bash
cd "Artificiall Ops Manager"
```

### Passo 2: Instalar dependências

```bash
pip install -r requirements.txt
```

### Passo 3: Configurar variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

Edite `.env`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
TELEGRAM_WEBHOOK_URL=https://seu-dominio.com/webhook/telegram

# Google Sheets
GOOGLE_SHEET_ID=id_da_planilha_aqui
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json

# Zoom API
ZOOM_ACCOUNT_ID=seu_account_id
ZOOM_CLIENT_ID=seu_client_id
ZOOM_CLIENT_SECRET=seu_client_secret
ZOOM_REDIRECT_URI=https://seu-dominio.com/auth/zoom

# AIOX Core
AIOX_AGENT_ID=artificiall_ops_manager
AIOX_LOG_LEVEL=INFO

# Timezone
TIMEZONE=America/Sao_Paulo

# Admin IDs (Telegram)
ADMIN_TELEGRAM_IDS=123456789,987654321
CEO_TELEGRAM_ID=123456789
```

### Passo 4: Configurar Google Sheets

1. Crie uma planilha no Google Sheets
2. Compartilhe com o email da Service Account (ex: `ops-bot@project.iam.gserviceaccount.com`)
3. Copie o ID da planilha (parte da URL entre `/d/` e `/edit`)
4. Coloque o ID em `GOOGLE_SHEET_ID` no `.env`

### Passo 5: Executar

**Desenvolvimento (polling):**

```bash
python bot.py
```

**Produção (webhook):**

```bash
# Configure um servidor web (ex: gunicorn, uvicorn)
# Ou use um serviço como Railway, Heroku, AWS Lambda
```

---

## 📱 Comandos Disponíveis

| Comando | Descrição | Permissão |
|---------|-----------|-----------|
| `/cheguei` | Registrar entrada | Todos |
| `/fui` | Registrar saída | Todos |
| `/registrar @user Nome +5511999998888 Cargo` | Cadastrar funcionário | Admin |
| `/reuniao [tema]` | Criar reunião Zoom | Todos |
| `/decisao [texto]` | Registrar decisão executiva | CEO |
| `/help` | Mostrar ajuda | Todos |
| `/start` | Mensagem de boas-vindas | Todos |

---

## 📖 Exemplos de Uso

### Registro de Ponto

```
Usuário: /cheguei
Bot: ✅ Ponto de entrada registrado, Daniele!
     🕐 Horário: 27/03/2026 às 08:00
     📍 Fuso: America/Sao_Paulo
```

### Cadastro de Funcionário

```
Admin: /registrar @joao João Silva +5511999998888 Desenvolvedor
Bot: ✅ Funcionário João Silva registrado com sucesso na base da Artificiall!
```

### Criação de Reunião

```
Usuário: /reuniao Alinhamento Semanal
Bot: 🎥 @usuario, a reunião 'Alinhamento Semanal' foi iniciada.
     📌 Link de acesso: https://zoom.us/j/123456789
     🆔 ID da reunião: 123 456 789
```

### Registro de Decisão

```
CEO: /decisao Aprovo a contratação de Maria Santos para Gerente de Vendas
Bot: ✅ Decisão registrada com sucesso no log de compliance.
     🆔 ID: abc123-def456
     📅 Data: 27/03/2026 14:30:00
     📋 Categoria: RH
```

---

## 🏗️ Estrutura do Projeto

```
Artificiall Ops Manager/
├── .aiox-agent/          # Configuração AIOX
│   └── agent.json
├── config/               # Configurações
│   └── settings.py
├── handlers/             # Handlers de comandos
│   ├── checkpoint.py     # /cheguei, /fui
│   ├── register.py       # /registrar
│   ├── meeting.py        # /reuniao
│   └── decision.py       # /decisao
├── integrations/         # Integrações externas
│   ├── google_sheets.py  # Google Sheets API
│   ├── zoom_api.py       # Zoom API
│   └── telegram_bot.py   # Telegram Bot
├── middleware/           # Middleware
│   ├── auth.py           # Autenticação e RBAC
│   ├── logger.py         # Logger estruturado
│   └── timezone.py       # Timezone America/Sao_Paulo
├── models/               # Modelos de dados
│   ├── employee.py       # Funcionário
│   ├── timesheet.py      # Registro de ponto
│   └── decision.py       # Decisão executiva
├── logs/                 # Logs de operações
│   ├── operations.log
│   └── errors.log
├── tests/                # Testes unitários
├── .env                  # Variáveis de ambiente
├── .env.example          # Exemplo de configuração
├── bot.py                # Aplicação principal
├── requirements.txt      # Dependências
├── README.md             # Este arquivo
├── ARQUITETURA.md        # Documentação de arquitetura
└── TODO.md               # Backlog de tarefas
```

---

## 🔒 Segurança

### Controle de Acesso (RBAC)

| Cargo | Comandos |
|-------|----------|
| `funcionario` | `/cheguei`, `/fui`, `/reuniao` |
| `admin` | + `/registrar` |
| `ceo` | Todos (inclui `/decisao`) |

### Logs de Auditoria

Todas as operações são logadas em JSON com:
- Timestamp
- User ID
- Comando executado
- Ação realizada
- Trace ID para rastreabilidade

---

## 🧪 Testes

Execute os testes:

```bash
pytest tests/ -v
```

---

## 📊 Monitoramento

### Logs

- **operations.log**: Todas as operações do sistema
- **errors.log**: Erros e warnings

### Health Check

```bash
# Verificar se o bot está rodando
curl https://seu-dominio.com/health
```

---

## 🛠️ Troubleshooting

### Bot não responde no Telegram

1. Verifique se o webhook está configurado:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```
2. Verifique logs em `logs/errors.log`

### Erro de autenticação Google Sheets

1. Verifique se o Service Account tem acesso à planilha
2. Confirme que o `GOOGLE_SHEET_ID` está correto
3. Teste com o script `scripts/setup_sheets.py`

### Erro ao criar reunião Zoom

1. Verifique credentials OAuth em `.env`
2. Teste conexão: `python -c "from integrations.zoom_api import ZoomAPIIntegration; z = ZoomAPIIntegration(...); print(z.test_connection())"`

---

## 📞 Suporte

Para suporte, contate:
- **Gean Santos (CEO)** - gean@artificiall.com

---

## 📄 Licença

Uso interno - Artificiall LTDA

---

**Versão:** 1.0.0
**Data:** 27/03/2026
**Autor:** Gean Santos (CEO)
