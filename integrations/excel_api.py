"""
Microsoft Excel Online Integration for Artificiall Ops Manager.

Substitui o Google Sheets pelo Excel Online via Microsoft Graph API.
Usa o mesmo token Azure AD já configurado para o Teams.

Estrutura do arquivo Excel no OneDrive:
  - Aba: Funcionários (Employee registry)
  - Aba: Ponto       (Timesheet)
  - Aba: Decisões    (Executive decisions)
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List

import requests
from tenacity import retry, wait_exponential, stop_after_attempt

from models.employee import Employee
from models.timesheet import TimesheetEntry
from models.decision import Decision

logger = logging.getLogger(__name__)


class ExcelReadOnlyError(Exception):
    """Exception raised when the Excel drive is in Read-Only mode."""
    pass


class ExcelOnlineIntegration:
    """
    Integration with Microsoft Excel Online via Microsoft Graph API.

    Uses the same Azure AD credentials as TeamsAPIIntegration
    (Client Credentials flow — no user login required).
    """

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Sheet (worksheet) names
    SHEET_FUNCIONARIOS = "Funcionários"
    SHEET_PONTO = "Ponto"
    SHEET_DECISOES = "Decisões"

    # Table names inside each sheet
    TABLE_FUNCIONARIOS = "TblFuncionarios"
    TABLE_PONTO = "TblPonto"
    TABLE_DECISOES = "TblDecisoes"

    # Column indices (0-based) — must match the Excel table headers
    FUNCIONARIOS_COLS = {
        "telegram_id": 0,
        "nome": 1,
        "numero": 2,
        "data_cadastro": 3,
        "cargo": 4,
        "ativo": 5,
        "role": 6,
        "email": 7,
        "username": 8,
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

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        drive_item_id: str,
        user_id: str,
    ):
        """
        Initialize Microsoft Excel Online integration.

        Args:
            tenant_id: Azure AD Directory (Tenant) ID
            client_id: Azure AD Application (Client) ID
            client_secret: Azure AD Client Secret value
            drive_item_id: ID do arquivo Excel no OneDrive do usuário
            user_id: Object ID do usuário dono do arquivo no Azure AD
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.drive_item_id = drive_item_id
        self.user_id = user_id
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """Get or refresh Microsoft Graph access token."""
        from datetime import timedelta

        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=15,
        )
        response.raise_for_status()
        token_data = response.json()
        self._access_token = token_data["access_token"]
        from datetime import timedelta
        self._token_expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
        return self._access_token

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    def _make_request(self, method: str, endpoint: str, data=None) -> dict:
        """Make authenticated request to Microsoft Graph API."""
        url = f"{self.GRAPH_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }
        response = requests.request(
            method=method, url=url, headers=headers, json=data, timeout=30
        )
        if response.status_code not in (200, 201, 204):
            error_text = response.text
            if "EditModeCannotAcquireLock" in error_text:
                if "SiteReadOnly" in error_text or "Database Is Read Only" in error_text:
                    logger.error(
                        "⚠️ ERRO CRÍTICO: O site do SharePoint/OneDrive está em modo SOMENTE LEITURA. "
                        "Isso geralmente indica que a cota foi atingida ou o site foi bloqueado administrativemente."
                    )
                    raise ExcelReadOnlyError("O site do SharePoint está em modo somente leitura (Database Is Read Only).")
                else:
                    logger.error(
                        "Graph API ERRO DE ARQUIVO ABERTO: O arquivo Excel no OneDrive está aberto ou bloqueado. "
                        "Feche a janela do Excel para que o bot possa gravar os dados."
                    )
            logger.error(f"Graph API Error ({response.status_code}): {error_text}")
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    def _workbook_url(self, path: str) -> str:
        """Build workbook endpoint for the configured Excel file."""
        return f"/users/{self.user_id}/drive/items/{self.drive_item_id}/workbook{path}"

    # ─── READS ────────────────────────────────────────────────────────────────

    def _get_table_rows(self, table_name: str) -> List[List]:
        """Return all data rows (excluding header) from a workbook table."""
        endpoint = self._workbook_url(f"/tables/{table_name}/rows")
        try:
            resp = self._make_request("GET", endpoint)
            rows = resp.get("value", [])
            return [r["values"][0] for r in rows]
        except ExcelReadOnlyError:
            raise
        except Exception as e:
            logger.error(f"Error reading table {table_name}: {e}")
            return []

    def _append_table_row(self, table_name: str, values: list) -> bool:
        """Append a row to a workbook table."""
        endpoint = self._workbook_url(f"/tables/{table_name}/rows")
        try:
            self._make_request("POST", endpoint, {"values": [values]})
            return True
        except ExcelReadOnlyError:
            raise
        except Exception as e:
            logger.error(f"Error appending to table {table_name}: {e}")
            return False

    # ─── EMPLOYEES ────────────────────────────────────────────────────────────

    def get_employee(self, telegram_id: str) -> Optional[Employee]:
        """Get active employee by Telegram ID."""
        try:
            rows = self._get_table_rows(self.TABLE_FUNCIONARIOS)
            for row in rows:
                if len(row) > self.FUNCIONARIOS_COLS["telegram_id"]:
                    if str(row[self.FUNCIONARIOS_COLS["telegram_id"]]) == telegram_id:
                        ativo = str(row[self.FUNCIONARIOS_COLS["ativo"]]).lower()
                        if ativo in ["true", "1", "sim"]:
                            return Employee.from_row(row)
            return None
        except Exception as e:
            logger.error(f"Error getting employee {telegram_id}: {e}")
            return None

    def get_employee_by_username(self, username: str) -> Optional[Employee]:
        """Get active employee by Telegram username (without @)."""
        username = username.lstrip("@").lower()
        try:
            rows = self._get_table_rows(self.TABLE_FUNCIONARIOS)
            for row in rows:
                # Username is column 8 (last)
                if len(row) > self.FUNCIONARIOS_COLS["username"]:
                    if str(row[self.FUNCIONARIOS_COLS["username"]]).lower() == username:
                        ativo = str(row[self.FUNCIONARIOS_COLS["ativo"]]).lower()
                        if ativo in ["true", "1", "sim"]:
                            return Employee.from_row(row)
            return None
        except Exception as e:
            logger.error(f"Error getting employee by username {username}: {e}")
            return None

    def create_employee(self, employee: Employee) -> bool:
        """Create new employee record."""
        try:
            row_data = employee.to_row()
            return self._append_table_row(self.TABLE_FUNCIONARIOS, row_data)
        except Exception as e:
            logger.error(f"Error creating employee: {e}")
            return False

    def update_employee_field(self, search_term: str, field_index: int, new_value: str) -> bool:
        """Update a specific field of an employee found by username or name."""
        try:
            endpoint = self._workbook_url(f"/tables/{self.TABLE_FUNCIONARIOS}/rows")
            resp = self._make_request("GET", endpoint)
            rows = resp.get("value", [])

            for row in rows:
                values = row["values"][0]
                current_username = str(values[self.FUNCIONARIOS_COLS["username"]]).lower() if len(values) > self.FUNCIONARIOS_COLS["username"] else ""
                current_name = str(values[self.FUNCIONARIOS_COLS["nome"]]).lower() if len(values) > self.FUNCIONARIOS_COLS["nome"] else ""
                current_telegram_id = str(values[self.FUNCIONARIOS_COLS["telegram_id"]]).lower() if len(values) > self.FUNCIONARIOS_COLS["telegram_id"] else ""

                search_lower = search_term.lower()
                # Procura por nome, username (com ou sem pending_)
                if (
                    search_lower in current_name
                    or search_lower == current_username
                    or search_lower == current_telegram_id
                    or f"pending_{search_lower}" == current_telegram_id
                ):
                    row_index = row["index"]
                    update_endpoint = self._workbook_url(
                        f"/tables/{self.TABLE_FUNCIONARIOS}/rows/itemAt(index={row_index})"
                    )
                    new_values = list(values)
                    
                    # Ensure list is long enough for the field we want to update
                    while len(new_values) <= field_index:
                        new_values.append("")
                        
                    new_values[field_index] = new_value
                    self._make_request("PATCH", update_endpoint, {"values": [new_values]})
                    logger.info(f"Updated employee field {field_index} to '{new_value}' for search term '{search_term}'")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating employee field: {e}")
            return False

    def update_employee_telegram_id(self, pending_id: str, telegram_id: str) -> bool:
        """Update pending placeholder ID to actual Telegram ID. (Legacy/Specific method)"""
        return self.update_employee_field(pending_id, self.FUNCIONARIOS_COLS["telegram_id"], telegram_id)

    def get_employee_by_pending_id(self, pending_id: str) -> Optional[Employee]:
        """Get employee by pending placeholder ID."""
        try:
            rows = self._get_table_rows(self.TABLE_FUNCIONARIOS)
            for row in rows:
                if str(row[self.FUNCIONARIOS_COLS["telegram_id"]]).lower() == pending_id.lower():
                    ativo = str(row[self.FUNCIONARIOS_COLS["ativo"]]).lower()
                    if ativo in ["true", "1", "sim"]:
                        return Employee.from_row(row)
            return None
        except Exception as e:
            logger.error(f"Error getting employee by pending_id: {e}")
            return None

    # ─── TIMESHEET ────────────────────────────────────────────────────────────

    def log_timesheet(self, entry: TimesheetEntry) -> bool:
        """Log timesheet entry (ponto)."""
        try:
            row_data = entry.to_row()
            result = self._append_table_row(self.TABLE_PONTO, row_data)
            if result:
                logger.info(f"Timesheet logged: {entry.nome} - {entry.tipo}")
            return result
        except Exception as e:
            logger.error(f"Error logging timesheet: {e}")
            return False

    # ─── DECISIONS ────────────────────────────────────────────────────────────

    def create_decision(self, decision: Decision) -> bool:
        """Create executive decision record."""
        try:
            row_data = decision.to_row()
            result = self._append_table_row(self.TABLE_DECISOES, row_data)
            if result:
                logger.info(f"Decision created: {decision.id}")
            return result
        except Exception as e:
            logger.error(f"Error creating decision: {e}")
            return False

    # ─── SETUP ────────────────────────────────────────────────────────────────

    def ensure_sheets_exist(self) -> bool:
        """
        Verify the workbook is accessible and all tables exist.
        For Excel Online, the file and tables must be created manually
        or via the setup script (scripts/setup_excel.py).
        """
        try:
            endpoint = self._workbook_url("/tables")
            resp = self._make_request("GET", endpoint)
            tables = [t.get("name") for t in resp.get("value", [])]
            required = [self.TABLE_FUNCIONARIOS, self.TABLE_PONTO, self.TABLE_DECISOES]
            missing = [t for t in required if t not in tables]

            if missing:
                logger.warning(
                    f"Missing tables in Excel workbook: {missing}. "
                    "Run scripts/setup_excel.py to create them."
                )
            else:
                logger.info("All Excel tables verified successfully.")
            return len(missing) == 0
        except Exception as e:
            logger.error(f"Error verifying Excel workbook: {e}")
            return False
