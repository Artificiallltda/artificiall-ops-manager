"""
Handler de Registro de Funcionários (/registrar) para Artificiall Ops Manager.

Permite que administradores cadastrem novos funcionários na base.
"""

import logging
import re
from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes

from integrations.excel_api import ExcelOnlineIntegration, ExcelReadOnlyError
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware
from models.employee import Employee

logger = logging.getLogger(__name__)


def parse_register_command(args: List[str]) -> Optional[dict]:
    """
    Parse /registrar command arguments.
    Expected: /registrar @username Nome Completo +5511999998888 email@empresa.com Cargo
    """
    if len(args) < 5:
        return None

    # 1. Username
    username_arg = args[0]
    username = None
    if username_arg.startswith("@"):
        username = username_arg[1:]
        args = args[1:]

    # Join the rest to search using regex
    text = " ".join(args)

    # 2. Email
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    if not email_match:
        return None
    email = email_match.group(0)

    # 3. Telefone: procura por um + seguido por digitos, espacos e hifens.
    phone_match = re.search(r"\+[\d\s\-]{10,20}", text)
    if not phone_match:
        return None
    
    numero_raw = phone_match.group(0).strip()
    numero_digits = re.sub(r"[^\d]", "", numero_raw)
    if len(numero_digits) < 10:
        return None
    numero = "+" + numero_digits

    # 4. Nome e Cargo
    phone_start = text.find(phone_match.group(0))
    nome = text[:phone_start].strip()

    email_end = text.find(email) + len(email)
    cargo = text[email_end:].strip()

    if not nome or not cargo:
        return None

    return {
        "username": username,
        "nome": nome,
        "numero": numero,
        "email": email,
        "cargo": cargo,
    }


async def handle_registrar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
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

    if len(args) < 5:
        message = (
            "❌ *Formato inválido.*\n\n"
            "Use: `/registrar @username Nome +55... email@empresa.com Cargo`\n\n"
            "Exemplo:\n"
            "`/registrar @daniele Daniele Silva +5511999998888 dani@empresa.com Analista`"
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return

    parsed = parse_register_command(args)
    if not parsed:
        message = "❌ Erro ao processar os dados. Verifique o uso de e-mail e telefone."
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return

    username = parsed.get("username").lower() if parsed.get("username") else None
    telegram_id = f"pending_{username}" if username else "pending"

    try:
        if username:
            existing_pending = sheets.get_employee_by_pending_id(telegram_id)
            if existing_pending:
                await context.bot.send_message(chat_id=chat_id, text=f"⚠️ @{username} já registrado.")
                return

        # Check if name is already registered to avoid duplicates (QA-M02)
        # Using existing data logic
        try:
            rows = sheets._get_table_rows(sheets.TABLE_FUNCIONARIOS)
            for row in rows:
                if len(row) > sheets.FUNCIONARIOS_COLS["nome"]:
                    if str(row[sheets.FUNCIONARIOS_COLS["nome"]]).strip().lower() == parsed["nome"].strip().lower():
                        await context.bot.send_message(
                            chat_id=chat_id, 
                            text=f"⚠️ Funcionário **{parsed['nome']}** já está cadastrado no sistema.",
                            parse_mode="Markdown"
                        )
                        return
        except ExcelReadOnlyError:
            raise
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")

        # Cria o objeto com os NOVOS CAMPOS
        employee = Employee(
            telegram_id=telegram_id,
            nome=parsed["nome"],
            numero=parsed["numero"],
            data_cadastro=tz.get_brazil_timestamp(),
            cargo=parsed["cargo"],
            email=parsed["email"],
            username=username or "",
            ativo=True,
            role="funcionario",
        )

        success = sheets.create_employee(employee)

        if success:
            instruction = (
                f"⚠️ **Próximo passo:** Peça para **@{username}** executar `/register_me` no bot para ativar o acesso."
                if username else "⚠️ **Próximo passo:** O funcionário deve executar `/register_me`."
            )

            message = (
                f"✅ **`{parsed['nome']}`** registrado!\n\n"
                f"📧 E-mail: `{parsed['email']}`\n"
                f"👤 Cargo: `{parsed['cargo']}`\n\n"
                f"{instruction}"
            )

            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

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
            raise Exception("Failed to create employee record")
    except ExcelReadOnlyError as e:
        message = (
            "⚠️ **ERRO: Banco de Dados em Modo de Leitura**\n\n"
            "Não foi possível registrar o funcionário porque o OneDrive está bloqueado para escrita pela Microsoft.\n\n"
            "Verifique o espaço em disco ou o status da conta."
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        op_logger.log_error(command="registrar", telegram_id=admin_telegram_id, user_name=admin_name, error=str(e))
    except Exception as e:
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
            error=str(e),
        )


async def handle_register_me(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
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
    try:
        existing = sheets.get_employee(telegram_id)
        if existing:
            message = (
                f"✅ Você já está cadastrado como **`{existing.nome}`**.\n\n"
                f"📋 Cargo: `{existing.cargo}`\n"
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
            username = username.lower()
            pending_employee = sheets.get_employee_by_pending_id(f"pending_{username}")
            
            if not pending_employee:
                # Se não achou na coluna telegram_id como pending_*, tenta achar na coluna username
                pending_employee = sheets.get_employee_by_username(username)
                
            if pending_employee:
                # Update telegram_id na linha do funcionário
                success = sheets.update_employee_field(username, sheets.FUNCIONARIOS_COLS["telegram_id"], telegram_id)
                if success:
                    message = (
                        f"✅ Cadastro atualizado com sucesso, **`{pending_employee.nome}`**!\n\n"
                        f"Seu ID do Telegram foi vinculado ao seu registro.\n\n"
                        f"📋 Agora você já pode usar:\n"
                        f"• `/cheguei` - Registrar entrada\n"
                        f"• `/fui` - Registrar saída\n"
                        f"• `/reuniao` - Criar reunião no Teams/Outlook"
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
    except ExcelReadOnlyError as e:
        message = (
            "⚠️ **ERRO: Banco de Dados em Modo de Leitura**\n\n"
            "Não foi possível completar seu cadastro porque o OneDrive está bloqueado para escrita pela Microsoft."
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        op_logger.log_error(command="register_me", telegram_id=telegram_id, user_name=user_name, error=str(e))
        await context.bot.send_message(chat_id=chat_id, text="❌ Erro ao processar registro.")
