"""Mapping engine that converts source XML to SIRI-SX according to configuration."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import xml.etree.ElementTree as ET

from .config import MappingConfig, MappingRule
from .exceptions import MappingError
from .operations import evaluate_rule
from .siri import (
    SIRI_NS,
    create_siri_document,
    serialize_siri_document,
    set_target_path,
)
from .xml_utils import (
    detect_message_type,
    find_elements_by_path,
    parse_xml,
    strip_namespace,
)


class MappingEngine:
    """The mapping engine converts KV XML messages into SIRI-SX messages."""

    def __init__(self, config: MappingConfig):
        self.config = config

    @classmethod
    def from_toml_file(cls, path: Union[str, Path]) -> "MappingEngine":
        config = MappingConfig.from_file(path)
        return cls(config)

    @classmethod
    def from_toml_string(cls, toml_str: str) -> "MappingEngine":
        config = MappingConfig.from_toml_string(toml_str)
        return cls(config)

    def _find_message_units(self, root: ET.Element, message_type: str) -> List[ET.Element]:
        """Find repeated message payload units within root, or return [root] for single unit."""
        # Common message payload elements that may repeat in a batch
        repeat_tags = ["STOPMESSAGE", "GENERALMESSAGEUPDATE", "KV17cvlinfo"]
        for tag in repeat_tags:
            matches = [
                desc for desc in root.iter()
                if strip_namespace(desc.tag).lower() == tag.lower()
            ]
            if len(matches) > 1:
                return matches

        return [root]

    def _convert_unit(
        self,
        unit: ET.Element,
        rules: List[MappingRule],
        message_type: str,
    ) -> ET.Element:
        """Convert a single source message unit into a PtSituationElement."""
        situation = ET.Element(f"{{{SIRI_NS}}}PtSituationElement")
        default_lang = self.config.defaults.get("default_language")

        for rule in rules:
            if not rule.source_path:
                continue

            matches = find_elements_by_path(unit, rule.source_path)

            if not matches:
                # Field is missing: evaluate with None to trigger missing/required handling
                val = evaluate_rule(rule, unit, None, self.config.config)
                if val is not None:
                    if isinstance(val, dict):
                        for t_path, part in val.items():
                            set_target_path(situation, t_path, part, default_lang)
                    elif rule.target_path:
                        set_target_path(situation, rule.target_path, val, default_lang)
                continue

            # If template operation, run once on the container element
            if rule.operation.lower() == "template":
                val = evaluate_rule(rule, unit, matches[0], self.config.config)
                if val is not None and rule.target_path:
                    set_target_path(situation, rule.target_path, val, default_lang)
                continue

            # For each matched source element, evaluate and set target path
            for match in matches:
                val = evaluate_rule(rule, unit, match, self.config.config)
                if val is None:
                    continue

                if isinstance(val, dict):
                    # Result from split operation
                    for t_path, part in val.items():
                        set_target_path(situation, t_path, part, default_lang)
                elif rule.target_path:
                    set_target_path(situation, rule.target_path, val, default_lang)

        return situation

    def convert(
        self,
        xml_input: Union[str, bytes, ET.Element],
        source_message: Optional[str] = None,
    ) -> str:
        """Convert an input KV XML into a SIRI-SX XML string.

        Args:
            xml_input: XML string, bytes, or parsed ElementTree Element.
            source_message: Optional override for the source message type.

        Returns:
            Pretty-printed SIRI-SX XML document string.
        """
        if isinstance(xml_input, (str, bytes)):
            if isinstance(xml_input, bytes):
                xml_input = xml_input.decode("utf-8")
            root = parse_xml(xml_input)
        elif isinstance(xml_input, ET.Element):
            root = xml_input
        else:
            raise TypeError(f"Expected str, bytes, or ET.Element, got {type(xml_input)}")

        candidate_types = list(dict.fromkeys(r.source_message for r in self.config.rules))
        detected_message = source_message or detect_message_type(root, candidate_types)

        if not detected_message:
            raise MappingError(
                f"unable to detect source message type from input XML (candidates: {', '.join(candidate_types)})"
            )

        rules = self.config.get_rules_for_message(detected_message)
        if not rules:
            raise MappingError(
                f"no mapping rules configured for source message '{detected_message}'"
            )

        units = self._find_message_units(root, detected_message)
        situations = [self._convert_unit(unit, rules, detected_message) for unit in units]

        siri_doc = create_siri_document(situations, self.config.defaults)
        return serialize_siri_document(siri_doc)
