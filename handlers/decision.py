"""
Handler de Decisões Executivas (/decisao) para Artificiall Ops Manager.

Permite apenas ao CEO registrar decisões executivas no log de compliance.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from integrations.excel_api import ExcelOnlineIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware
from models.decision import Decision

logger = logging.getLogger(__name__)


async def handle_decisao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /decisao command - Register executive decision (CEO only).

    Args:
        update: Telegram update object
        context: Telegram context object
        sheets: Google Sheets integration instance
        auth: Auth middleware instance
        op_logger: Operation logger instance
        tz: Timezone middleware instance
    """
    if not update.effective_user or not update.effective_chat:
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuário"

    # Step 1: Check CEO permission (CRITICAL SECURITY CHECK)
    if not auth.is_ceo(telegram_id):
        message = "🔒 Apenas o CEO tem autorização para registrar decisões."
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_warning(
            command="decisao",
            telegram_id=telegram_id,
            user_name=user_name,
            warning="Unauthorized decision registration attempt - SECURITY VIOLATION",
            details={
                "security_level": "CRITICAL",
                "expected_ceo_id": auth.ceo_id,
                "received_telegram_id": telegram_id,
            },
        )
        return

    # Step 2: Get decision text from command arguments
    args = context.args or []

    if not args:
        message = (
            "❌ Por favor, informe o texto da decisão.\n\n"
            "Use: `/decisao [texto da decisão]`\n\n"
            "Exemplo:\n"
            "`/decisao Aprovo a contratação de João Silva para o cargo de Gerente de Vendas`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    decisao_texto = " ".join(args)

    # Validate minimum length
    if len(decisao_texto) < 10:
        message = (
            "❌ A decisão deve ter pelo menos 10 caracteres.\n\n"
            "Por favor, descreva a decisão de forma mais completa."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    # Step 3: Try to extract category from text (optional)
    # Simple keyword-based categorization
    categoria = None
    keywords_categoria = {
        "RH": ["contratação", "demissão", "promoção", "salário", "benefício", "funcionário"],
        "Financeiro": ["orçamento", "investimento", "pagamento", "receita", "despesa", "financeiro"],
        "Estratégia": ["estratégia", "planejamento", "meta", "objetivo", "direcionamento"],
        "Operacional": ["operação", "processo", "procedimento", "rotina"],
        "Tecnologia": ["tecnologia", "sistema", "software", "infraestrutura", "TI"],
    }

    decisao_lower = decisao_texto.lower()
    for cat, keywords in keywords_categoria.items():
        if any(keyword in decisao_lower for keyword in keywords):
            categoria = cat
            break

    # Step 4: Create decision record
    decision = Decision(
        decisao=decisao_texto,
        registrado_por=user_name,
        ceo_telegram_id=telegram_id,
        categoria=categoria,
        data=tz.get_brazil_timestamp(),
    )

    # Step 5: Save to Google Sheets
    success = sheets.create_decision(decision)

    if success:
        message = (
            f"✅ Decisão registrada com sucesso no log de compliance.\n\n"
            f"🆔 **ID:** `{decision.id}`\n"
            f"📅 **Data:** {tz.format_timestamp(decision.data)}\n"
            f"📋 **Categoria:** {categoria or 'Geral'}\n\n"
            f"_Registro auditável e imutável._"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        # CRITICAL: Log this operation with highest priority
        # SECURITY: Do NOT log full decision text to avoid exposing sensitive information
        op_logger.log_critical(
            command="decisao",
            telegram_id=telegram_id,
            user_name=user_name,
            message="Executive decision registered",
            details={
                "decision_id": decision.id,
                "categoria": categoria or "Geral",
                "ceo_telegram_id": telegram_id,
                "text_length": len(decisao_texto),  # Only length, not content
                # SECURITY: decision_text is NOT logged to protect sensitive information
            },
        )
    else:
        message = (
            "❌ Erro ao registrar decisão.\n\n"
            "Por favor, tente novamente ou verifique a configuração do Google Sheets."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_error(
            command="decisao",
            telegram_id=telegram_id,
            user_name=user_name,
            error="Failed to create decision record",
            details={
                # SECURITY: decision_text is NOT logged even in error cases
                "categoria": categoria or "Geral",
                "text_length": len(decisao_texto),  # Apenas tamanho, não conteúdo
            },
        )
