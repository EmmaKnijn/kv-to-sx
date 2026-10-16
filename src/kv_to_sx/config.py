"""Configuration model and loader for kv-to-sx mapping files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import tomllib

from .exceptions import ConfigurationError


@dataclass
class GeneralConfig:
    """General configuration options."""
    source_format: str = "xml"
    target_format: str = "siri-sx"
    path_style: str = "element-path"
    missing_value: str = "omit"  # "omit" or "error"
    invalid_value: str = "error"  # "error" or "omit"


@dataclass
class MappingRule:
    """A single mapping rule defining how to convert source fields to SIRI-SX."""
    name: str
    source_message: str
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    target_paths: List[str] = field(default_factory=list)
    operation: str = "direct"
    required: bool = False
    delimiter: Optional[str] = None
    parts: List[str] = field(default_factory=list)
    template: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MappingRule":
        name = data.get("name")
        if not name:
            raise ConfigurationError("Mapping rule is missing required 'name' field")

        # Source specification
        source_info = data.get("source")
        if not isinstance(source_info, dict):
            raise ConfigurationError(f"Rule '{name}' missing 'source' table")
        source_message = source_info.get("message")
        if not source_message:
            raise ConfigurationError(f"Rule '{name}' missing 'source.message'")
        source_path = source_info.get("path")

        # Target specification
        target_info = data.get("target") or {}
        target_path = target_info.get("path")
        target_paths = target_info.get("paths", [])
        if isinstance(target_paths, str):
            target_paths = [target_paths]

        operation = data.get("operation", "direct")
        required = bool(data.get("required", False))
        delimiter = data.get("delimiter")
        parts = data.get("parts", [])
        if isinstance(parts, str):
            parts = [parts]
        template = data.get("template")

        # If operation is split and target_paths is empty but parts is given
        if not target_paths and parts:
            target_paths = list(parts)

        return cls(
            name=name,
            source_message=source_message,
            source_path=source_path,
            target_path=target_path,
            target_paths=target_paths,
            operation=operation,
            required=required,
            delimiter=delimiter,
            parts=parts,
            template=template,
        )


@dataclass
class MappingConfig:
    """The root mapping configuration loaded from a TOML file."""
    config: GeneralConfig = field(default_factory=GeneralConfig)
    rules: List[MappingRule] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_toml_string(cls, toml_str: str) -> "MappingConfig":
        try:
            data = tomllib.loads(toml_str)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse TOML configuration: {e}") from e

        # Parse general config
        cfg_dict = data.get("config", {})
        config = GeneralConfig(
            source_format=cfg_dict.get("source_format", "xml"),
            target_format=cfg_dict.get("target_format", "siri-sx"),
            path_style=cfg_dict.get("path_style", "element-path"),
            missing_value=cfg_dict.get("missing_value", "omit"),
            invalid_value=cfg_dict.get("invalid_value", "error"),
        )

        # Parse mapping rules
        rules_data = data.get("mapping", [])
        if not isinstance(rules_data, list):
            raise ConfigurationError("'mapping' section must be an array of tables")

        rules = [MappingRule.from_dict(r) for r in rules_data]
        defaults = data.get("defaults", {})

        return cls(config=config, rules=rules, defaults=defaults)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "MappingConfig":
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigurationError(f"Mapping configuration file not found: {file_path}")
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ConfigurationError(f"Cannot read mapping file '{file_path}': {e}") from e
        return cls.from_toml_string(content)

    def get_rules_for_message(self, message_type: str) -> List[MappingRule]:
        """Return all mapping rules applicable to the given source message type."""
        return [r for r in self.rules if r.source_message == message_type]
