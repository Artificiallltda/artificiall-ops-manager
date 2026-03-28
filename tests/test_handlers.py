"""
Testes unitários para handlers de comandos.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.checkpoint import handle_cheguei, handle_fui
from handlers.register import parse_register_command
from middleware.auth import AuthMiddleware
from middleware.timezone import TimezoneMiddleware


class TestCheckpointHandler:
    """Testes para handlers de ponto eletrônico."""

    @pytest.fixture
    def mock_dependencies(self):
        """Criar dependências mockadas."""
        sheets = MagicMock()
        auth = MagicMock()
        op_logger = MagicMock()
        tz = TimezoneMiddleware()

        return {
            "sheets": sheets,
            "auth": auth,
            "op_logger": op_logger,
            "tz": tz,
        }

    @pytest.mark.asyncio
    async def test_cheguei_user_not_registered(self, mock_dependencies):
        """Testar /cheguei quando usuário não está cadastrado."""
        # Setup
        mock_dependencies["sheets"].get_employee.return_value = None

        update = MagicMock()
        update.effective_user.id = 123456789
        update.effective_user.first_name = "Test User"
        update.effective_chat.id = 987654321

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        # Execute
        await handle_cheguei(
            update,
            context,
            mock_dependencies["sheets"],
            mock_dependencies["auth"],
            mock_dependencies["op_logger"],
            mock_dependencies["tz"],
        )

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args[1]
        assert "não está cadastrado" in call_args["text"]

    @pytest.mark.asyncio
    async def test_cheguei_user_registered(self, mock_dependencies):
        """Testar /cheguei quando usuário está cadastrado."""
        # Setup
        employee = MagicMock()
        employee.nome = "Daniele Silva"
        mock_dependencies["sheets"].get_employee.return_value = employee
        mock_dependencies["sheets"].log_timesheet.return_value = True

        update = MagicMock()
        update.effective_user.id = 123456789
        update.effective_user.first_name = "Test"
        update.effective_chat.id = 987654321

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        # Execute
        await handle_cheguei(
            update,
            context,
            mock_dependencies["sheets"],
            mock_dependencies["auth"],
            mock_dependencies["op_logger"],
            mock_dependencies["tz"],
        )

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args[1]
        assert "Ponto de entrada registrado" in call_args["text"]
        mock_dependencies["sheets"].log_timesheet.assert_called_once()

    @pytest.mark.asyncio
    async def test_fui_user_registered(self, mock_dependencies):
        """Testar /fui quando usuário está cadastrado."""
        # Setup
        employee = MagicMock()
        employee.nome = "Daniele Silva"
        mock_dependencies["sheets"].get_employee.return_value = employee
        mock_dependencies["sheets"].log_timesheet.return_value = True

        update = MagicMock()
        update.effective_user.id = 123456789
        update.effective_chat.id = 987654321

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        # Execute
        await handle_fui(
            update,
            context,
            mock_dependencies["sheets"],
            mock_dependencies["auth"],
            mock_dependencies["op_logger"],
            mock_dependencies["tz"],
        )

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args[1]
        assert "Ponto de saída registrado" in call_args["text"]


class TestRegisterCommand:
    """Testes para parser do comando /registrar."""

    def test_parse_register_valid(self):
        """Testar parse de comando válido."""
        args = ["@daniele", "Daniele", "Silva", "+5511999998888", "Analista"]

        result = parse_register_command(args)

        assert result is not None
        assert result["username"] == "daniele"
        assert result["nome"] == "Daniele Silva"
        assert result["numero"] == "+5511999998888"
        assert result["cargo"] == "Analista"

    def test_parse_register_no_username(self):
        """Testar parse sem username."""
        args = ["Daniele", "Silva", "+5511999998888", "Analista"]

        result = parse_register_command(args)

        assert result is not None
        assert result["username"] is None
        assert result["nome"] == "Daniele Silva"

    def test_parse_register_invalid_phone(self):
        """Testar parse com telefone inválido."""
        args = ["@user", "Nome", "123", "Cargo"]

        result = parse_register_command(args)

        assert result is None

    def test_parse_register_too_few_args(self):
        """Testar parse com poucos argumentos."""
        args = ["@user", "Nome"]

        result = parse_register_command(args)

        assert result is None


class TestDecisionHandler:
    """Testes para handler de decisões."""

    @pytest.fixture
    def mock_dependencies(self):
        """Criar dependências mockadas."""
        sheets = MagicMock()
        auth = MagicMock()
        auth.is_ceo.return_value = True
        op_logger = MagicMock()
        tz = TimezoneMiddleware()

        return {
            "sheets": sheets,
            "auth": auth,
            "op_logger": op_logger,
            "tz": tz,
        }

    @pytest.mark.asyncio
    async def test_decisao_not_ceo(self, mock_dependencies):
        """Testar /decisao quando usuário não é CEO."""
        mock_dependencies["auth"].is_ceo.return_value = False

        update = MagicMock()
        update.effective_user.id = 123456789
        update.effective_chat.id = 987654321

        context = MagicMock()
        context.args = ["Decisão teste"]
        context.bot.send_message = AsyncMock()

        # Import handler
        from handlers.decision import handle_decisao

        # Execute
        await handle_decisao(
            update,
            context,
            mock_dependencies["sheets"],
            mock_dependencies["auth"],
            mock_dependencies["op_logger"],
            mock_dependencies["tz"],
        )

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args[1]
        assert "Apenas o CEO" in call_args["text"]

    @pytest.mark.asyncio
    async def test_decisao_ceo_success(self, mock_dependencies):
        """Testar /decisao quando CEO registra decisão."""
        mock_dependencies["sheets"].create_decision.return_value = True

        update = MagicMock()
        update.effective_user.id = 999999999
        update.effective_chat.id = 987654321

        context = MagicMock()
        context.args = ["Aprovo a contratação de João"]
        context.bot.send_message = AsyncMock()

        from handlers.decision import handle_decisao

        # Execute
        await handle_decisao(
            update,
            context,
            mock_dependencies["sheets"],
            mock_dependencies["auth"],
            mock_dependencies["op_logger"],
            mock_dependencies["tz"],
        )

        # Assert
        context.bot.send_message.assert_called_once()
        call_args = context.bot.send_message.call_args[1]
        assert "Decisão registrada com sucesso" in call_args["text"]
        mock_dependencies["sheets"].create_decision.assert_called_once()
