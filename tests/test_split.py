"""Tests for split transformation operation."""

import xml.etree.ElementTree as ET
from kv_to_sx.config import MappingConfig
from kv_to_sx.engine import MappingEngine

SIRI_NS = "{http://www.siri.org.uk/siri}"


def test_split_transformation_from_mapping_toml(mapping_engine: MappingEngine, sample_kv15_xml: str):
    """Test splitting messagecontent into Summary and Description using mapping.toml."""
    output_xml = mapping_engine.convert(sample_kv15_xml)
    root = ET.fromstring(output_xml)

    summary = root.find(f".//{SIRI_NS}Summary/{SIRI_NS}Summary")
    assert summary is not None
    assert summary.text == "Track maintenance"

    desc = root.find(f".//{SIRI_NS}Description/{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "Bus substitution in place until 18:00"


def test_split_custom_delimiter():
    """Test splitting with a custom delimiter."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [[mapping]]
    name = "colon-split"
    source.message = "KV15"
    source.path = "MSG/text"
    target.paths = ["Summary", "Description"]
    operation = "split"
    delimiter = "::"
    """
    engine = MappingEngine.from_toml_string(toml_str)
    xml_input = "<MSG><text>PartOne::PartTwo</text></MSG>"
    output_xml = engine.convert(xml_input)
    root = ET.fromstring(output_xml)

    summary = root.find(f".//{SIRI_NS}Summary")
    assert summary is not None
    assert summary.text == "PartOne"

    desc = root.find(f".//{SIRI_NS}Description")
    assert desc is not None
    assert desc.text == "PartTwo"
