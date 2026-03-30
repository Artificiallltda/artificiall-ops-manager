"""
Configuration settings for Artificiall Ops Manager.

Loads environment variables and provides centralized configuration.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment variables."""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")

    # Microsoft Excel Online (OneDrive via Graph API)
    # ID do arquivo .xlsx no OneDrive (obtido via scripts/setup_excel.py)
    EXCEL_DRIVE_ITEM_ID: str = os.getenv("EXCEL_DRIVE_ITEM_ID", "")

    # Microsoft Teams (Azure AD / Graph API)
    MICROSOFT_TENANT_ID: str = os.getenv("MICROSOFT_TENANT_ID", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    MICROSOFT_ORGANIZER_ID: str = os.getenv("MICROSOFT_ORGANIZER_ID", "")

    # AIOX Core
    AIOX_AGENT_ID: str = os.getenv("AIOX_AGENT_ID", "artificiall_ops_manager")
    AIOX_LOG_LEVEL: str = os.getenv("AIOX_LOG_LEVEL", "INFO")

    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Sao_Paulo")

    # Admin IDs
    ADMIN_TELEGRAM_IDS: str = os.getenv("ADMIN_TELEGRAM_IDS", "")
    CEO_TELEGRAM_ID: str = os.getenv("CEO_TELEGRAM_ID", "")

    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    LOGS_DIR: Path = BASE_DIR / "logs"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required settings are present.

        Returns:
            True if all required settings are present, False otherwise
        """
        required_settings = [
            "TELEGRAM_BOT_TOKEN",
            "EXCEL_DRIVE_ITEM_ID",
            "MICROSOFT_TENANT_ID",
            "MICROSOFT_CLIENT_ID",
            "MICROSOFT_CLIENT_SECRET",
            "MICROSOFT_ORGANIZER_ID",
            "CEO_TELEGRAM_ID",
        ]

        missing = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing.append(setting)

        if missing:
            logger.error(f"Missing required settings: {', '.join(missing)}")
            return False

        logger.info("All required settings validated")
        return True

    @classmethod
    def get_admin_ids(cls) -> list:
        """
        Get list of admin Telegram IDs.

        Returns:
            List of admin IDs
        """
        if not cls.ADMIN_TELEGRAM_IDS:
            return []
        return [id.strip() for id in cls.ADMIN_TELEGRAM_IDS.split(",") if id.strip()]

    @classmethod
    def is_production(cls) -> bool:
        """
        Check if running in production mode.

        Returns:
            True if production, False if development
        """
        return os.getenv("ENVIRONMENT", "development") == "production"


# Export settings instance
settings = Settings()
