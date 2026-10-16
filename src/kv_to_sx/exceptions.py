"""Custom exception types for kv-to-sx."""

from typing import Optional


class KvToSxError(Exception):
    """Base exception for all kv-to-sx errors."""
    pass


class ConfigurationError(KvToSxError):
    """Raised when there is an issue with the mapping configuration file."""
    pass


class XmlParseError(KvToSxError):
    """Raised when input XML cannot be parsed."""
    pass


class MappingError(KvToSxError):
    """Raised when a mapping rule cannot be evaluated or applied.

    Identifies the relevant input message, field, and mapping rule when possible.
    """

    def __init__(
        self,
        detail: str,
        *,
        rule_name: Optional[str] = None,
        source_message: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        self.detail = detail
        self.rule_name = rule_name
        self.source_message = source_message
        self.field_path = field_path

        parts = []
        if rule_name:
            parts.append(f"rule '{rule_name}'")
        if source_message:
            parts.append(f"message '{source_message}'")
        if field_path:
            parts.append(f"field '{field_path}'")

        if parts:
            context = ", ".join(parts)
            msg = f"Mapping error in {context}: {detail}"
        else:
            msg = f"Mapping error: {detail}"

        super().__init__(msg)


class UnsupportedOperationError(MappingError):
    """Raised when an unknown or unsupported mapping operation is specified."""

    def __init__(
        self,
        operation: str,
        *,
        rule_name: Optional[str] = None,
        source_message: Optional[str] = None,
        field_path: Optional[str] = None,
    ):
        super().__init__(
            f"unsupported operation '{operation}'",
            rule_name=rule_name,
            source_message=source_message,
            field_path=field_path,
        )
