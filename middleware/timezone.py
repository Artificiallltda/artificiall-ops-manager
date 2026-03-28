"""
Middleware de Timezone para Artificiall Ops Manager.

Gerencia conversão e formatação de timestamps para America/Sao_Paulo.
"""

import logging
from datetime import datetime
from typing import Optional

import pytz

logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    """
    Timezone conversion and formatting middleware.
    
    All timestamps are stored in America/Sao_Paulo timezone (BRT/BRST).
    """

    TIMEZONE_NAME = "America/Sao_Paulo"

    def __init__(self, timezone_name: str = TIMEZONE_NAME):
        """
        Initialize Timezone middleware.

        Args:
            timezone_name: IANA timezone name (default: America/Sao_Paulo)
        """
        self.timezone = pytz.timezone(timezone_name)
        logger.info(f"Timezone middleware initialized: {timezone_name}")

    def get_brazil_timestamp(self) -> datetime:
        """
        Get current timestamp in America/Sao_Paulo timezone.

        Returns:
            Timezone-aware datetime object
        """
        now = datetime.now(self.timezone)
        logger.debug(f"Brazil timestamp: {now.isoformat()}")
        return now

    def format_timestamp(
        self,
        dt: datetime,
        format_string: str = "%d/%m/%Y %H:%M:%S",
    ) -> str:
        """
        Format datetime to string in Brazil timezone.

        Args:
            dt: Datetime object (timezone-aware or naive)
            format_string: strftime format string

        Returns:
            Formatted date string
        """
        # Convert to Brazil timezone if needed
        if dt.tzinfo is None:
            # Naive datetime - assume UTC and convert
            dt = pytz.utc.localize(dt)

        brazil_time = dt.astimezone(self.timezone)
        return brazil_time.strftime(format_string)

    def parse_timestamp(
        self,
        date_string: str,
        format_string: str = "%d/%m/%Y %H:%M:%S",
    ) -> datetime:
        """
        Parse string to datetime in Brazil timezone.

        Args:
            date_string: Date string to parse
            format_string: strptime format string

        Returns:
            Timezone-aware datetime object
        """
        dt = datetime.strptime(date_string, format_string)
        # Localize to Brazil timezone
        brazil_dt = self.timezone.localize(dt)
        return brazil_dt

    def format_for_google_sheets(self, dt: datetime) -> str:
        """
        Format datetime for Google Sheets compatibility.

        Google Sheets accepts ISO 8601 or DD/MM/YYYY HH:MM:SS format.

        Args:
            dt: Datetime object

        Returns:
            Formatted string for Google Sheets
        """
        brazil_time = dt.astimezone(self.timezone)
        return brazil_time.strftime("%d/%m/%Y %H:%M:%S")

    def format_date_only(self, dt: datetime) -> str:
        """
        Format date only (no time) for Google Sheets.

        Args:
            dt: Datetime object

        Returns:
            Date string (DD/MM/YYYY)
        """
        brazil_time = dt.astimezone(self.timezone)
        return brazil_time.strftime("%d/%m/%Y")

    def get_timezone_offset(self, dt: Optional[datetime] = None) -> str:
        """
        Get timezone offset string for current or given datetime.

        Args:
            dt: Optional datetime (uses current time if None)

        Returns:
            Offset string (e.g., "-03:00" for BRT, "-02:00" for BRST)
        """
        if dt is None:
            dt = self.get_brazil_timestamp()
        else:
            dt = dt.astimezone(self.timezone)

        # Get UTC offset
        offset = dt.utcoffset()
        if offset:
            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes, _ = divmod(remainder, 60)
            sign = "-" if total_seconds < 0 else "+"
            return f"{sign}{hours:02d}:{minutes:02d}"
        return "-03:00"

    def is_business_hours(
        self,
        dt: Optional[datetime] = None,
        start_hour: int = 9,
        end_hour: int = 18,
    ) -> bool:
        """
        Check if datetime falls within business hours.

        Args:
            dt: Optional datetime (uses current time if None)
            start_hour: Business start hour (default: 9)
            end_hour: Business end hour (default: 18)

        Returns:
            True if within business hours, False otherwise
        """
        if dt is None:
            dt = self.get_brazil_timestamp()
        else:
            dt = dt.astimezone(self.timezone)

        # Check if weekday
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Check if within hours
        return start_hour <= dt.hour < end_hour

    @classmethod
    def from_env(cls) -> "TimezoneMiddleware":
        """
        Create TimezoneMiddleware instance from environment variables.

        Expects:
            - TIMEZONE: Timezone name (default: America/Sao_Paulo)

        Returns:
            TimezoneMiddleware instance
        """
        import os
        timezone_name = os.getenv("TIMEZONE", cls.TIMEZONE_NAME)
        return cls(timezone_name=timezone_name)
