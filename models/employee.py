"""
Modelo de dados para Funcionário.

Este módulo define a classe Employee para representar um funcionário
no sistema Artificiall Ops Manager, com integração ao Google Sheets.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional


class Employee:
    """
    Representa um funcionário cadastrado no sistema.

    Atributos:
        telegram_id: ID único do usuário no Telegram (chave primária).
        nome: Nome completo do funcionário.
        numero: Número de telefone no formato internacional.
        data_cadastro: Data e hora do cadastro no sistema.
        cargo: Cargo/função do funcionário na empresa.
        ativo: Indica se o funcionário está ativo no sistema.
        role: Nível de permissão (funcionario, admin, ceo).
    """

    def __init__(
        self,
        telegram_id: str,
        nome: str,
        numero: str,
        data_cadastro: datetime,
        cargo: str,
        ativo: bool = True,
        role: str = "funcionario"
    ) -> None:
        """
        Inicializa uma instância de Employee.

        Args:
            telegram_id: ID único do usuário no Telegram.
            nome: Nome completo do funcionário.
            numero: Número de telefone no formato internacional.
            data_cadastro: Data e hora do cadastro.
            cargo: Cargo/função do funcionário.
            ativo: Status de atividade (padrão: True).
            role: Nível de permissão (padrão: "funcionario").

        Raises:
            ValueError: Se algum campo obrigatório estiver vazio ou inválido.
        """
        if not telegram_id or not isinstance(telegram_id, str):
            raise ValueError("telegram_id deve ser uma string não vazia")
        if not nome or not isinstance(nome, str):
            raise ValueError("nome deve ser uma string não vazia")
        if not numero or not isinstance(numero, str):
            raise ValueError("numero deve ser uma string não vazia")
        if not isinstance(data_cadastro, datetime):
            raise ValueError("data_cadastro deve ser um objeto datetime")
        if not cargo or not isinstance(cargo, str):
            raise ValueError("cargo deve ser uma string não vazia")
        if not isinstance(ativo, bool):
            raise ValueError("ativo deve ser um booleano")
        if role not in ("funcionario", "admin", "ceo"):
            raise ValueError("role deve ser 'funcionario', 'admin' ou 'ceo'")

        self.telegram_id = telegram_id
        self.nome = nome
        self.numero = numero
        self.data_cadastro = data_cadastro
        self.cargo = cargo
        self.ativo = ativo
        self.role = role

    @classmethod
    def from_row(cls, row: list[Any]) -> Employee:
        """
        Cria uma instância de Employee a partir de uma linha do Google Sheets.

        Espera-se que a linha tenha a seguinte estrutura:
        [telegram_id, nome, numero, data_cadastro, cargo, ativo, role]

        Args:
            row: Lista com os valores da linha do Google Sheets.

        Returns:
            Instância de Employee populada com os dados da linha.

        Raises:
            ValueError: Se a linha tiver menos de 7 colunas ou dados inválidos.
        """
        if len(row) < 7:
            raise ValueError(
                f"Linha inválida: esperadas 7 colunas, recebidas {len(row)}"
            )

        telegram_id = str(row[0]).strip()
        nome = str(row[1]).strip()
        numero = str(row[2]).strip()

        # Parse da data_cadastro (formato Google Sheets: datetime ou string)
        data_cadastro_raw = row[3]
        if isinstance(data_cadastro_raw, datetime):
            data_cadastro = data_cadastro_raw
        elif isinstance(data_cadastro_raw, str):
            # Tenta parsear formatos comuns
            for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
                try:
                    data_cadastro = datetime.strptime(data_cadastro_raw, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Data inválida: {data_cadastro_raw}")
        else:
            raise ValueError(f"Data em formato desconhecido: {type(data_cadastro_raw)}")

        cargo = str(row[4]).strip()
        ativo = cls._parse_boolean(row[5])
        role = str(row[6]).strip().lower()

        return cls(
            telegram_id=telegram_id,
            nome=nome,
            numero=numero,
            data_cadastro=data_cadastro,
            cargo=cargo,
            ativo=ativo,
            role=role
        )

    @staticmethod
    def _parse_boolean(value: Any) -> bool:
        """
        Converte um valor do Google Sheets em booleano Python.

        Args:
            value: Valor a ser convertido (pode ser bool, str, int).

        Returns:
            Valor booleano convertido.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().upper() in ("TRUE", "1", "SIM", "S")
        if isinstance(value, (int, float)):
            return value != 0
        return False

    def to_row(self) -> list[Any]:
        """
        Converte a instância em uma lista para escrita no Google Sheets.

        Returns:
            Lista com os valores na ordem esperada pelo Google Sheets:
            [telegram_id, nome, numero, data_cadastro, cargo, ativo, role]
        """
        return [
            self.telegram_id,
            self.nome,
            self.numero,
            self.data_cadastro.strftime("%d/%m/%Y %H:%M:%S"),
            self.cargo,
            "TRUE" if self.ativo else "FALSE",  # Google Sheets expects string boolean
            self.role
        ]

    def __str__(self) -> str:
        """
        Retorna uma representação legível do funcionário.

        Returns:
            String formatada com nome, cargo e status do funcionário.
        """
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.nome} ({self.cargo}) - {status} [{self.role}]"

    def __repr__(self) -> str:
        """
        Retorna uma representação oficial da instância.

        Returns:
            String que pode ser usada para recriar o objeto (debug).
        """
        return (
            f"Employee(telegram_id='{self.telegram_id}', "
            f"nome='{self.nome}', role='{self.role}')"
        )
