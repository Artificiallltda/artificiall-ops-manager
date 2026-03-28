"""
Microsoft Teams API Integration for Artificiall Ops Manager.

Handles Teams online meeting creation via Microsoft Graph API
using OAuth 2.0 Client Credentials flow (Azure AD).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

import requests

logger = logging.getLogger(__name__)


class TeamsAPIIntegration:
    """Integration with Microsoft Graph API for Teams meeting creation."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, organizer_user_id: str = ""):
        """
        Initialize Microsoft Teams API integration.

        Args:
            tenant_id: Azure AD Directory (Tenant) ID
            client_id: Azure AD Application (Client) ID
            client_secret: Azure AD Client Secret value
            organizer_user_id: Object ID do usuario organizador no Azure AD
                               (obrigatorio para Application permissions)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.organizer_user_id = organizer_user_id
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """
        Get or refresh Microsoft Graph access token using Client Credentials flow.

        Returns:
            Access token string
        """
        # Return cached token if still valid (with 5 minute buffer)
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                logger.debug("Using cached Microsoft Graph access token")
                return self._access_token

        token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)

        try:
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
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info("Microsoft Graph access token obtained successfully")
            return self._access_token

        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to obtain Microsoft Graph token: {e} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error obtaining Microsoft Graph token: {e}")
            raise

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """
        Make an authenticated HTTP request to the Microsoft Graph API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., /me/onlineMeetings)
            data: Request body as dictionary (for POST/PATCH)

        Returns:
            Response JSON as dictionary
        """
        url = f"{self.GRAPH_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()

            # Some endpoints return 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Microsoft Graph API HTTP error: {e} - Response: {e.response.text}"
            )
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Microsoft Graph API request failed: {e}")
            raise

    def create_calendar_event(
        self,
        subject: str,
        start_time: datetime,
        duration: int = 60,
        attendees: list = None,
        content: str = "Reunião agendada via Artificiall Ops Manager."
    ) -> Dict:
        """
        Create a new Outlook Calendar event with an integrated Teams meeting link.

        Args:
            subject: Event title
            start_time: Start time (datetime object)
            duration: Duration in minutes
            attendees: List of email addresses to invite
            content: Body text for the meeting invite

        Returns:
            Dictionary with event details
        """
        end_time = start_time + timedelta(minutes=duration)
        
        # Format for ISO 8601 with Z suffix (UTC)
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Prepare attendees list
        attendee_list = []
        if attendees:
            for email in attendees:
                attendee_list.append({
                    "emailAddress": {
                        "address": email
                    },
                    "type": "required"
                })

        event_payload = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": content
            },
            "start": {
                "dateTime": start_str,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_str,
                "timeZone": "UTC"
            },
            "attendees": attendee_list,
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness"
        }

        try:
            if not self.organizer_user_id:
                raise ValueError("MICROSOFT_ORGANIZER_ID nao configurado.")

            endpoint = f"/users/{self.organizer_user_id}/events"
            response = self._make_request("POST", endpoint, event_payload)

            return {
                "id": response.get("id"),
                "join_url": response.get("onlineMeeting", {}).get("joinUrl"),
                "subject": response.get("subject"),
                "start": response.get("start", {}).get("dateTime"),
                "web_link": response.get("webLink") # Link para o evento no Outlook Web
            }
        except Exception as e:
            logger.error(f"Failed to create Calendar event: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test the Microsoft Graph API connection by fetching app service info.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # A lightweight call to verify the token works
            self._get_access_token()
            logger.info("Microsoft Graph connection test passed — token obtained.")
            return True
        except Exception as e:
            logger.error(f"Microsoft Graph connection test failed: {e}")
            return False
