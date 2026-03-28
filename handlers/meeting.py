"""
Handler de Reuniões (/reuniao) para Artificiall Ops Manager.

Cria reuniões no Microsoft Teams e anuncia no grupo com link de participação.
Suporta reuniões imediatas e agendadas com data/hora específica.

Formatos aceitos:
  /reuniao [tema]                         → cria imediatamente
  /reuniao [tema] DD/MM/YYYY HH:MM        → agenda para a data/hora informada
"""

import logging
import re
from datetime import datetime
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from integrations.google_sheets import GoogleSheetsIntegration
from integrations.teams_api import TeamsAPIIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware

logger = logging.getLogger(__name__)

# Regex para capturar data DD/MM/YYYY e hora HH:MM no final do argumento
_DATE_TIME_PATTERN = re.compile(
    r"(.*?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s*$"
)


def _parse_scheduled_args(args: list) -> Tuple[str, Optional[datetime]]:
    """
    Extrai o tema e a data/hora agendada dos argumentos do comando.

    Exemplos:
      ["Alinhamento", "Semanal"]               → ("Alinhamento Semanal", None)
      ["Reunião", "29/03/2026", "14:00"]        → ("Reunião", datetime(...))
      ["Reunião", "de", "Time", "29/03/2026", "14:00"] → ("Reunião de Time", datetime(...))

    Returns:
        Tuple (tema, scheduled_time | None)
    """
    full_text = " ".join(args)
    match = _DATE_TIME_PATTERN.match(full_text)

    if match:
        tema = match.group(1).strip()
        date_str = match.group(2)  # DD/MM/YYYY
        time_str = match.group(3)  # HH:MM
        try:
            scheduled_time = datetime.strptime(
                f"{date_str} {time_str}", "%d/%m/%Y %H:%M"
            )
            return tema, scheduled_time
        except ValueError:
            pass  # Data inválida → trata como tema sem agendamento

    return full_text, None


async def handle_reuniao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: GoogleSheetsIntegration,
    teams: TeamsAPIIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    """
    Handle /reuniao command - Create or schedule a Microsoft Teams meeting.

    Args:
        update: Telegram update object
        context: Telegram context object
        sheets: Google Sheets integration instance
        teams: Microsoft Teams API integration instance
        auth: Auth middleware instance
        op_logger: Operation logger instance
        tz: Timezone middleware instance
    """
    if not update.effective_user or not update.effective_chat:
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username

    # Identifica o funcionário na base
    employee = sheets.get_employee(telegram_id)
    display_name = employee.nome if employee else user_name
    mention = f"@{username}" if username else display_name

    # Lê argumentos do comando
    args = context.args or []

    if not args:
        message = (
            "❌ Por favor, informe o tema da reunião.\n\n"
            "📌 *Uso:*\n"
            "`/reuniao [tema]` — cria agora\n"
            "`/reuniao [tema] DD/MM/AAAA HH:MM` — agenda\n\n"
            "📋 *Exemplos:*\n"
            "`/reuniao Alinhamento Semanal`\n"
            "`/reuniao Alinhamento Semanal 29/03/2026 14:00`"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        return

    # Parseia tema e possível data/hora agendada
    tema, scheduled_time = _parse_scheduled_args(args)

    if not tema:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Informe o tema da reunião antes da data/hora.",
            parse_mode="Markdown",
        )
        return

    # Define o horário de início
    is_scheduled = scheduled_time is not None
    start_time = scheduled_time if is_scheduled else tz.get_brazil_timestamp()

    # Valida que o horário agendado não está no passado
    if is_scheduled and scheduled_time < tz.get_brazil_timestamp():
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❌ A data/hora informada já passou.\n\n"
                "Por favor, informe um horário futuro."
            ),
            parse_mode="Markdown",
        )
        return

    # Cria a reunião no Teams
    try:
        meeting = teams.create_meeting(
            topic=tema,
            start_time=start_time,
            duration=60,
            timezone=tz.TIMEZONE_NAME,
        )

        join_url = meeting.get("join_url", "")
        meeting_id = meeting.get("id", "")

        if not join_url:
            raise ValueError("Microsoft Graph did not return a valid join URL")

        # Monta a mensagem de resposta
        if is_scheduled:
            data_formatada = scheduled_time.strftime("%d/%m/%Y às %H:%M")
            message = (
                f"🗓️ {mention}, a reunião **'{tema}'** foi agendada no **Microsoft Teams**.\n\n"
                f"🕐 **Data/Hora:** {data_formatada}\n"
                f"📌 **Link de acesso:** {join_url}\n\n"
                f"_Compartilhe o link com os participantes._"
            )
            action = "teams_meeting_scheduled"
        else:
            message = (
                f"🎥 {mention}, a reunião **'{tema}'** foi iniciada no **Microsoft Teams**.\n\n"
                f"📌 **Link de acesso:** {join_url}\n\n"
                f"_Clique no link acima para participar agora._"
            )
            action = "teams_meeting_created"

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        # Registra a operação no log
        op_logger.log_operation(
            command="reuniao",
            telegram_id=telegram_id,
            user_name=display_name,
            action=action,
            details={
                "topic": tema,
                "meeting_id": meeting_id,
                "join_url": join_url,
                "scheduled": is_scheduled,
                "start_time": start_time.isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Failed to create Teams meeting: {e}")

        message = (
            "❌ Erro ao criar reunião no Microsoft Teams.\n\n"
            "Por favor, verifique se a integração Azure está configurada corretamente "
            "ou contate o administrador.\n\n"
            f"_Detalhes: {str(e)}_"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )

        op_logger.log_error(
            command="reuniao",
            telegram_id=telegram_id,
            user_name=display_name,
            error=f"Failed to create Teams meeting: {e}",
            details={"topic": tema, "scheduled": is_scheduled},
        )

