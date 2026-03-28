"""
Handler de Registro de Funcionários (/registrar) para Artificiall Ops Manager.

Permite que administradores cadastrem novos funcionários na base.
"""

import logging
import re
from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes

from integrations.google_sheets import GoogleSheetsIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware
from models.employee import Employee

logger = logging.getLogger(__name__)


def parse_register_command(args: List[str]) -> Optional[dict]:
    """
    Parse /registrar command arguments.

    Expected format: /registrar @username Nome Completo +5511999998888 Cargo

    Args:
        args: Command arguments list

    Returns:
        Dictionary with parsed data or None if invalid
    """
    if len(args) < 4:
        return None

    # Extract telegram username (optional, for reference)
    username_arg = args[0]
    username = None
    if username_arg.startswith("@"):
        username = username_arg[1:]
        args = args[1:]

    # Need at least 3 more args: nome, numero, cargo
    if len(args) < 3:
        return None

    # Last arg is cargo (may contain spaces)
    # Second to last is numero
    # Everything before is nome

    # Try to find phone number (should match international format)
    numero_idx = None
    for i, arg in enumerate(args):
        # Simple phone validation: starts with + and has digits
        if re.match(r"^\+\d{10,15}$", arg.replace("-", "").replace(" ", "")):
            numero_idx = i
            break

    if numero_idx is None or numero_idx == 0:
        return None

    # Nome is everything before numero
    nome = " ".join(args[:numero_idx])

    # Numero is at numero_idx
    numero = args[numero_idx]

    # Cargo is everything after numero
    cargo = " ".join(args[numero_idx + 1:])

    if not nome or not cargo:
        return None

    return {
        "username": username,
        "nome": nome.strip(),
        "numero": numero.strip(),
        "cargo": cargo.strip(),
    }


async def handle_registrar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: GoogleSheetsIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /registrar command - Register new employee.

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

    admin_telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    admin_name = update.effective_user.first_name or "Administrador"

    # Step 1: Check admin permission
    if not auth.is_admin(admin_telegram_id):
        message = "❌ Você não tem permissão para realizar registros."
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_warning(
            command="registrar",
            telegram_id=admin_telegram_id,
            user_name=admin_name,
            warning="Unauthorized registration attempt",
        )
        return

    # Step 2: Parse command arguments
    # Expected: /registrar @username Nome Completo +5511999998888 Cargo
    args = context.args or []

    if len(args) < 4:
        message = (
            "❌ Formato inválido.\n\n"
            "Use: `/registrar @username Nome Completo +5511999998888 Cargo`\n\n"
            "Exemplo:\n"
            "`/registrar @daniele Daniele Silva +5511999998888 Analista de Marketing`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    parsed = parse_register_command(args)

    if not parsed:
        message = (
            "❌ Não foi possível entender os dados.\n\n"
            "Verifique se o formato está correto:\n"
            "`/registrar @username Nome Completo +5511999998888 Cargo`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    # Step 3: Get telegram_id from the mentioned user
    # Use username-based pending ID for later matching
    username = parsed.get("username")
    if username:
        telegram_id = f"pending_{username}"  # Will be updated when user runs /register_me
    else:
        telegram_id = "pending"  # Fallback for no-username case

    # Step 4: Check if employee already exists by pending ID
    if username:
        existing_pending = sheets.get_employee_by_pending_id(telegram_id)
        if existing_pending:
            message = (
                f"⚠️ Funcionário com username **@{username}** já está cadastrado.\n\n"
                f"Nome registrado: {existing_pending.nome}\n\n"
                f"Use `/registrar` com outro username ou contate o administrador."
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )
            return

    # For now, let's create the employee record
    employee = Employee(
        telegram_id=telegram_id,  # Placeholder
        nome=parsed["nome"],
        numero=parsed["numero"],
        data_cadastro=tz.get_brazil_timestamp(),
        cargo=parsed["cargo"],
        ativo=True,
        role="funcionario",
    )

    success = sheets.create_employee(employee)

    if success:
        # Build instruction message based on whether username was provided
        if username:
            instruction = (
                f"⚠️ **Próximo passo:** Peça para **@{username}** executar o comando:\n\n"
                f"`/register_me`\n\n"
                f"Isso irá vincular o ID do Telegram ao registro automaticamente."
            )
        else:
            instruction = (
                f"⚠️ **Próximo passo:** O funcionário deve executar:\n\n"
                f"`/register_me`\n\n"
                f"Isso irá capturar o ID do Telegram e vincular ao registro."
            )

        message = (
            f"✅ Funcionário **{parsed['nome']}** registrado com sucesso na base da Artificiall!\n\n"
            f"📋 Dados:\n"
            f"• Nome: {parsed['nome']}\n"
            f"• Cargo: {parsed['cargo']}\n"
            f"• Telefone: {parsed['numero']}\n\n"
            f"{instruction}"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_operation(
            command="registrar",
            telegram_id=admin_telegram_id,
            user_name=admin_name,
            action="employee_created",
            details={
                "employee_name": parsed["nome"],
                "cargo": parsed["cargo"],
                "numero": parsed["numero"],
                "registered_by": admin_name,
            },
        )
    else:
        message = (
            "❌ Erro ao registrar funcionário.\n\n"
            "Verifique se o funcionário já não está cadastrado ou contate o administrador."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_error(
            command="registrar",
            telegram_id=admin_telegram_id,
            user_name=admin_name,
            error="Failed to create employee record",
        )


async def handle_register_me(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: GoogleSheetsIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /register_me command - Self-registration for employees.

    Captures user's telegram_id and updates pending record or creates new one.
    """
    if not update.effective_user or not update.effective_chat:
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuário"

    # Step 1: Check if already registered with actual telegram_id
    existing = sheets.get_employee(telegram_id)
    if existing:
        message = (
            f"✅ Você já está cadastrado como **{existing.nome}**.\n\n"
            f"📋 Cargo: {existing.cargo}\n"
            f"📅 Cadastro: {tz.format_timestamp(existing.data_cadastro)}"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    # Step 2: Check if there's a pending record with this username
    username = update.effective_user.username
    if username:
        pending_employee = sheets.get_employee_by_pending_id(f"pending_{username}")
        if pending_employee:
            # Update telegram_id
            success = sheets.update_employee_telegram_id(f"pending_{username}", telegram_id)
            if success:
                message = (
                    f"✅ Cadastro atualizado com sucesso, **{pending_employee.nome}**!\n\n"
                    f"Seu ID do Telegram foi vinculado ao seu registro.\n\n"
                    f"📋 Agora você já pode usar:\n"
                    f"• `/cheguei` - Registrar entrada\n"
                    f"• `/fui` - Registrar saída\n"
                    f"• `/reuniao` - Criar reunião Zoom"
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown",
                )

                op_logger.log_operation(
                    command="register_me",
                    telegram_id=telegram_id,
                    user_name=user_name,
                    action="employee_telegram_id_updated",
                    details={
                        "employee_name": pending_employee.nome,
                        "previous_id": f"pending_{username}",
                        "new_id": telegram_id,
                    },
                )
                return

    # Step 3: No pending record - create new self-registration
    # Ask user to provide details or notify admin
    message = (
        f"📋 **Auto-registro iniciado, {user_name}!**\n\n"
        f"Seu ID do Telegram: `{telegram_id}`\n\n"
        f"Um administrador deve completar seu cadastro com:\n"
        f"• Nome completo\n"
        f"• Cargo\n"
        f"• Telefone\n\n"
        f"_Após o cadastro, use `/cheguei` ou `/fui` para registrar seu ponto._"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown",
    )

    # Notify admins (optional - log for now)
    op_logger.log_operation(
        command="register_me",
        telegram_id=telegram_id,
        user_name=user_name,
        action="employee_self_registration_initiated",
        details={
            "username": username,
            "status": "pending_admin_completion",
        },
    )
