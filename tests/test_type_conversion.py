"""Tests for type conversion operations: to_string, to_datetime, to_integer."""

import xml.etree.ElementTree as ET
from kv_to_sx.engine import MappingEngine

SIRI_NS = "{http://www.siri.org.uk/siri}"
KV17_NS = "{http://bison.connekt.nl/tmi8/kv17/msg}"


def test_to_datetime_conversion(mapping_engine: MappingEngine, sample_kv17_xml: str):
    """Test datetime conversion in KV17 mutation time to VersionedAtTime."""
    output_xml = mapping_engine.convert(sample_kv17_xml)
    root = ET.fromstring(output_xml)

    vat = root.find(f".//{SIRI_NS}VersionedAtTime")
    assert vat is not None
    assert vat.text == "2026-10-16T10:15:30Z"


def test_to_integer_conversion(mapping_engine: MappingEngine, sample_kv17_xml: str):
    """Test integer conversion in KV17 passage sequence number."""
    output_xml = mapping_engine.convert(sample_kv17_xml)
    root = ET.fromstring(output_xml)

    psn = root.find(f".//{KV17_NS}PassageSequenceNumber")
    assert psn is not None
    assert psn.text == "4"


def test_to_string_conversion(mapping_engine: MappingEngine, sample_kv17_xml: str):
    """Test string conversion for journey number to SituationNumber."""
    output_xml = mapping_engine.convert(sample_kv17_xml)
    root = ET.fromstring(output_xml)

    sit_num = root.find(f".//{SIRI_NS}SituationNumber")
    assert sit_num is not None
    assert sit_num.text == "1042"
