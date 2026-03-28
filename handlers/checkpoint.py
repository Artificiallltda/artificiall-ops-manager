"""
Handler de Ponto Eletrônico (/cheguei e /fui) para Artificiall Ops Manager.

Registra entrada e saída de funcionários com timestamp em America/Sao_Paulo.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from integrations.excel_api import ExcelOnlineIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware
from models.employee import Employee
from models.timesheet import TimesheetEntry

logger = logging.getLogger(__name__)


async def handle_cheguei(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /cheguei command - Register employee entry.

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

    # Step 1: Check if user is registered
    employee = sheets.get_employee(telegram_id)

    if not employee:
        # User not registered
        message = (
            "❌ Você não está cadastrado.\n\n"
            "Peça ao administrador para te registrar com o comando:\n"
            "`/registrar @seuusuario [Nome Completo] [Número] [Cargo]`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_warning(
            command="cheguei",
            telegram_id=telegram_id,
            user_name=user_name,
            warning="User not registered",
        )
        return

    # Step 2: Get current timestamp in Brazil timezone
    now = tz.get_brazil_timestamp()

    # Step 3: Create timesheet entry
    entry = TimesheetEntry(
        telegram_id=telegram_id,
        nome=employee.nome,
        tipo="Entrada",
        timestamp=now,
    )

    # Step 4: Log to Google Sheets
    success = sheets.log_timesheet(entry)

    if success:
        # Format response message
        timestamp_str = tz.format_timestamp(now, "%d/%m/%Y às %H:%M")

        message = (
            f"✅ Ponto de entrada registrado, {employee.nome}!\n\n"
            f"🕐 Horário: {timestamp_str}\n"
            f"📍 Fuso: {tz.TIMEZONE_NAME}"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_operation(
            command="cheguei",
            telegram_id=telegram_id,
            user_name=employee.nome,
            action="timesheet_entry_created",
            details={
                "type": "Entrada",
                "timestamp": entry.timestamp.isoformat(),
            },
        )
    else:
        # Error logging timesheet
        message = (
            "❌ Erro ao registrar ponto.\n\n"
            "Por favor, tente novamente ou contate o administrador."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_error(
            command="cheguei",
            telegram_id=telegram_id,
            user_name=employee.nome,
            error="Failed to log timesheet entry",
        )


async def handle_fui(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /fui command - Register employee departure.

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

    # Step 1: Check if user is registered
    employee = sheets.get_employee(telegram_id)

    if not employee:
        # User not registered
        message = (
            "❌ Você não está cadastrado.\n\n"
            "Peça ao administrador para te registrar com o comando:\n"
            "`/registrar @seuusuario [Nome Completo] [Número] [Cargo]`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_warning(
            command="fui",
            telegram_id=telegram_id,
            user_name=user_name,
            warning="User not registered",
        )
        return

    # Step 2: Get current timestamp in Brazil timezone
    now = tz.get_brazil_timestamp()

    # Step 3: Create timesheet entry
    entry = TimesheetEntry(
        telegram_id=telegram_id,
        nome=employee.nome,
        tipo="Saída",
        timestamp=now,
    )

    # Step 4: Log to Google Sheets
    success = sheets.log_timesheet(entry)

    if success:
        # Format response message
        timestamp_str = tz.format_timestamp(now, "%d/%m/%Y às %H:%M")

        message = (
            f"✅ Ponto de saída registrado, {employee.nome}!\n\n"
            f"🕐 Horário: {timestamp_str}\n"
            f"📍 Fuso: {tz.TIMEZONE_NAME}"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_operation(
            command="fui",
            telegram_id=telegram_id,
            user_name=employee.nome,
            action="timesheet_exit_created",
            details={
                "type": "Saída",
                "timestamp": entry.timestamp.isoformat(),
            },
        )
    else:
        # Error logging timesheet
        message = (
            "❌ Erro ao registrar ponto.\n\n"
            "Por favor, tente novamente ou contate o administrador."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_error(
            command="fui",
            telegram_id=telegram_id,
            user_name=employee.nome,
            error="Failed to log timesheet exit",
        )
