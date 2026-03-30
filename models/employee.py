"""
Modelo de dados para Funcionário.

Este módulo define a classe Employee para representar um funcionário
no sistema Artificiall Ops Manager, com integração ao Excel Online.
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
        email: E-mail corporativo/pessoal para convites.
        username: Handle do Telegram (sem o @).
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
        email: str = "",
        username: str = "",
        ativo: bool = True,
        role: str = "funcionario"
    ) -> None:
        """Inicializa uma instância de Employee."""
        if not telegram_id or not isinstance(telegram_id, str):
            raise ValueError("telegram_id deve ser uma string não vazia")
        if not nome or not isinstance(nome, str):
            raise ValueError("nome deve ser uma string não vazia")
        if not isinstance(data_cadastro, datetime):
            raise ValueError("data_cadastro deve ser um objeto datetime")
        if role not in ("funcionario", "admin", "ceo"):
            raise ValueError("role deve ser 'funcionario', 'admin' ou 'ceo'")

        self.telegram_id = telegram_id
        self.nome = nome
        self.numero = numero
        self.data_cadastro = data_cadastro
        self.cargo = cargo
        self.email = email
        self.username = username
        self.ativo = ativo
        self.role = role

    @classmethod
    def from_row(cls, row: list[Any]) -> Employee:
        """Cria uma instância de Employee a partir de uma linha do Excel."""
        if len(row) < 7:
            raise ValueError(f"Linha inválida: esperadas pelo menos 7 colunas, recebidas {len(row)}")

        telegram_id = str(row[0]).strip()
        nome = str(row[1]).strip()
        numero = str(row[2]).strip()

        data_cadastro_raw = row[3]
        if isinstance(data_cadastro_raw, datetime):
            data_cadastro = data_cadastro_raw
        else:
            try:
                # Formato padrão: DD/MM/YYYY HH:MM:S
                data_cadastro = datetime.strptime(str(data_cadastro_raw), "%d/%m/%Y %H:%M:%S")
            except:
                data_cadastro = datetime.now()

        cargo = str(row[4]).strip()
        ativo = cls._parse_boolean(row[5])
        role = str(row[6]).strip().lower()
        
        # Novos campos (email e username)
        email = str(row[7]).strip() if len(row) > 7 else ""
        username = str(row[8]).strip() if len(row) > 8 else ""

        return cls(
            telegram_id=telegram_id,
            nome=nome,
            numero=numero,
            data_cadastro=data_cadastro,
            cargo=cargo,
            email=email,
            username=username,
            ativo=ativo,
            role=role
        )

    @staticmethod
    def _parse_boolean(value: Any) -> bool:
        """Converte valor do Excel para booleano."""
        if isinstance(value, bool):
            return value
        return str(value).strip().upper() in ("TRUE", "1", "SIM", "S")

    def to_row(self) -> list[Any]:
        """Converte instância em lista para escrita no Excel."""
        numero_str = f"'{self.numero}" if self.numero.startswith("+") else self.numero

        return [
            self.telegram_id,
            self.nome,
            numero_str,
            self.data_cadastro.strftime("%d/%m/%Y %H:%M:%S"),
            self.cargo,
            "TRUE" if self.ativo else "FALSE",
            self.role,
            self.email,
            self.username
        ]

    def __str__(self) -> str:
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.nome} (@{self.username}) - {self.cargo} [{status}]"

    def __repr__(self) -> str:
        return f"Employee(telegram_id='{self.telegram_id}', nome='{self.nome}', email='{self.email}')"
