"""
Middleware de Autenticação e Autorização (RBAC) para Artificiall Ops Manager.

Implementa controle de acesso baseado em cargos (role-based access control).
"""

import logging
import os
from typing import List, Optional

from telegram import Update

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Authentication and Authorization middleware.
    
    Handles user authentication via telegram_id and role-based permissions.
    """

    # Roles
    ROLE_CEO = "ceo"
    ROLE_ADMIN = "admin"
    ROLE_FUNCIONARIO = "funcionario"

    def __init__(
        self,
        admin_ids: List[str],
        ceo_id: str,
    ):
        """
        Initialize Auth middleware.

        Args:
            admin_ids: List of Telegram IDs with admin privileges
            ceo_id: Telegram ID of the CEO
        """
        self.admin_ids = set(admin_ids)
        self.ceo_id = ceo_id
        logger.info(f"Auth middleware initialized with {len(admin_ids)} admins")

    def get_user_role(self, telegram_id: str) -> str:
        """
        Get user role based on Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Role string: 'ceo', 'admin', or 'funcionario'
        """
        if telegram_id == self.ceo_id:
            return self.ROLE_CEO
        elif telegram_id in self.admin_ids:
            return self.ROLE_ADMIN
        else:
            return self.ROLE_FUNCIONARIO

    def is_admin(self, telegram_id: str) -> bool:
        """
        Check if user has admin privileges.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if user is admin or CEO, False otherwise
        """
        return telegram_id in self.admin_ids or telegram_id == self.ceo_id

    def is_ceo(self, telegram_id: str) -> bool:
        """
        Check if user is the CEO.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if user is CEO, False otherwise
        """
        return telegram_id == self.ceo_id

    def check_permission(
        self,
        telegram_id: str,
        required_role: str,
    ) -> bool:
        """
        Check if user has required permission level.

        Permission hierarchy: ceo > admin > funcionario

        Args:
            telegram_id: Telegram user ID
            required_role: Minimum required role

        Returns:
            True if user has permission, False otherwise
        """
        user_role = self.get_user_role(telegram_id)

        # Role hierarchy (higher roles can access lower role features)
        role_hierarchy = {
            self.ROLE_FUNCIONARIO: 1,
            self.ROLE_ADMIN: 2,
            self.ROLE_CEO: 3,
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def can_use_command(self, telegram_id: str, command: str) -> bool:
        """
        Check if user can use a specific command.

        Command permissions:
        - /cheguei, /fui: All users
        - /registrar: Admin, CEO
        - /reuniao: All users
        - /decisao: CEO only

        Args:
            telegram_id: Telegram user ID
            command: Command name (without /)

        Returns:
            True if user can use command, False otherwise
        """
        # Commands available to all
        if command in ["cheguei", "fui", "reuniao"]:
            return True

        # Admin-only commands
        if command == "registrar":
            return self.is_admin(telegram_id)

        # CEO-only commands
        if command == "decisao":
            return self.is_ceo(telegram_id)

        # Unknown command - deny by default
        logger.warning(f"Unknown command permission check: {command}")
        return False

    def get_permission_error_message(self, telegram_id: str, command: str) -> str:
        """
        Get appropriate error message for permission denial.

        Args:
            telegram_id: Telegram user ID
            command: Command name (without /)

        Returns:
            Error message string
        """
        if command == "decisao":
            return "🔒 Apenas o CEO tem autorização para registrar decisões."
        elif command == "registrar":
            return "❌ Você não tem permissão para realizar registros."
        else:
            return "❌ Você não tem permissão para executar este comando."

    @classmethod
    def from_env(cls) -> "AuthMiddleware":
        """
        Create AuthMiddleware instance from environment variables.

        Expects:
            - ADMIN_TELEGRAM_IDS: Comma-separated list of admin IDs
            - CEO_TELEGRAM_ID: CEO's Telegram ID

        Returns:
            AuthMiddleware instance
        """
        admin_ids_str = os.getenv("ADMIN_TELEGRAM_IDS", "")
        admin_ids = [
            id.strip() for id in admin_ids_str.split(",") if id.strip()
        ]
        ceo_id = os.getenv("CEO_TELEGRAM_ID", "").strip()

        if not ceo_id:
            logger.error("CEO_TELEGRAM_ID not set in environment")
            raise ValueError("CEO_TELEGRAM_ID environment variable is required")

        logger.info(f"Auth middleware loaded from env: {len(admin_ids)} admins, CEO: {ceo_id}")
        return cls(admin_ids=admin_ids, ceo_id=ceo_id)
