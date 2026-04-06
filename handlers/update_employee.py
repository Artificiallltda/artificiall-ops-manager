"""
Handler de Atualização de Funcionários (/atualizar) para Artificiall Ops Manager.

Permite que administradores atualizem dados de funcionários existentes.
"""

import logging
from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes

from integrations.excel_api import ExcelOnlineIntegration, ExcelReadOnlyError
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware

logger = logging.getLogger(__name__)


def parse_update_command(args: List[str]) -> Optional[dict]:
    """
    Parse /atualizar command arguments.
    Expected: /atualizar "Nome Completo" campo novo_valor
    Or: /atualizar @username campo novo_valor
    """
    if len(args) < 3:
        return None

    texto = " ".join(args)
    search_term = ""
    campo = ""
    novo_valor = ""

    valid_fields = ["email", "cargo", "numero", "nome", "username"]

    # Extrair search_term se estiver entre aspas duplas, caso contrário busca pelo nome do campo
    if texto.startswith('"'):
        end_quote = texto.find('"', 1)
        if end_quote != -1:
            search_term = texto[1:end_quote].strip()
            rest = texto[end_quote + 1:].strip().split(" ", 1)
            if len(rest) == 2:
                campo, novo_valor = rest
        else:
            return None
    else:
        tokens = texto.split()
        for i, token in enumerate(tokens):
            if token.lower() in valid_fields:
                search_term = " ".join(tokens[:i]).strip()
                campo = token.lower()
                novo_valor = " ".join(tokens[i+1:]).strip()
                break
                
    if not search_term or not campo or not novo_valor:
        return None

    # Se usou @ no começo, vamos tirar
    if search_term.startswith("@"):
        search_term = search_term[1:]

    return {
        "search_term": search_term,
        "campo": campo,
        "novo_valor": novo_valor
    }


async def handle_atualizar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """Handle /atualizar command - Update employee records."""
    if not update.effective_user or not update.effective_chat:
        return

    admin_telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    admin_name = update.effective_user.first_name or "Administrador"

    # Step 1: Check admin permission
    if not auth.is_admin(admin_telegram_id):
        message = "❌ Você não tem permissão para realizar atualizações."
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    # Step 2: Parse command args
    args = context.args or []
    parsed = parse_update_command(args)

    if not parsed:
        message = (
            "❌ *Formato inválido.*\n\n"
            "Use: `/atualizar @username campo novo_valor`\n"
            "Ou: `/atualizar \"Nome do Funcionario\" campo novo_valor`\n\n"
            "Campos válidos: `email`, `cargo`, `numero`, `nome`, `username`\n\n"
            "Exemplo:\n"
            "`/atualizar @daniele email novo.email@empresa.com`"
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return

    search_term = parsed["search_term"]
    campo = parsed["campo"]
    novo_valor = parsed["novo_valor"]

    # Mapear campo para o indice da coluna
    mapping = {
        "nome": sheets.FUNCIONARIOS_COLS["nome"],
        "numero": sheets.FUNCIONARIOS_COLS["numero"],
        "cargo": sheets.FUNCIONARIOS_COLS["cargo"],
        "email": sheets.FUNCIONARIOS_COLS["email"],
        "username": sheets.FUNCIONARIOS_COLS["username"],
    }

    if campo not in mapping:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"❌ Campo inválido: `{campo}`. Campos permitidos: email, cargo, numero, nome, username.", 
            parse_mode="Markdown"
        )
        return

    field_index = mapping[campo]

    try:
        # Step 3: Call Excel to update field
        success = sheets.update_employee_field(search_term, field_index, novo_valor)

        if success:
            message = (
                f"✅ Cadastro atualizado com sucesso!\n\n"
                f"O campo `{campo}` para o registro referente a `{search_term}` foi alterado.\n"
                f"Novo valor: `{novo_valor}`"
            )

            try:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            except Exception as msg_err:
                logger.warning(f"Failed to send success message: {msg_err}")

            op_logger.log_operation(
                command="atualizar",
                telegram_id=admin_telegram_id,
                user_name=admin_name,
                action="employee_updated",
                details={
                    "search_term": search_term,
                    "field": campo,
                    "new_value": novo_valor,
                },
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"❌ Não foi possível encontrar nenhum funcionário correspondente a `{search_term}` ou a atualização falhou.", 
                parse_mode="Markdown"
            )

    except ExcelReadOnlyError as e:
        message = (
            "⚠️ **ERRO: Banco de Dados em Modo de Leitura**\n\n"
            "O OneDrive/SharePoint foi colocado em modo 'Somente Leitura' pela Microsoft."
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        op_logger.log_error(command="atualizar", telegram_id=admin_telegram_id, user_name=admin_name, error=str(e))
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="❌ Erro inesperado ao tentar atualizar.")
        logger.error(f"Error in handle_atualizar: {e}")
