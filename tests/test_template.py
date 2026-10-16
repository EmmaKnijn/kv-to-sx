"""Tests for template composition transformation."""

import xml.etree.ElementTree as ET
from kv_to_sx.config import MappingConfig
from kv_to_sx.engine import MappingEngine

SIRI_NS = "{http://www.siri.org.uk/siri}"


def test_kv17_template_shorten_description(mapping_engine: MappingEngine, sample_kv17_xml: str):
    """Test template operation 'Stop {userstopcode} is cancelled' from mapping.toml."""
    output_xml = mapping_engine.convert(sample_kv17_xml)
    root = ET.fromstring(output_xml)

    desc = root.find(f".//{SIRI_NS}Description/{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "Stop 57000101 is cancelled"


def test_multi_variable_template():
    """Test template composing multiple fields into target description."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [[mapping]]
    name = "multi-var"
    source.message = "KV17cvlinfo"
    source.path = "KV17cvlinfo/MUTATION"
    target.path = "Description"
    operation = "template"
    template = "Line {line} delayed by {delay} mins due to {reason}"
    """
    engine = MappingEngine.from_toml_string(toml_str)
    xml_input = """<KV17cvlinfo><MUTATION><line>51</line><delay>15</delay><reason>signal failure</reason></MUTATION></KV17cvlinfo>"""
    output_xml = engine.convert(xml_input)
    root = ET.fromstring(output_xml)

    desc = root.find(f".//{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "Line 51 delayed by 15 mins due to signal failure"
