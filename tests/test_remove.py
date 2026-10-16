"""Tests for remove operation."""

import xml.etree.ElementTree as ET
from kv_to_sx.engine import MappingEngine
from kv_to_sx.xml_utils import strip_namespace


def test_remove_operation(mapping_engine: MappingEngine, sample_kv15_xml: str):
    """Test that discarded/removed fields (e.g. delimiter) are not emitted to target XML."""
    output_xml = mapping_engine.convert(sample_kv15_xml)
    root = ET.fromstring(output_xml)

    # Ensure no element named 'delimiter' exists anywhere in output
    for elem in root.iter():
        assert strip_namespace(elem.tag).lower() != "delimiter"
        assert elem.text != "|"
