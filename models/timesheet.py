"""
Modelo de dados para Registro de Ponto (Timesheet).

Este módulo define a classe TimesheetEntry para representar um registro
de entrada ou saída de funcionário no sistema Artificiall Ops Manager.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional


class TimesheetEntry:
    """
    Representa um registro de ponto (entrada ou saída) de um funcionário.

    Atributos:
        id: UUID único do registro (chave primária).
        telegram_id: ID do funcionário no Telegram.
        nome: Nome do funcionário (copia da base para rastreabilidade).
        tipo: Tipo de registro ("Entrada" ou "Saída").
        timestamp: Data e hora exata do registro.
        data: Data do registro (apenas dia, para agrupamento).
        timezone: Fuso horário utilizado (padrão: America/Sao_Paulo).
    """

    VALID_TYPES = ("Entrada", "Saída")

    def __init__(
        self,
        telegram_id: str,
        nome: str,
        tipo: str,
        timestamp: datetime,
        timezone: str = "America/Sao_Paulo",
        id: Optional[str] = None,
        data: Optional[datetime] = None
    ) -> None:
        """
        Inicializa uma instância de TimesheetEntry.

        Args:
            telegram_id: ID do funcionário no Telegram.
            nome: Nome do funcionário.
            tipo: Tipo de registro ("Entrada" ou "Saída").
            timestamp: Data e hora do registro.
            timezone: Fuso horário (padrão: America/Sao_Paulo).
            id: UUID do registro (gerado automaticamente se None).
            data: Data do registro (extraída do timestamp se None).

        Raises:
            ValueError: Se algum campo obrigatório estiver inválido.
        """
        if not telegram_id or not isinstance(telegram_id, str):
            raise ValueError("telegram_id deve ser uma string não vazia")
        if not nome or not isinstance(nome, str):
            raise ValueError("nome deve ser uma string não vazia")
        if tipo not in self.VALID_TYPES:
            raise ValueError(f"tipo deve ser 'Entrada' ou 'Saída', recebido: '{tipo}'")
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp deve ser um objeto datetime")
        if not timezone or not isinstance(timezone, str):
            raise ValueError("timezone deve ser uma string não vazia")

        self._id = id if id else self.generate_id()
        self.telegram_id = telegram_id
        self.nome = nome
        self._tipo = tipo
        self.timestamp = timestamp
        self.data = data if data else timestamp.date()
        self.timezone = timezone

    @property
    def id(self) -> str:
        """Retorna o UUID do registro."""
        return self._id

    @property
    def tipo(self) -> str:
        """
        Retorna o tipo de registro.

        Returns:
            "Entrada" ou "Saída".
        """
        return self._tipo

    @tipo.setter
    def tipo(self, value: str) -> None:
        """
        Define o tipo de registro com validação.

        Args:
            value: Novo tipo ("Entrada" ou "Saída").

        Raises:
            ValueError: Se o tipo não for válido.
        """
        if value not in self.VALID_TYPES:
            raise ValueError(f"tipo deve ser 'Entrada' ou 'Saída', recebido: '{value}'")
        self._tipo = value

    @staticmethod
    def generate_id() -> str:
        """
        Gera um UUID único para o registro.

        Returns:
            String UUID no formato padrão (ex: "abc123-def456-...").
        """
        return str(uuid.uuid4())

    @classmethod
    def from_row(cls, row: list[Any]) -> TimesheetEntry:
        """
        Cria uma instância de TimesheetEntry a partir de uma linha do Google Sheets.

        Espera-se que a linha tenha a seguinte estrutura:
        [id, telegram_id, nome, tipo, timestamp, data, timezone]

        Args:
            row: Lista com os valores da linha do Google Sheets.

        Returns:
            Instância de TimesheetEntry populada com os dados da linha.

        Raises:
            ValueError: Se a linha tiver menos de 7 colunas ou dados inválidos.
        """
        if len(row) < 7:
            raise ValueError(
                f"Linha inválida: esperadas 7 colunas, recebidas {len(row)}"
            )

        id = str(row[0]).strip()
        telegram_id = str(row[1]).strip()
        nome = str(row[2]).strip()
        tipo = str(row[3]).strip()

        # Parse do timestamp
        timestamp_raw = row[4]
        if isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw
        elif isinstance(timestamp_raw, str):
            for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    timestamp = datetime.strptime(timestamp_raw, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Timestamp inválido: {timestamp_raw}")
        else:
            raise ValueError(f"Timestamp em formato desconhecido: {type(timestamp_raw)}")

        # Parse da data
        data_raw = row[5]
        if isinstance(data_raw, datetime):
            data = data_raw.date()
        elif isinstance(data_raw, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    data = datetime.strptime(data_raw, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Data inválida: {data_raw}")
        else:
            raise ValueError(f"Data em formato desconhecido: {type(data_raw)}")

        timezone = str(row[6]).strip()

        return cls(
            id=id,
            telegram_id=telegram_id,
            nome=nome,
            tipo=tipo,
            timestamp=timestamp,
            data=data,
            timezone=timezone
        )

    def to_row(self) -> list[Any]:
        """
        Converte a instância em uma lista para escrita no Google Sheets.

        Returns:
            Lista com os valores na ordem esperada pelo Google Sheets:
            [id, telegram_id, nome, tipo, timestamp, data, timezone]
        """
        return [
            self.id,
            self.telegram_id,
            self.nome,
            self.tipo,
            self.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            self.data.strftime("%d/%m/%Y"),
            self.timezone
        ]

    def __str__(self) -> str:
        """
        Retorna uma representação legível do registro de ponto.

        Returns:
            String formatada com nome, tipo e horário do registro.
        """
        return (
            f"{self.nome} - {self.tipo} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
        )

    def __repr__(self) -> str:
        """
        Retorna uma representação oficial da instância.

        Returns:
            String que pode ser usada para debug.
        """
        return (
            f"TimesheetEntry(id='{self.id}', tipo='{self.tipo}', "
            f"telegram_id='{self.telegram_id}')"
        )
