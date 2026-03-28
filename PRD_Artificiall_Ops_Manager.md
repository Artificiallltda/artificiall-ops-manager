# PRD — Artificiall Ops Manager
**Produto:** Bot de Gestão Operacional via Telegram + AIOX  
**Empresa:** Artificiall LTDA  
**Responsável:** Gean Santos (CEO)  
**Versão:** 1.0  
**Data:** 27/03/2026  
**Destino:** Plataforma AIOX (Configuração de Agente AI)

---

## 1. Visão Geral do Produto

O **Artificiall Ops Manager** é um agente de inteligência artificial integrado ao Telegram cuja missão é digitalizar e automatizar a gestão operacional interna da Artificiall LTDA. Ele substitui controles manuais de ponto, atas de decisão e coordenação de reuniões por um sistema de comandos simples e eficiente, com rastreabilidade total via Google Sheets e integração com a API do Zoom.

---

## 2. Objetivos

- Automatizar o registro de ponto eletrônico dos colaboradores.
- Centralizar o log de decisões executivas com controle de acesso por cargo.
- Facilitar a criação de reuniões Zoom com anúncio automático no grupo.
- Manter base de dados de funcionários atualizada diretamente pela conversa no Telegram.
- Garantir rastreabilidade e compliance das ações operacionais da equipe.

---

## 3. Público-Alvo

| Perfil | Descrição |
|---|---|
| **Funcionários** | Usuários do Telegram que registram ponto e participam de reuniões |
| **Administradores** | Responsáveis pelo cadastro de novos membros na base |
| **CEO (Gean Santos)** | Único com permissão para registrar decisões executivas |

---

## 4. Persona do Agente

> **Nome:** Artificiall Ops Manager  
> **Papel:** Gerente de Operações Virtual  
> **Tom de Voz:** Sóbrio, executivo e eficiente  
> **Característica:** Analítico, profissional, focado em logs de dados. Sempre chama os funcionários pelo nome registrado na base.

---

## 5. System Prompt (Configuração no AIOX)

```
Você é o Gerente de Operações Virtual da Artificiall LTDA. Sua missão é manter a produtividade da equipe, gerir a jornada de trabalho e centralizar a comunicação executiva. Você é analítico, profissional e focado em logs de dados.

**Identificação Personalizada:**
Consulte a base de dados (Aba "Funcionários") para identificar o usuário pelo ID do Telegram. Sempre que um funcionário bater ponto ou enviar uma informação, chame-o pelo nome registrado.
Exemplo: "Ponto de entrada registrado, Daniele."

**Registro de Novo Membro:**
Ao receber o comando /registrar, salve os dados na planilha e confirme:
"Funcionário [Nome] registrado com sucesso na base da Artificiall."

**Ponto Eletrônico:**
Registre /cheguei e /fui com Timestamp exata. Se o usuário não estiver cadastrado, oriente que o administrador realize o registro primeiro.

**Gestão de Reuniões (Zoom):**
Ao comando /reuniao [tema], gere o link via API do Zoom e anuncie no grupo:
"🎥 @[Nome do Solicitante], a reunião '[Tema]' foi iniciada. Link: [URL]"

**Log de Decisões:**
Apenas o CEO (@GeanSantos) tem permissão para usar o comando /decisao.
Salve o texto na aba "Log de Decisões".

**Foco Profissional:**
Ignore conteúdos que não sejam comandos ou informações de trabalho. Não responda a dramas, desabafos ou questões pessoais, a menos que interfiram no registro de ponto (falta/presença).
```

---

## 6. Estrutura de Comandos

| Comando | Ação | Trigger no AIOX | Destino |
|---|---|---|---|
| `/registrar @user [Nome] [Número]` | Cadastra novo funcionário | Create Row | Aba **Funcionários** (Google Sheets) |
| `/cheguei` | Registra entrada com timestamp | Log Entrada | Aba **Ponto** (Google Sheets) |
| `/fui` | Registra saída com timestamp | Log Saída | Aba **Ponto** (Google Sheets) |
| `/reuniao [tema]` | Cria reunião no Zoom | Zoom API Meeting | Link anunciado no grupo |
| `/decisao [texto]` | Registra decisão executiva | Log Compliance | Aba **Decisões** (Google Sheets) |

---

## 7. Arquitetura de Fluxo no AIOX

### 7.1 Fluxo de Ponto (`/cheguei` e `/fui`)

```
[Trigger: Telegram Message]
        ↓
[Nó de Busca — Google Sheets]
  → Get Row na aba "Funcionários"
  → Chave: ID do Telegram do usuário
        ↓
[Condicional]
  → Usuário encontrado?
    ├── SIM → Registra timestamp na aba "Ponto"
    │         → Resposta: "Ponto registrado, {{nome_funcionario}}!"
    └── NÃO → Resposta: "Você não está cadastrado. Peça ao administrador para te registrar com /registrar."
```

### 7.2 Fluxo de Registro (`/registrar`)

```
[Trigger: Telegram Message — comando /registrar]
        ↓
[Verificação de Permissão]
  → É administrador?
    ├── SIM → Create Row na aba "Funcionários"
    │         → Campos: ID Telegram, Nome, Número, Data de Cadastro
    │         → Resposta: "Funcionário [Nome] registrado com sucesso na base da Artificiall."
    └── NÃO → Resposta: "Você não tem permissão para realizar registros."
```

### 7.3 Fluxo de Reunião (`/reuniao [tema]`)

```
[Trigger: Telegram Message — comando /reuniao]
        ↓
[Nó de Busca — Identifica nome do solicitante]
        ↓
[Zoom API — Create Meeting]
  → Parâmetros: Tema, Data/Hora atual, Duração padrão
        ↓
[Resposta no grupo]
  → "🎥 @[Nome], a reunião '[Tema]' foi iniciada. Link: [URL Zoom]"
```

### 7.4 Fluxo de Decisão (`/decisao [texto]`)

```
[Trigger: Telegram Message — comando /decisao]
        ↓
[Verificação de Permissão]
  → ID Telegram == @GeanSantos?
    ├── SIM → Create Row na aba "Log de Decisões"
    │         → Campos: Data, Texto da Decisão, ID do CEO
    │         → Resposta: "✅ Decisão registrada com sucesso no log de compliance."
    └── NÃO → Resposta: "Apenas o CEO tem autorização para registrar decisões."
```

---

## 8. Estrutura da Planilha Google Sheets

### Aba: Funcionários

| Campo | Tipo | Descrição |
|---|---|---|
| `telegram_id` | Texto | ID único do usuário no Telegram |
| `nome` | Texto | Nome completo do funcionário |
| `numero` | Texto | Número de WhatsApp/telefone |
| `data_cadastro` | Data | Data de registro na base |
| `cargo` | Texto | Cargo/função na empresa |
| `ativo` | Boolean | Status ativo/inativo |

### Aba: Ponto

| Campo | Tipo | Descrição |
|---|---|---|
| `telegram_id` | Texto | ID do usuário |
| `nome` | Texto | Nome do funcionário |
| `tipo` | Texto | "Entrada" ou "Saída" |
| `timestamp` | DateTime | Data e hora exata do registro |
| `data` | Data | Data do ponto |

### Aba: Log de Decisões

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | DateTime | Data e hora da decisão |
| `decisao` | Texto | Texto completo da decisão |
| `registrado_por` | Texto | ID/nome do CEO |

---

## 9. Integrações Necessárias

| Serviço | Finalidade | Tipo de Integração |
|---|---|---|
| **Telegram Bot API** | Canal de comunicação e trigger | Webhook / AIOX Native |
| **Google Sheets API** | Armazenamento de dados (ponto, funcionários, decisões) | AIOX Node (Get/Create Row) |
| **Zoom API** | Criação automática de reuniões | REST API (OAuth 2.0) |

---

## 10. Regras de Negócio

1. **Cadastro prévio obrigatório:** O bot não registra ponto de usuários não cadastrados.
2. **Controle de acesso:** Somente administradores podem usar `/registrar`; somente o CEO pode usar `/decisao`.
3. **Timestamp automático:** Todo registro de ponto deve conter a data e hora exata (timezone: America/Sao_Paulo).
4. **Foco profissional:** O agente deve ignorar mensagens sem comandos válidos e não responder a conteúdo pessoal.
5. **Identificação por nome:** O agente sempre usa o nome registrado na planilha em suas respostas.

---

## 11. Critérios de Aceite

- [ ] O bot identifica corretamente o usuário pelo ID do Telegram.
- [ ] `/cheguei` e `/fui` registram entrada e saída com timestamp na aba Ponto.
- [ ] `/registrar` cria uma nova linha na aba Funcionários.
- [ ] `/reuniao [tema]` gera e anuncia um link válido do Zoom.
- [ ] `/decisao [texto]` só funciona para `@GeanSantos` e registra na aba Decisões.
- [ ] O agente responde pelo nome do funcionário em todas as confirmações.
- [ ] Usuários não cadastrados recebem mensagem orientando o registro.
- [ ] O agente ignora mensagens sem comandos válidos.

---

## 12. Próximos Passos

1. **Configurar Planilha Google Sheets** com as abas e campos definidos na seção 8.
2. **Criar Bot no Telegram** e obter o Token da BotFather.
3. **Configurar agente no AIOX** com o System Prompt da seção 5.
4. **Adicionar Nós de Integração** no AIOX: Google Sheets (Lookup + Create Row) e Zoom API.
5. **Testes de homologação** com equipe interna antes do deploy oficial.
6. **Deploy e treinamento** da equipe para uso dos comandos.

---

*Documento elaborado pela equipe Artificiall LTDA — uso interno e operacional.*
