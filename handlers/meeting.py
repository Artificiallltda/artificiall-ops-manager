import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from telegram import Update
from telegram.ext import ContextTypes

from integrations.excel_api import ExcelOnlineIntegration
from integrations.teams_api import TeamsAPIIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware

logger = logging.getLogger(__name__)

# Regex para capturar data DD/MM/YYYY e hora HH:MM
_DATE_TIME_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})")
# Regex simples para e-mails
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _parse_reuniao_args(
    args: List[str], 
    sheets: ExcelOnlineIntegration
) -> Tuple[str, Optional[datetime], List[str]]:
    """
    Extrai tema, data/hora e e-mails dos argumentos.
    Também converte @mentions em e-mails consultando o Excel.
    """
    full_text = " ".join(args)
    
    # 1. Extrair e-mails diretos
    emails = _EMAIL_PATTERN.findall(full_text)
    
    # 2. Extrair @mentions e buscar e-mails no Excel
    mentions = re.findall(r"@(\w+)", full_text)
    for username in mentions:
        employee = sheets.get_employee_by_username(username)
        if employee and employee.email:
            if employee.email not in emails:
                emails.append(employee.email)

    # 3. Limpar o texto de e-mails e menções para processar o tema/data
    text_without_metadata = _EMAIL_PATTERN.sub("", full_text)
    text_without_metadata = re.sub(r"@\w+", "", text_without_metadata).strip()
    
    # 4. Extrair data/hora do texto limpo
    date_match = _DATE_TIME_PATTERN.search(text_without_metadata)
    scheduled_time = None
    tema = text_without_metadata
    
    if date_match:
        date_str, time_str = date_match.groups()
        try:
            scheduled_time = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            # O tema é o que vem ANTES da data
            tema = text_without_metadata.split(date_str)[0].strip()
        except ValueError:
            pass

    return tema, scheduled_time, emails


async def handle_reuniao(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    sheets: ExcelOnlineIntegration,
    teams: TeamsAPIIntegration,
    auth: AuthMiddleware,
    op_logger: OperationLogger,
    tz: TimezoneMiddleware,
) -> None:
    if not update.effective_user or not update.effective_chat:
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Usuário"
    username = update.effective_user.username

    employee = sheets.get_employee(telegram_id)
    if not employee:
        message = "⚠️ Você não está cadastrado. Apenas funcionários registrados podem agendar reuniões."
        await context.bot.send_message(chat_id=chat_id, text=message)
        op_logger.log_warning(
            command="reuniao",
            telegram_id=telegram_id,
            user_name=user_name,
            warning="Unregistered user attempted to create meeting",
        )
        return

    display_name = employee.nome if employee else user_name
    mention = f"@{username}" if username else display_name

    args = context.args or []
    if not args:
        message = (
            "❌ *Por favor, informe o tema da reunião.*\n\n"
            "📌 *Uso:*\n"
            "`/reuniao [tema] [emails...]` — agora\n"
            "`/reuniao [tema] DD/MM/AAAA HH:MM [emails...]` — agendar\n\n"
            "📋 *Exemplos:*\n"
            "`/reuniao Alinhamento comercial@empresa.com`\n"
            "`/reuniao Daily 29/03/2026 10:00 dev@empresa.com`"
        )
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return

    tema, scheduled_time, emails = _parse_reuniao_args(args, sheets)

    if not tema:
        await context.bot.send_message(chat_id=chat_id, text="❌ Informe o tema da reunião.")
        return

    is_scheduled = scheduled_time is not None
    start_time = scheduled_time if is_scheduled else tz.get_brazil_timestamp()

    if is_scheduled and scheduled_time < tz.get_brazil_timestamp():
        await context.bot.send_message(chat_id=chat_id, text="❌ A data/hora informada já passou.")
        return

    try:
        # Cria evento no CALENDÁRIO (incluindo Teams e convidados)
        meeting = teams.create_calendar_event(
            subject=tema,
            start_time=start_time,
            duration=60,
            attendees=emails,
            content=f"Reunião agendada via Telegram por {display_name}."
        )

        join_url = meeting.get("join_url", "")
        web_link = meeting.get("web_link", "")

        # Resposta no Telegram
        data_fmt = start_time.strftime("%d/%m/%Y às %H:%M")
        attendees_text = f"\n📧 **Participantes convidados:** {', '.join(emails)}" if emails else ""
        
        status_text = "agendada" if is_scheduled else "iniciada"
        message = (
            f"🗓️ {mention}, a reunião **'{tema}'** foi {status_text} no **Calendário do Outlook**.\n\n"
            f"🕐 **Horário:** {data_fmt}\n"
            f"📌 **Link Teams:** [Ingressar na Reunião]({join_url})\n"
            f"🔗 **Ver no Outlook:** [Abrir Evento]({web_link})"
            f"{attendees_text}\n\n"
            f"_O convite foi enviado para os e-mails e adicionado à sua agenda._"
        )

        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown", disable_web_page_preview=True)

        op_logger.log_operation(
            command="reuniao",
            telegram_id=telegram_id,
            user_name=display_name,
            action="calendar_event_created",
            details={
                "topic": tema,
                "start": start_time.isoformat(),
                "emails": emails,
                "join_url": join_url
            },
        )

    except Exception as e:
        logger.error(f"Failed to create Calendar event: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Erro ao criar evento no Calendário: {str(e)}",
            parse_mode="Markdown"
        )

