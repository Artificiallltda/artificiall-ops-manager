"""
Telegram Bot Integration for Artificiall Ops Manager.

Wrapper for Telegram Bot API operations including message formatting
and user information extraction.
"""

import logging
from typing import Dict, Optional

from telegram import Update, User
from telegram.ext import Application

logger = logging.getLogger(__name__)


class TelegramBotIntegration:
    """Integration with Telegram Bot API for messaging and user interaction."""

    def __init__(self, bot_token: str):
        """
        Initialize Telegram Bot integration.

        Args:
            bot_token: Telegram Bot Token from BotFather
        """
        self.bot_token = bot_token
        self._application: Optional[Application] = None

    def get_application(self) -> Application:
        """Get or create Telegram Bot application."""
        if self._application is None:
            self._application = Application.builder().token(self.bot_token).build()
            logger.info("Telegram Bot application initialized")
        return self._application

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_to_message_id: Optional[int] = None,
    ) -> bool:
        """
        Send message to Telegram chat.

        Args:
            chat_id: Telegram chat/user ID
            text: Message text (supports Markdown if parse_mode="Markdown")
            parse_mode: Parse mode ("Markdown", "HTML", or None)
            reply_to_message_id: Optional message ID to reply to

        Returns:
            True if successful, False otherwise
        """
        try:
            app = self.get_application()
            bot = app.bot

            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_to_message_id=reply_to_message_id,
            )
            logger.debug(f"Message sent to chat {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def format_mention(self, user_id: int, name: str) -> str:
        """
        Format user mention for Telegram.

        Args:
            user_id: Telegram user ID
            name: Display name for the mention

        Returns:
            Formatted mention string (e.g., "@Daniele")
        """
        # Telegram Markdown mention format
        return f"[{name}](tg://user?id={user_id})"

    def escape_markdown(self, text: str) -> str:
        """
        Escape special Markdown characters in text.

        Telegram Markdown special characters: _ * [ ] ( ) ~ ` > # + - = | { } . !

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for Markdown parsing
        """
        # Characters that need escaping in Telegram Markdown
        special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]

        for char in special_chars:
            text = text.replace(char, f"\\{char}")

        return text

    def get_user_info(self, update: Update) -> Dict:
        """
        Extract user information from Telegram update.

        Args:
            update: Telegram Update object

        Returns:
            Dictionary with user information:
            {
                "user_id": int,
                "username": str or None,
                "first_name": str,
                "last_name": str or None,
                "full_name": str,
                "is_bot": bool
            }
        """
        user: User = update.effective_user

        if not user:
            logger.warning("No user found in update")
            return {
                "user_id": 0,
                "username": None,
                "first_name": "Unknown",
                "last_name": None,
                "full_name": "Unknown",
                "is_bot": False,
            }

        full_name = user.first_name or ""
        if user.last_name:
            full_name += f" {user.last_name}"

        user_info = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": full_name.strip(),
            "is_bot": user.is_bot,
        }

        logger.debug(f"User info extracted: {user_info}")
        return user_info

    def format_command_response(
        self,
        success: bool,
        message: str,
        emoji: Optional[str] = None,
    ) -> str:
        """
        Format a command response message.

        Args:
            success: Whether the operation was successful
            message: Main message content
            emoji: Optional emoji to prepend

        Returns:
            Formatted message string
        """
        if emoji:
            prefix = emoji
        else:
            prefix = "✅" if success else "❌"

        return f"{prefix} {message}"

    async def send_error_message(
        self,
        chat_id: int,
        error_message: str,
        original_message: Optional[str] = None,
    ) -> None:
        """
        Send formatted error message.

        Args:
            chat_id: Telegram chat/user ID
            error_message: Error description
            original_message: Optional original command that caused the error
        """
        text = f"❌ *Erro:*\n{error_message}"

        if original_message:
            text += f"\n\n_Comando:_ `{original_message}`"

        await self.send_message(chat_id, text, parse_mode="Markdown")
