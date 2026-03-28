# Handoff — Architect para Dev

**Story ID:** OPS-001  
**Story Path:** `Artificiall Ops Manager/PRD_Artificiall_Ops_Manager.md`  
**Status:** Ready for Development  
**Branch:** `feature/artificiall-ops-manager`  
**Data:** 27/03/2026 10:45 BRT

---

## 📦 Contexto da Story

Implementar o **Artificiall Ops Manager**, um bot Telegram para gestão operacional da Artificiall LTDA com:
- Controle de ponto eletrônico (/cheguei, /fui)
- Cadastro de funcionários (/registrar)
- Criação de reuniões Zoom (/reuniao)
- Log de decisões executivas (/decisao)

---

## 🏗️ Arquitetura Definida

**Documento:** `Artificiall Ops Manager/ARQUITETURA.md`

### Stack Tecnológico
| Componente | Tecnologia |
|------------|------------|
| Runtime | Python 3.10+ |
| Bot Framework | python-telegram-bot v20+ |
| Google Sheets | gspread v5+ + google-auth |
| Zoom API | requests + OAuth2Client |
| Timezone | pytz (America/Sao_Paulo) |

### Estrutura de Pastas
```
Artificiall Ops Manager/
├── .aiox-agent/          # Configuração AIOX
├── config/               # Settings, permissions
├── handlers/             # checkpoint, register, meeting, decision
├── integrations/         # google_sheets, zoom_api, telegram_bot
├── models/               # employee, timesheet, decision
├── middleware/           # auth, logger, timezone
├── logs/                 # operations.log, errors.log
├── tests/                # Testes unitários
├── scripts/              # setup_sheets, seed_admins
├── .env.example
├── requirements.txt
└── TODO.md
```

### Modelo de Dados (Google Sheets)
| Aba | Campos Principais |
|-----|-------------------|
| Funcionários | telegram_id, nome, numero, data_cadastro, cargo, ativo, role |
| Ponto | id, telegram_id, nome, tipo, timestamp, data, timezone |
| Decisões | id, data, decisao, registrado_por, ceo_telegram_id, categoria |

---

## ✅ Decisões de Arquitetura

1. **Google Sheets como DB** — Simplicidade e rastreabilidade (PRD Seção 8)
2. **Timezone America/Sao_Paulo** — Todos os timestamps em BRT/BRST
3. **RBAC por telegram_id** — Lista branca em .env para admins e CEO
4. **Logs estruturados em JSON** — Audit trail completo em `operations.log`
5. **Padrão AIOX** — Handlers modulares, integrações encapsuladas

---

## 📁 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `ARQUITETURA.md` | Documento completo de arquitetura técnica |
| `TODO.md` | Backlog com 30+ tarefas detalhadas |
| `HANDOFF_DEV.md` | Este arquivo (handoff para @dev) |

---

## 🚧 Blockers

Nenhum blocker ativo. Aguardando início da implementação.

---

## 🎯 Próxima Ação (para @dev)

1. **Iniciar Fase 1 (Setup)** — TASK-001, TASK-002, TASK-003
2. **Criar estrutura de pastas** conforme ARQUITETURA.md Seção 3
3. **Criar `.env.example`** com variáveis da Seção 4.3
4. **Criar `requirements.txt`** com dependências da Seção 4.2

---

## 📋 Critérios de Aceite (PRD Seção 11)

- [ ] CA-01: Bot identifica usuário pelo telegram_id
- [ ] CA-02: `/cheguei` registra entrada com timestamp
- [ ] CA-03: `/fui` registra saída com timestamp
- [ ] CA-04: `/registrar` cria linha em Funcionários
- [ ] CA-05: `/reuniao` gera link Zoom válido
- [ ] CA-06: `/decisao` só funciona para CEO
- [ ] CA-07: Respostas usam nome do funcionário
- [ ] CA-08: Usuários não cadastrados recebem orientação
- [ ] CA-09: Mensagens sem comando são ignoradas
- [ ] CA-10: Timestamps em America/Sao_Paulo

---

## 📎 Referências

| Documento | Path |
|-----------|------|
| PRD Completo | `Artificiall Ops Manager/PRD_Artificiall_Ops_Manager.md` |
| Arquitetura | `Artificiall Ops Manager/ARQUITETURA.md` |
| Todo List | `Artificiall Ops Manager/TODO.md` |
| System Prompt | PRD Seção 5 |

---

**Handoff criado por:** Aria (@architect)  
**Destinatário:** @dev  
**Prioridade:** Alta  
**Estimativa:** 8-12 horas de desenvolvimento

---

## 🚀 Iniciar Implementação

@dev, você foi convocado para implementar o **Artificiall Ops Manager**.

### Primeiros Passos:
1. Leia o PRD em: `PRD_Artificiall_Ops_Manager.md`
2. Leia a Arquitetura em: `ARQUITETURA.md`
3. Execute as tarefas do TODO.md começando pela Fase 1

**Boa implementação!** 🎯
