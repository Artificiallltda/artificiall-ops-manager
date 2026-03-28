"""
Artificiall Ops Manager - Main Bot Application.

Telegram bot for operational management of Artificiall LTDA.
Integrates with Google Sheets and Microsoft Teams.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import Settings
from integrations.excel_api import ExcelOnlineIntegration
from integrations.teams_api import TeamsAPIIntegration
from integrations.telegram_bot import TelegramBotIntegration
from middleware.auth import AuthMiddleware
from middleware.logger import OperationLogger
from middleware.timezone import TimezoneMiddleware
from handlers import (
    handle_cheguei,
    handle_fui,
    handle_registrar,
    handle_register_me,
    handle_reuniao,
    handle_decisao,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, Settings.AIOX_LOG_LEVEL),
)
logger = logging.getLogger(__name__)


class ArtificiallOpsBot:
    """Main bot application class."""

    def __init__(self):
        """Initialize the bot with all integrations and middleware."""
        # Validate settings
        if not Settings.validate():
            raise ValueError("Invalid configuration. Check .env file.")

        # Initialize integrations
        self.sheets = ExcelOnlineIntegration(
            tenant_id=Settings.MICROSOFT_TENANT_ID,
            client_id=Settings.MICROSOFT_CLIENT_ID,
            client_secret=Settings.MICROSOFT_CLIENT_SECRET,
            drive_item_id=Settings.EXCEL_DRIVE_ITEM_ID,
            user_id=Settings.MICROSOFT_ORGANIZER_ID,
        )

        self.teams = TeamsAPIIntegration(
            tenant_id=Settings.MICROSOFT_TENANT_ID,
            client_id=Settings.MICROSOFT_CLIENT_ID,
            client_secret=Settings.MICROSOFT_CLIENT_SECRET,
            organizer_user_id=Settings.MICROSOFT_ORGANIZER_ID,
        )

        self.telegram = TelegramBotIntegration(
            bot_token=Settings.TELEGRAM_BOT_TOKEN,
        )

        # Initialize middleware
        self.auth = AuthMiddleware(
            admin_ids=Settings.get_admin_ids(),
            ceo_id=Settings.CEO_TELEGRAM_ID,
        )

        self.op_logger = OperationLogger.from_env()
        self.tz = TimezoneMiddleware.from_env()

        # Create Telegram application
        self.application = Application.builder().token(Settings.TELEGRAM_BOT_TOKEN).build()

        # Register command handlers
        self._register_handlers()

        logger.info("Artificiall Ops Bot initialized successfully")

    def _register_handlers(self) -> None:
        """Register all command handlers with the application."""
        # Ponto eletrônico
        self.application.add_handler(
            CommandHandler("cheguei", self._cheguei_handler)
        )
        self.application.add_handler(
            CommandHandler("fui", self._fui_handler)
        )

        # Registro de funcionários
        self.application.add_handler(
            CommandHandler("registrar", self._registrar_handler)
        )
        self.application.add_handler(
            CommandHandler("register_me", self._register_me_handler)
        )

        # Reuniões Teams
        self.application.add_handler(
            CommandHandler("reuniao", self._reuniao_handler)
        )

        # Decisões executivas
        self.application.add_handler(
            CommandHandler("decisao", self._decisao_handler)
        )

        # Help command
        self.application.add_handler(
            CommandHandler("help", self._help_handler)
        )

        # Start command
        self.application.add_handler(
            CommandHandler("start", self._start_handler)
        )

        logger.info("Command handlers registered")

    async def _cheguei_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /cheguei command."""
        await handle_cheguei(
            update,
            context,
            self.sheets,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _fui_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /fui command."""
        await handle_fui(
            update,
            context,
            self.sheets,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _registrar_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /registrar command."""
        await handle_registrar(
            update,
            context,
            self.sheets,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _register_me_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /register_me command."""
        await handle_register_me(
            update,
            context,
            self.sheets,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _reuniao_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /reuniao command."""
        await handle_reuniao(
            update,
            context,
            self.sheets,
            self.teams,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _decisao_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /decisao command."""
        await handle_decisao(
            update,
            context,
            self.sheets,
            self.auth,
            self.op_logger,
            self.tz,
        )

    async def _help_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /help command - Show available commands."""
        if not update.effective_chat:
            return

        message = (
            "🤖 *Artificiall Ops Manager - Comandos Disponíveis*\n\n"
            "📍 *Ponto Eletrônico:*\n"
            "`/cheguei` - Registrar entrada\n"
            "`/fui` - Registrar saída\n\n"
            "👥 *Funcionários:*\n"
            "`/registrar @user Nome +5511999998888 Cargo` - Cadastrar funcionário (Admin)\n\n"
            "🎥 *Reuniões:*\n"
            "`/reuniao [tema]` - Criar reunião no Teams agora\n"
            "`/reuniao [tema] DD/MM/AAAA HH:MM` - Agendar reunião\n\n"
            "📋 *Decisões:*\n"
            "`/decisao [texto]` - Registrar decisão executiva (CEO apenas)\n\n"
            "ℹ️ *Ajuda:*\n"
            "`/help` - Mostrar esta mensagem\n\n"
            "_Artificiall LTDA - Gestão Operacional_"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="Markdown",
        )

    async def _start_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /start command - Welcome message."""
        if not update.effective_chat:
            return

        message = (
            "👋 Olá! Eu sou o *Artificiall Ops Manager*.\n\n"
            "Sou o bot de gestão operacional da Artificiall LTDA.\n\n"
            "Use `/help` para ver todos os comandos disponíveis.\n\n"
            "_Estou aqui para facilitar o registro de ponto, criação de reuniões e documentação de decisões._"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="Markdown",
        )

    async def setup_webhook(self) -> None:
        """Setup Telegram webhook."""
        if Settings.TELEGRAM_WEBHOOK_URL:
            await self.application.bot.set_webhook(Settings.TELEGRAM_WEBHOOK_URL)
            logger.info(f"Webhook set to: {Settings.TELEGRAM_WEBHOOK_URL}")
        else:
            logger.warning("TELEGRAM_WEBHOOK_URL not set. Webhook not configured.")

    async def delete_webhook(self) -> None:
        """Delete Telegram webhook (for development)."""
        await self.application.bot.delete_webhook()
        logger.info("Webhook deleted")

    def run_polling(self) -> None:
        """Run bot with polling (for development)."""
        logger.info("Starting bot in polling mode...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def run_webhook(self) -> None:
        """Run bot with webhook (for production)."""
        logger.info("Starting bot in webhook mode...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_webhook(
            listen="0.0.0.0",
            port=8443,
            url_path=Settings.TELEGRAM_BOT_TOKEN,
            webhook_url=Settings.TELEGRAM_WEBHOOK_URL,
        )


def main():
    """Main entry point."""
    try:
        bot = ArtificiallOpsBot()

        # Ensure Google Sheets are set up
        bot.sheets.ensure_sheets_exist()

        # Run in polling mode by default (use webhook for production)
        bot.run_polling()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
