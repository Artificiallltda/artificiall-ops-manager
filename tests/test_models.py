"""
Testes unitários para modelos de dados.
"""

import pytest
import uuid
from datetime import datetime

from models.employee import Employee
from models.timesheet import TimesheetEntry
from models.decision import Decision


class TestEmployee:
    """Testes para classe Employee."""

    def test_create_employee_valid(self):
        """Testar criação de funcionário válido."""
        employee = Employee(
            telegram_id="123456789",
            nome="Daniele Silva",
            numero="+5511999998888",
            data_cadastro=datetime.now(),
            cargo="Analista de Marketing",
            ativo=True,
            role="funcionario",
        )

        assert employee.telegram_id == "123456789"
        assert employee.nome == "Daniele Silva"
        assert employee.cargo == "Analista de Marketing"
        assert employee.ativo is True
        assert employee.role == "funcionario"

    def test_employee_to_row(self):
        """Testar conversão para linha Google Sheets."""
        employee = Employee(
            telegram_id="123456789",
            nome="Daniele Silva",
            numero="+5511999998888",
            data_cadastro=datetime(2026, 3, 27, 10, 30, 0),
            cargo="Analista de Marketing",
            ativo=True,
            role="funcionario",
        )

        row = employee.to_row()

        assert len(row) == 7
        assert row[0] == "123456789"  # telegram_id
        assert row[1] == "Daniele Silva"  # nome
        assert row[4] == "Analista de Marketing"  # cargo
        assert row[5] == "TRUE"  # ativo

    def test_employee_from_row(self):
        """Testar criação a partir de linha Google Sheets."""
        row = [
            "123456789",
            "Daniele Silva",
            "+5511999998888",
            "27/03/2026 10:30:00",
            "Analista de Marketing",
            "TRUE",
            "funcionario",
        ]

        employee = Employee.from_row(row)

        assert employee.telegram_id == "123456789"
        assert employee.nome == "Daniele Silva"
        assert employee.cargo == "Analista de Marketing"
        assert employee.ativo is True

    def test_employee_str(self):
        """Testar representação string."""
        employee = Employee(
            telegram_id="123456789",
            nome="Daniele Silva",
            numero="+5511999998888",
            data_cadastro=datetime.now(),
            cargo="Analista de Marketing",
            ativo=True,
            role="funcionario",
        )

        str_repr = str(employee)
        assert "Daniele Silva" in str_repr
        assert "Analista de Marketing" in str_repr

    def test_employee_invalid_role(self):
        """Testar validação de role inválido."""
        with pytest.raises(ValueError):
            Employee(
                telegram_id="123456789",
                nome="Teste",
                numero="+5511999998888",
                data_cadastro=datetime.now(),
                cargo="Cargo",
                ativo=True,
                role="invalid_role",
            )


class TestTimesheetEntry:
    """Testes para classe TimesheetEntry."""

    def test_create_entry_valid(self):
        """Testar criação de registro de ponto válido."""
        entry = TimesheetEntry(
            telegram_id="123456789",
            nome="Daniele Silva",
            tipo="Entrada",
            timestamp=datetime.now(),
        )

        assert entry.telegram_id == "123456789"
        assert entry.nome == "Daniele Silva"
        assert entry.tipo == "Entrada"
        assert entry.timezone == "America/Sao_Paulo"

    def test_timesheet_invalid_tipo(self):
        """Testar validação de tipo inválido."""
        with pytest.raises(ValueError):
            TimesheetEntry(
                telegram_id="123456789",
                nome="Daniele Silva",
                tipo="Almoço",  # Inválido
                timestamp=datetime.now(),
            )

    def test_timesheet_generate_id(self):
        """Testar geração de ID UUID."""
        id1 = TimesheetEntry.generate_id()
        id2 = TimesheetEntry.generate_id()

        # Verify UUID format
        uuid.UUID(id1)  # Should not raise
        uuid.UUID(id2)  # Should not raise

        # Verify uniqueness
        assert id1 != id2

    def test_timesheet_to_row(self):
        """Testar conversão para linha Google Sheets."""
        entry = TimesheetEntry(
            telegram_id="123456789",
            nome="Daniele Silva",
            tipo="Entrada",
            timestamp=datetime(2026, 3, 27, 8, 0, 0),
        )

        row = entry.to_row()

        assert len(row) == 7
        assert row[1] == "123456789"  # telegram_id
        assert row[2] == "Daniele Silva"  # nome
        assert row[3] == "Entrada"  # tipo


class TestDecision:
    """Testes para classe Decision."""

    def test_create_decision_valid(self):
        """Testar criação de decisão válida."""
        decision = Decision(
            decisao="Aprovo a contratação de João Silva",
            registrado_por="Gean Santos",
            ceo_telegram_id="123456789",
            categoria="RH",
            data=datetime.now(),
        )

        assert decision.decisao == "Aprovo a contratação de João Silva"
        assert decision.registrado_por == "Gean Santos"
        assert decision.categoria == "RH"

    def test_decision_short_text(self):
        """Testar validação de texto curto."""
        with pytest.raises(ValueError):
            Decision(
                decisao="Curto",  # Menos de 10 caracteres
                registrado_por="Gean Santos",
                ceo_telegram_id="123456789",
                data=datetime.now(),
            )

    def test_decision_generate_id(self):
        """Testar geração de ID UUID."""
        id1 = Decision.generate_id()
        id2 = Decision.generate_id()

        uuid.UUID(id1)
        uuid.UUID(id2)
        assert id1 != id2

    def test_decision_optional_categoria(self):
        """Testar categoria opcional."""
        decision = Decision(
            decisao="Decisão sem categoria específica",
            registrado_por="Gean Santos",
            ceo_telegram_id="123456789",
            data=datetime.now(),
        )

        assert decision.categoria is None

    def test_decision_to_row(self):
        """Testar conversão para linha Google Sheets."""
        decision = Decision(
            decisao="Aprovo o orçamento de marketing",
            registrado_por="Gean Santos",
            ceo_telegram_id="123456789",
            categoria="Financeiro",
            data=datetime(2026, 3, 27, 14, 30, 0),
        )

        row = decision.to_row()

        assert len(row) == 6
        assert row[2] == "Aprovo o orçamento de marketing"
        assert row[3] == "Gean Santos"
        assert row[4] == "123456789"
