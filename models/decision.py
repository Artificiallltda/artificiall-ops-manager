"""
Modelo de dados para Decisão Executiva.

Este módulo define a classe Decision para representar uma decisão
registrada pelo CEO no sistema Artificiall Ops Manager.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional


class Decision:
    """
    Representa uma decisão executiva registrada pelo CEO.

    Atributos:
        id: UUID único da decisão (chave primária).
        data: Data e hora do registro da decisão.
        decisao: Texto completo descrevendo a decisão tomada.
        registrado_por: Nome de quem registrou (normalmente o CEO).
        ceo_telegram_id: ID do CEO no Telegram.
        categoria: Categoria opcional da decisão (ex: "RH", "Financeiro").
    """

    def __init__(
        self,
        data: datetime,
        decisao: str,
        registrado_por: str,
        ceo_telegram_id: str,
        categoria: Optional[str] = None,
        id: Optional[str] = None
    ) -> None:
        """
        Inicializa uma instância de Decision.

        Args:
            data: Data e hora do registro.
            decisao: Texto da decisão (mínimo 10 caracteres).
            registrado_por: Nome de quem registrou.
            ceo_telegram_id: ID do CEO no Telegram.
            categoria: Categoria opcional da decisão.
            id: UUID da decisão (gerado automaticamente se None).

        Raises:
            ValueError: Se algum campo obrigatório estiver inválido.
        """
        if not isinstance(data, datetime):
            raise ValueError("data deve ser um objeto datetime")
        if not decisao or not isinstance(decisao, str):
            raise ValueError("decisao deve ser uma string não vazia")
        if len(decisao) < 10:
            raise ValueError("decisao deve ter pelo menos 10 caracteres")
        if not registrado_por or not isinstance(registrado_por, str):
            raise ValueError("registrado_por deve ser uma string não vazia")
        if not ceo_telegram_id or not isinstance(ceo_telegram_id, str):
            raise ValueError("ceo_telegram_id deve ser uma string não vazia")
        if categoria is not None and not isinstance(categoria, str):
            raise ValueError("categoria deve ser uma string ou None")

        self._id = id if id else self.generate_id()
        self.data = data
        self.decisao = decisao
        self.registrado_por = registrado_por
        self.ceo_telegram_id = ceo_telegram_id
        self.categoria = categoria

    @property
    def id(self) -> str:
        """Retorna o UUID da decisão."""
        return self._id

    @staticmethod
    def generate_id() -> str:
        """
        Gera um UUID único para a decisão.

        Returns:
            String UUID no formato padrão (ex: "abc123-def456-...").
        """
        return str(uuid.uuid4())

    @classmethod
    def from_row(cls, row: list[Any]) -> Decision:
        """
        Cria uma instância de Decision a partir de uma linha do Google Sheets.

        Espera-se que a linha tenha a seguinte estrutura:
        [id, data, decisao, registrado_por, ceo_telegram_id, categoria]

        Args:
            row: Lista com os valores da linha do Google Sheets.

        Returns:
            Instância de Decision populada com os dados da linha.

        Raises:
            ValueError: Se a linha tiver menos de 5 colunas ou dados inválidos.
        """
        if len(row) < 5:
            raise ValueError(
                f"Linha inválida: esperadas pelo menos 5 colunas, recebidas {len(row)}"
            )

        id = str(row[0]).strip()

        # Parse da data
        data_raw = row[1]
        if isinstance(data_raw, datetime):
            data = data_raw
        elif isinstance(data_raw, str):
            for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
                try:
                    data = datetime.strptime(data_raw, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Data inválida: {data_raw}")
        else:
            raise ValueError(f"Data em formato desconhecido: {type(data_raw)}")

        decisao = str(row[2]).strip()
        registrado_por = str(row[3]).strip()
        ceo_telegram_id = str(row[4]).strip()

        # Categoria é opcional (coluna F)
        categoria = None
        if len(row) >= 6 and row[5]:
            categoria = str(row[5]).strip()
            if not categoria:
                categoria = None

        return cls(
            id=id,
            data=data,
            decisao=decisao,
            registrado_por=registrado_por,
            ceo_telegram_id=ceo_telegram_id,
            categoria=categoria
        )

    def to_row(self) -> list[Any]:
        """
        Converte a instância em uma lista para escrita no Google Sheets.

        Returns:
            Lista com os valores na ordem esperada pelo Google Sheets:
            [id, data, decisao, registrado_por, ceo_telegram_id, categoria]
        """
        return [
            self.id,
            self.data.strftime("%d/%m/%Y %H:%M:%S"),
            self.decisao,
            self.registrado_por,
            self.ceo_telegram_id,
            self.categoria if self.categoria else ""
        ]

    def __str__(self) -> str:
        """
        Retorna uma representação legível da decisão.

        Returns:
            String formatada com data, categoria e resumo da decisão.
        """
        categoria_str = f" [{self.categoria}]" if self.categoria else ""
        resumo = (
            self.decisao[:50] + "..."
            if len(self.decisao) > 50
            else self.decisao
        )
        return (
            f"{self.data.strftime('%d/%m/%Y %H:%M')}{categoria_str} - "
            f"{self.registrado_por}: {resumo}"
        )

    def __repr__(self) -> str:
        """
        Retorna uma representação oficial da instância.

        Returns:
            String que pode ser usada para debug.
        """
        categoria_repr = f", categoria='{self.categoria}'" if self.categoria else ""
        return (
            f"Decision(id='{self.id}', data='{self.data}', "
            f"registrado_por='{self.registrado_por}'{categoria_repr})"
        )
