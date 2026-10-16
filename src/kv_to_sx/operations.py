"""Field transformation operations for mapping source values to target values."""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

from .config import GeneralConfig, MappingRule
from .exceptions import MappingError, UnsupportedOperationError
from .xml_utils import extract_element_context, get_element_text


def parse_datetime(val: str) -> datetime:
    """Parse a datetime string in standard formats (ISO 8601 / RFC 3339)."""
    val = val.strip()
    # Replace Z with +00:00 for python's fromisoformat
    if val.endswith("Z") or val.endswith("z"):
        val = val[:-1] + "+00:00"
    return datetime.fromisoformat(val)


def format_datetime_iso(dt: datetime) -> str:
    """Format datetime in standard ISO 8601 UTC or offset format."""
    # SIRI standard typically uses ISO 8601 e.g. 2026-10-16T10:15:30Z
    if dt.tzinfo is not None:
        utc_dt = dt.astimezone(timezone.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_rule(
    rule: MappingRule,
    root: ET.Element,
    source_element: Optional[ET.Element],
    config: GeneralConfig,
) -> Union[None, str, Dict[str, str]]:
    """Evaluate a mapping rule against the source XML and return target value(s).

    Returns:
    - None: Field is omitted or removed.
    - str: Single scalar value to set at rule.target_path.
    - Dict[str, str]: Mapping of target_path -> value (for split operations).
    """
    op = rule.operation.lower()

    if op == "remove":
        # Discard the source field
        return None

    # Handle template operation where source_element is the container element
    if op == "template":
        if source_element is None:
            if rule.required or config.missing_value == "error":
                raise MappingError(
                    "required source element is missing",
                    rule_name=rule.name,
                    source_message=rule.source_message,
                    field_path=rule.source_path,
                )
            return None

        template = rule.template or ""
        context = extract_element_context(source_element)
        placeholders = re.findall(r"\{([a-zA-Z0-9_]+)\}", template)

        result = template
        for placeholder in placeholders:
            val = context.get(placeholder)
            if val is None or val == "":
                if rule.required or config.invalid_value == "error":
                    raise MappingError(
                        f"template variable '{{{placeholder}}}' not found in source element",
                        rule_name=rule.name,
                        source_message=rule.source_message,
                        field_path=rule.source_path,
                    )
                val = ""
            result = result.replace(f"{{{placeholder}}}", val)
        return result

    # For other operations, extract raw text
    raw_value = get_element_text(source_element)

    if raw_value is None or raw_value == "":
        if rule.required:
            raise MappingError(
                f"required source field '{rule.source_path}' is missing or empty",
                rule_name=rule.name,
                source_message=rule.source_message,
                field_path=rule.source_path,
            )
        if config.missing_value == "error":
            raise MappingError(
                f"source field '{rule.source_path}' is missing",
                rule_name=rule.name,
                source_message=rule.source_message,
                field_path=rule.source_path,
            )
        return None

    if op == "direct":
        return raw_value

    elif op == "to_string":
        return str(raw_value)

    elif op == "to_datetime":
        try:
            dt = parse_datetime(raw_value)
            return format_datetime_iso(dt)
        except Exception as e:
            if config.invalid_value == "error" or rule.required:
                raise MappingError(
                    f"invalid datetime value '{raw_value}': {e}",
                    rule_name=rule.name,
                    source_message=rule.source_message,
                    field_path=rule.source_path,
                ) from e
            return None

    elif op == "to_integer":
        try:
            val = int(raw_value)
            return str(val)
        except Exception as e:
            if config.invalid_value == "error" or rule.required:
                raise MappingError(
                    f"invalid integer value '{raw_value}': {e}",
                    rule_name=rule.name,
                    source_message=rule.source_message,
                    field_path=rule.source_path,
                ) from e
            return None

    elif op == "split":
        delimiter = rule.delimiter or " | "
        parts = [p.strip() for p in raw_value.split(delimiter)]
        target_paths = rule.target_paths or rule.parts

        result_dict: Dict[str, str] = {}
        for idx, target_path in enumerate(target_paths):
            if idx < len(parts):
                result_dict[target_path] = parts[idx]
            else:
                if rule.required or config.missing_value == "error":
                    raise MappingError(
                        f"split produced {len(parts)} parts, but target path '{target_path}' requires a value",
                        rule_name=rule.name,
                        source_message=rule.source_message,
                        field_path=rule.source_path,
                    )
        return result_dict

    else:
        raise UnsupportedOperationError(
            rule.operation,
            rule_name=rule.name,
            source_message=rule.source_message,
            field_path=rule.source_path,
        )
