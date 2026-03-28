"""
Testes unitários para middleware de autenticação.
"""

import pytest
import os

from middleware.auth import AuthMiddleware


class TestAuthMiddleware:
    """Testes para classe AuthMiddleware."""

    @pytest.fixture
    def auth(self):
        """Criar instância de AuthMiddleware para testes."""
        return AuthMiddleware(
            admin_ids=["111111111", "222222222"],
            ceo_id="999999999",
        )

    def test_is_admin(self, auth):
        """Testar verificação de admin."""
        assert auth.is_admin("111111111") is True
        assert auth.is_admin("222222222") is True
        assert auth.is_admin("333333333") is False

    def test_is_ceo(self, auth):
        """Testar verificação de CEO."""
        assert auth.is_ceo("999999999") is True
        assert auth.is_ceo("111111111") is False
        assert auth.is_ceo("333333333") is False

    def test_get_user_role(self, auth):
        """Testar obtenção de role do usuário."""
        assert auth.get_user_role("999999999") == "ceo"
        assert auth.get_user_role("111111111") == "admin"
        assert auth.get_user_role("333333333") == "funcionario"

    def test_check_permission(self, auth):
        """Testar verificação de permissão por nível."""
        # CEO pode tudo
        assert auth.check_permission("999999999", "funcionario") is True
        assert auth.check_permission("999999999", "admin") is True
        assert auth.check_permission("999999999", "ceo") is True

        # Admin pode acessar funcionario e admin
        assert auth.check_permission("111111111", "funcionario") is True
        assert auth.check_permission("111111111", "admin") is True
        assert auth.check_permission("111111111", "ceo") is False

        # Funcionario só pode acessar funcionario
        assert auth.check_permission("333333333", "funcionario") is True
        assert auth.check_permission("333333333", "admin") is False

    def test_can_use_command(self, auth):
        """Testar permissão por comando."""
        # Todos podem usar checkpoint e reuniao
        assert auth.can_use_command("333333333", "cheguei") is True
        assert auth.can_use_command("333333333", "fui") is True
        assert auth.can_use_command("333333333", "reuniao") is True

        # Só admin pode registrar
        assert auth.can_use_command("111111111", "registrar") is True
        assert auth.can_use_command("333333333", "registrar") is False

        # Só CEO pode usar decisao
        assert auth.can_use_command("999999999", "decisao") is True
        assert auth.can_use_command("111111111", "decisao") is False
        assert auth.can_use_command("333333333", "decisao") is False

    def test_get_permission_error_message(self, auth):
        """Testar mensagens de erro de permissão."""
        msg_decisao = auth.get_permission_error_message("333333333", "decisao")
        assert "CEO" in msg_decisao

        msg_registrar = auth.get_permission_error_message("333333333", "registrar")
        assert "permissão" in msg_registrar

    def test_from_env(self, monkeypatch):
        """Testar criação a partir de variáveis de ambiente."""
        monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "111,222,333")
        monkeypatch.setenv("CEO_TELEGRAM_ID", "999")

        auth = AuthMiddleware.from_env()

        assert auth.is_admin("111") is True
        assert auth.is_admin("222") is True
        assert auth.is_ceo("999") is True

    def test_from_env_missing_ceo(self, monkeypatch):
        """Testar erro quando CEO não está configurado."""
        monkeypatch.delenv("CEO_TELEGRAM_ID", raising=False)

        with pytest.raises(ValueError):
            AuthMiddleware.from_env()
