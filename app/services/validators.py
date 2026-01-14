"""Data validation utilities for marketing metrics."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class DataValidator:
    """Validator for marketing metric data."""

    @staticmethod
    def validate_campaign_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate campaign data fields.

        Args:
            data: Campaign data dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        if not data.get("external_id"):
            errors.append("external_id is required")
        elif len(str(data["external_id"])) > 255:
            errors.append("external_id must be <= 255 characters")

        if not data.get("campaign_name") and not data.get("campaign"):
            errors.append("campaign_name or campaign is required")
        elif len(str(data.get("campaign_name") or data.get("campaign", ""))) > 500:
            errors.append("campaign_name must be <= 500 characters")

        if not data.get("source"):
            errors.append("source is required")
        elif data["source"] not in ["meta_ads", "ga4", "google_ads"]:
            errors.append(f"source must be one of: meta_ads, ga4, google_ads (got: {data['source']})")

        return errors

    @staticmethod
    def validate_metric_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate metric data fields.

        Args:
            data: Metric data dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate date
        if not data.get("date"):
            errors.append("date is required")
        else:
            try:
                DataValidator._parse_date(data["date"])
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid date format: {str(e)}")

        # Validate numeric fields (must be non-negative)
        numeric_fields = ["impressions", "clicks", "spend", "conversions", "revenue"]
        for field in numeric_fields:
            value = data.get(field, 0)
            try:
                if field in ["spend", "revenue"]:
                    num_value = Decimal(str(value))
                else:
                    num_value = int(value)

                if num_value < 0:
                    errors.append(f"{field} must be non-negative (got: {num_value})")
            except (ValueError, TypeError, InvalidOperation) as e:
                errors.append(f"Invalid {field} value: {str(e)}")

        # Validate logical constraints
        impressions = data.get("impressions", 0)
        clicks = data.get("clicks", 0)
        conversions = data.get("conversions", 0)

        try:
            if clicks > impressions and impressions > 0:
                errors.append("clicks cannot exceed impressions")
            if conversions > clicks and clicks > 0:
                errors.append("conversions cannot exceed clicks")
        except (TypeError, ValueError):
            pass  # Skip if values aren't comparable

        return errors

    @staticmethod
    def validate_and_normalize_value(value: Any, field_type: type, default: Any = None) -> Any:
        """
        Validate and normalize a value to a specific type.

        Args:
            value: Value to validate
            field_type: Expected type (int, Decimal, str, date)
            default: Default value if value is None or invalid

        Returns:
            Normalized value
        """
        if value is None:
            return default

        try:
            if field_type == int:
                return int(float(value)) if value != "" else (default or 0)
            elif field_type == Decimal:
                return Decimal(str(value)) if value != "" else (default or Decimal("0"))
            elif field_type == str:
                return str(value) if value is not None else (default or "")
            elif field_type == date:
                return DataValidator._parse_date(value)
            else:
                return value
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.warning(f"Failed to normalize value {value} to {field_type}: {str(e)}")
            return default

    @staticmethod
    def _parse_date(date_value: Any) -> date:
        """
        Parse date from various formats.

        Args:
            date_value: Date value (string, date, datetime, etc.)

        Returns:
            date object

        Raises:
            ValueError: If date cannot be parsed
        """
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_value}")
        raise ValueError(f"Invalid date type: {type(date_value)}")

    @staticmethod
    def sanitize_string(value: Any, max_length: Optional[int] = None) -> str:
        """
        Sanitize string value.

        Args:
            value: Value to sanitize
            max_length: Maximum length (truncate if longer)

        Returns:
            Sanitized string
        """
        if value is None:
            return ""
        sanitized = str(value).strip()
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"String truncated to {max_length} characters")
        return sanitized

