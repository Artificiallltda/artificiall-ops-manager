# Guia de Validação QA — Hotfix 28/03/2026

**Projeto:** Artificiall Ops Manager  
**Hotfix:** 28/03/2026  
**QA Responsável:** Quinn (@qa)  
**Status:** ✅ Pronto para validação em homologação

---

## 🎯 Objetivo

Este guia descreve os passos para validar as correções do hotfix em ambiente de homologação.

---

## 📋 Pré-requisitos

1. Bot Telegram criado via BotFather
2. Google Sheets configurado com Service Account
3. Arquivo `.env` preenchido com credenciais reais
4. Dependências instaladas: `pip install -r requirements.txt`

---

## 🔍 Validação 1: QA-C01 - Comando /register_me

### Cenário: Registro de novo funcionário

**Passo 1:** Admin registra funcionário

```
Admin envia: /registrar @joao João Silva +5511999998888 Desenvolvedor
```

**Resultado Esperado:**
```
✅ Funcionário **João Silva** registrado com sucesso na base da Artificiall!

📋 Dados:
• Nome: João Silva
• Cargo: Desenvolvedor
• Telefone: +5511999998888

⚠️ **Próximo passo:** Peça para **@joao** executar o comando:

`/register_me`

Isso irá vincular o ID do Telegram ao registro automaticamente.
```

**Validação no Google Sheets:**
- Abrir aba "Funcionários"
- Verificar nova linha com `telegram_id = "pending_joao"`

---

**Passo 2:** Funcionário executa auto-registro

```
@joao envia: /register_me
```

**Resultado Esperado:**
```
✅ Cadastro atualizado com sucesso, **João Silva**!

Seu ID do Telegram foi vinculado ao seu registro.

📋 Agora você já pode usar:
• `/cheguei` - Registrar entrada
• `/fui` - Registrar saída
• `/reuniao` - Criar reunião Zoom
```

**Validação no Google Sheets:**
- Abrir aba "Funcionários"
- Verificar que `telegram_id` foi atualizado de `"pending_joao"` para ID numérico (ex: `"123456789"`)

---

**Passo 3:** Funcionário registra ponto

```
@joao envia: /cheguei
```

**Resultado Esperado:**
```
✅ Ponto de entrada registrado, João Silva!

🕐 Horário: 28/03/2026 às 10:30
📍 Fuso: America/Sao_Paulo
```

**Validação no Google Sheets:**
- Abrir aba "Ponto"
- Verificar nova linha com:
  - `telegram_id` = ID real do funcionário
  - `nome` = "João Silva"
  - `tipo` = "Entrada"
  - `timestamp` = timestamp válido

---

### Critério de Aprovação QA-C01

- [ ] `/registrar` cria registro com `pending_{username}`
- [ ] `/register_me` atualiza `pending_{username}` para telegram_id real
- [ ] `/cheguei` funciona após `/register_me`
- [ ] Google Sheets reflete atualizações corretamente

---

## 🔍 Validação 2: QA-C02 - Log Seguro de Decisões

### Cenário: CEO registra decisão executiva

**Passo 1:** CEO registra decisão

```
CEO envia: /decisao Aprovo a contratação de João Silva como Gerente de Vendas com salário de R$ 10.000
```

**Resultado Esperado:**
```
✅ Decisão registrada com sucesso no log de compliance.

🆔 **ID:** `DEC-20260328-001`
📅 **Data:** 28/03/2026 às 10:30
📋 **Categoria:** RH

_Registro auditável e imutável._
```

---

**Passo 2:** Validar logs

**Arquivo:** `logs/operations.log`

**Buscar por:** `"command": "decisao"`

**Resultado Esperado (JSON):**
```json
{
  "timestamp": "2026-03-28T10:30:00-03:00",
  "level": "CRITICAL",
  "command": "decisao",
  "telegram_id": "123456789",
  "user_name": "Gean Santos",
  "action": "critical",
  "details": {
    "decision_id": "DEC-20260328-001",
    "categoria": "RH",
    "ceo_telegram_id": "123456789",
    "text_length": 95,
    "message": "Executive decision registered"
  },
  "trace_id": "abc-123-def-456"
}
```

**Validação de Segurança:**
- [ ] Campo `decision_text` **NÃO** está presente no log
- [ ] Campo `text_length` está presente (apenas tamanho, não conteúdo)
- [ ] Dados sensíveis (salário, nome) **NÃO** estão expostos no log

---

**Passo 3:** Validar Google Sheets

**Aba:** "Decisões"

**Verificar:**
- [ ] Linha criada com decisão completa (para auditoria)
- [ ] Coluna `decisao` contém texto completo: "Aprovo a contratação de João Silva..."
- [ ] Coluna `categoria` = "RH"

---

### Critério de Aprovação QA-C02

- [ ] `operations.log` NÃO contém texto completo da decisão
- [ ] `operations.log` contém apenas `text_length` (metadado)
- [ ] Google Sheets contém decisão completa (para auditoria legítima)
- [ ] Logs não expõem informações sensíveis

---

## 🔍 Validação 3: QA-C03 - Timezone Windows-Compatible

### Cenário: Timestamp em diferentes sistemas

**Passo 1:** Executar script de validação

```bash
python scripts/validate_hotfix.py
```

**Resultado Esperado:**
```
============================================================
  QA-C03: Validação Timezone Windows-Compatible
============================================================

✅ PASS - strptime removido
   datetime.strptime não é mais usado

✅ PASS - timedelta adicionado
   timezone(timedelta(hours=-3)) usado

✅ PASS - Timestamp gerado é válido
   Timestamp: 2026-03-28T15:18:18.077443-03:00

✅ PASS - Timestamp tem indicador de timezone
```

---

**Passo 2:** Validar logs de operação

**Comando:** `/cheguei`

**Validar:** `logs/operations.log`

**Verificar:**
- [ ] Timestamp no formato ISO 8601: `2026-03-28T10:30:00-03:00`
- [ ] Timezone offset `-03:00` (America/Sao_Paulo)
- [ ] Sem erros de parsing de timezone

---

**Passo 3:** Testar em Windows (se aplicável)

```bash
# Em ambiente Windows
python -c "from middleware.logger import OperationLogger; l = OperationLogger(); print(l._get_timestamp())"
```

**Resultado Esperado:**
- Timestamp válido sem erros
- Formato: `YYYY-MM-DDTHH:MM:SS-03:00`

---

### Critério de Aprovação QA-C03

- [ ] `datetime.strptime("-03:00", "%z")` NÃO está no código
- [ ] `timezone(timedelta(hours=-3))` está implementado
- [ ] Timestamps são gerados corretamente
- [ ] Funciona em Windows e Linux

---

## 🧪 Validação Automatizada

### Executar Script de Validação

```bash
cd "Artificiall Ops Manager"
python scripts/validate_hotfix.py
```

**Resultado Esperado:**
```
============================================================
  RESUMO DA VALIDAÇÃO
============================================================
✅ PASS - QA-C01
✅ PASS - QA-C02
✅ PASS - QA-C03
✅ PASS - TESTES

============================================================
  ✅ TODAS AS VALIDAÇÕES PASSARAM!
  Hotfix pronto para deploy em homologação.
============================================================
```

---

### Executar Testes Unitários

```bash
pytest tests/ -v
```

**Resultado Esperado:**
```
============================= 31 passed in 0.40s ==============================
```

---

## 📊 Checklist de Aprovação QA

### Validação QA-C01

- [ ] `/registrar` com username cria `pending_{username}`
- [ ] `/register_me` atualiza telegram_id corretamente
- [ ] `/cheguei` funciona após `/register_me`
- [ ] `/fui` funciona após `/register_me`
- [ ] Google Sheets atualizado corretamente

### Validação QA-C02

- [ ] `/decisao` não loga texto completo
- [ ] Log contém apenas `text_length`
- [ ] Google Sheets contém decisão completa
- [ ] Logs não expõem dados sensíveis

### Validação QA-C03

- [ ] Timestamp funciona em Windows
- [ ] Timestamp formato ISO 8601
- [ ] Timezone America/Sao_Paulo correto
- [ ] Sem erros de parsing

### Validação Automatizada

- [ ] `python scripts/validate_hotfix.py` passa
- [ ] `pytest tests/ -v` passa (31/31)

---

## ✅ Aprovação Final

| Campo | Valor |
|-------|-------|
| **QA Responsável** | Quinn (@qa) |
| **Data Validação** | ___/___/_____ |
| **Status** | ☐ Aprovado ☐ Reprovado ☐ Aprovado com ressalvas |
| **Observações** | |

### Assinatura QA

**Nome:** _______________________________

**Data:** ___/___/_____

---

## 📎 Referências

- `HOTFIX_28_03_2026.md` - Relatório completo do hotfix
- `QA_ISSUES.md` - Lista detalhada de issues
- `QA_GATE_REPORT.md` - Relatório de QA Gate
- `scripts/validate_hotfix.py` - Script de validação automática

---

*Guia criado em 28/03/2026 para validação do Hotfix*
