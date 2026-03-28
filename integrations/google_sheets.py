"""
Google Sheets Integration for Artificiall Ops Manager.

Handles all CRUD operations with Google Sheets API for:
- Funcionários (Employees)
- Ponto (Timesheet)
- Decisões (Decisions)
"""

import logging
from typing import Optional, List
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from models.employee import Employee
from models.timesheet import TimesheetEntry
from models.decision import Decision

logger = logging.getLogger(__name__)


class GoogleSheetsIntegration:
    """Integration with Google Sheets API for data persistence."""

    # Sheet names
    SHEET_FUNCIONARIOS = "Funcionários"
    SHEET_PONTO = "Ponto"
    SHEET_DECISOES = "Decisões"

    # Column indices (0-based)
    FUNCIONARIOS_COLS = {
        "telegram_id": 0,
        "nome": 1,
        "numero": 2,
        "data_cadastro": 3,
        "cargo": 4,
        "ativo": 5,
        "role": 6,
    }

    PONTO_COLS = {
        "id": 0,
        "telegram_id": 1,
        "nome": 2,
        "tipo": 3,
        "timestamp": 4,
        "data": 5,
        "timezone": 6,
    }

    DECISOES_COLS = {
        "id": 0,
        "data": 1,
        "decisao": 2,
        "registrado_por": 3,
        "ceo_telegram_id": 4,
        "categoria": 5,
    }

    def __init__(self, sheet_id: str, service_account_json: str):
        """
        Initialize Google Sheets integration.

        Args:
            sheet_id: Google Spreadsheet ID (from URL)
            service_account_json: Path to service account JSON file
        """
        self.sheet_id = sheet_id
        self.service_account_json = service_account_json
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None

    def _get_client(self) -> gspread.Client:
        """Get or create gspread client with Service Account credentials."""
        if self._client is None:
            try:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
                creds = Credentials.from_service_account_file(
                    self.service_account_json, scopes=scopes
                )
                self._client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets client: {e}")
                raise
        return self._client

    def _get_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        Get worksheet by name.

        Args:
            sheet_name: Name of the worksheet

        Returns:
            Worksheet object
        """
        client = self._get_client()
        spreadsheet = client.open_by_key(self.sheet_id)
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            return worksheet
        except gspread.WorksheetNotFound:
            logger.error(f"Worksheet '{sheet_name}' not found")
            raise

    def get_employee(self, telegram_id: str) -> Optional[Employee]:
        """
        Get employee by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Employee object or None if not found
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_FUNCIONARIOS)
            all_rows = worksheet.get_all_values()

            if len(all_rows) <= 1:  # Only header row
                return None

            # Skip header row, search for telegram_id
            for row in all_rows[1:]:
                if len(row) > self.FUNCIONARIOS_COLS["telegram_id"]:
                    if row[self.FUNCIONARIOS_COLS["telegram_id"]] == telegram_id:
                        # Check if active
                        ativo_str = row[self.FUNCIONARIOS_COLS["ativo"]].lower()
                        if ativo_str in ["true", "1", "sim"]:
                            return Employee.from_row(row)

            return None
        except Exception as e:
            logger.error(f"Error getting employee {telegram_id}: {e}")
            return None

    def create_employee(self, employee: Employee) -> bool:
        """
        Create new employee record.

        Args:
            employee: Employee object to create

        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_FUNCIONARIOS)
            row_data = employee.to_row()
            worksheet.append_row(row_data)
            logger.info(f"Employee created: {employee.nome} (ID: {employee.telegram_id})")
            return True
        except Exception as e:
            logger.error(f"Error creating employee: {e}")
            return False

    def update_employee_telegram_id(self, pending_id: str, telegram_id: str) -> bool:
        """
        Update employee telegram_id from "pending" to actual ID.

        Args:
            pending_id: The pending placeholder ID to find
            telegram_id: The actual Telegram ID to update to

        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_FUNCIONARIOS)
            all_rows = worksheet.get_all_values()

            if len(all_rows) <= 1:  # Only header row
                return False

            # Find row with pending_id
            for idx, row in enumerate(all_rows[1:], start=2):  # Start from 2 (1-indexed + header)
                if len(row) > self.FUNCIONARIOS_COLS["telegram_id"]:
                    if row[self.FUNCIONARIOS_COLS["telegram_id"]] == pending_id:
                        # Update telegram_id in column A
                        cell = worksheet.cell(idx, 1)  # Column A (telegram_id)
                        cell.value = telegram_id
                        worksheet.update_cell(cell.row, cell.col, telegram_id)
                        logger.info(f"Updated employee telegram_id from '{pending_id}' to '{telegram_id}'")
                        return True

            return False
        except Exception as e:
            logger.error(f"Error updating employee telegram_id: {e}")
            return False

    def get_employee_by_pending_id(self, pending_id: str) -> Optional[Employee]:
        """
        Get employee by pending ID (placeholder before actual telegram_id).

        Args:
            pending_id: The pending placeholder ID

        Returns:
            Employee object or None if not found
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_FUNCIONARIOS)
            all_rows = worksheet.get_all_values()

            if len(all_rows) <= 1:  # Only header row
                return None

            # Skip header row, search for pending_id
            for row in all_rows[1:]:
                if len(row) > self.FUNCIONARIOS_COLS["telegram_id"]:
                    if row[self.FUNCIONARIOS_COLS["telegram_id"]] == pending_id:
                        ativo_str = row[self.FUNCIONARIOS_COLS["ativo"]].lower()
                        if ativo_str in ["true", "1", "sim"]:
                            return Employee.from_row(row)

            return None
        except Exception as e:
            logger.error(f"Error getting employee by pending_id {pending_id}: {e}")
            return None

    def log_timesheet(self, entry: TimesheetEntry) -> bool:
        """
        Log timesheet entry (ponto).

        Args:
            entry: TimesheetEntry object to log

        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_PONTO)
            row_data = entry.to_row()
            worksheet.append_row(row_data)
            logger.info(
                f"Timesheet logged: {entry.nome} - {entry.tipo} at {entry.timestamp}"
            )
            return True
        except Exception as e:
            logger.error(f"Error logging timesheet: {e}")
            return False

    def create_decision(self, decision: Decision) -> bool:
        """
        Create executive decision record.

        Args:
            decision: Decision object to create

        Returns:
            True if successful, False otherwise
        """
        try:
            worksheet = self._get_worksheet(self.SHEET_DECISOES)
            row_data = decision.to_row()
            worksheet.append_row(row_data)
            logger.info(
                f"Decision created: {decision.id} by {decision.registrado_por}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating decision: {e}")
            return False

    def ensure_sheets_exist(self) -> bool:
        """
        Ensure all required sheets exist with proper headers.

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            spreadsheet = client.open_by_key(self.sheet_id)

            # Define required sheets and headers
            sheets_config = {
                self.SHEET_FUNCIONARIOS: [
                    "telegram_id",
                    "nome",
                    "numero",
                    "data_cadastro",
                    "cargo",
                    "ativo",
                    "role",
                ],
                self.SHEET_PONTO: [
                    "id",
                    "telegram_id",
                    "nome",
                    "tipo",
                    "timestamp",
                    "data",
                    "timezone",
                ],
                self.SHEET_DECISOES: [
                    "id",
                    "data",
                    "decisao",
                    "registrado_por",
                    "ceo_telegram_id",
                    "categoria",
                ],
            }

            for sheet_name, headers in sheets_config.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    logger.info(f"Sheet '{sheet_name}' already exists")
                except gspread.WorksheetNotFound:
                    # Create new worksheet
                    worksheet = spreadsheet.add_worksheet(
                        title=sheet_name, rows=100, cols=len(headers)
                    )
                    # Add header row
                    worksheet.update("A1:G1", [headers])
                    logger.info(f"Sheet '{sheet_name}' created with headers")

            return True
        except Exception as e:
            logger.error(f"Error ensuring sheets exist: {e}")
            return False
