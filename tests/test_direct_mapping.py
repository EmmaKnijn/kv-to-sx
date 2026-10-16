"""Tests for direct mapping operations."""

import xml.etree.ElementTree as ET
from kv_to_sx.engine import MappingEngine
from kv_to_sx.xml_utils import strip_namespace

SIRI_NS = "{http://www.siri.org.uk/siri}"


def test_kv17_direct_mapping(mapping_engine: MappingEngine, sample_kv17_xml: str):
    """KV17 direct mapping: lineplanningnumber -> Affects/Lines/Line/LineRef."""
    output_xml = mapping_engine.convert(sample_kv17_xml)
    root = ET.fromstring(output_xml)

    # LineRef should be 315 from KV17JOURNEY/lineplanningnumber
    line_ref = root.find(f".//{SIRI_NS}LineRef")
    assert line_ref is not None
    assert line_ref.text == "315"


def test_kv8_direct_mapping(mapping_engine: MappingEngine, sample_kv8_xml: str):
    """KV7/8 direct mappings: timingpointcode -> StopPointRef, messagecontent -> Description."""
    output_xml = mapping_engine.convert(sample_kv8_xml)
    root = ET.fromstring(output_xml)

    stop_ref = root.find(f".//{SIRI_NS}StopPointRef")
    assert stop_ref is not None
    assert stop_ref.text == "30005123"

    desc = root.find(f".//{SIRI_NS}Description/{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "Elevator out of order at platform 2"


def test_kv15_direct_mapping():
    """KV15 direct mapping with a configuration having only direct mapping."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [[mapping]]
    name = "kv15-message-text"
    source.message = "KV15"
    source.path = "KV15messages/STOPMESSAGE/messagecontent"
    target.path = "Description/Description"
    operation = "direct"
    required = true
    """
    engine = MappingEngine.from_toml_string(toml_str)
    xml_input = """<KV15messages><STOPMESSAGE><messagecontent>Direct test message</messagecontent></STOPMESSAGE></KV15messages>"""
    output_xml = engine.convert(xml_input)
    root = ET.fromstring(output_xml)

    desc = root.find(f".//{SIRI_NS}Description/{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "Direct test message"
