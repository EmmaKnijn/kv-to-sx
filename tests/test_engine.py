"""Tests demonstrating mapping engine independently of command-line I/O."""

import xml.etree.ElementTree as ET
from kv_to_sx.config import MappingConfig
from kv_to_sx.engine import MappingEngine

SIRI_NS = "{http://www.siri.org.uk/siri}"


def test_engine_independent_conversion_with_string_and_element():
    """Engine can convert from XML string, bytes, or parsed ElementTree element directly."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [defaults]
    participant_ref = "test-adapter"

    [[mapping]]
    name = "sit-id"
    source.message = "TESTMSG"
    source.path = "TESTMSG/id"
    target.path = "SituationNumber"
    operation = "direct"
    """
    engine = MappingEngine.from_toml_string(toml_str)

    xml_text = "<TESTMSG><id>42</id></TESTMSG>"

    # 1. Test with string
    res1 = engine.convert(xml_text)
    assert "<SituationNumber>42</SituationNumber>" in res1
    assert "<ParticipantRef>test-adapter</ParticipantRef>" in res1

    # 2. Test with bytes
    res2 = engine.convert(xml_text.encode("utf-8"))
    assert "<SituationNumber>42</SituationNumber>" in res2

    # 3. Test with ET.Element
    elem = ET.fromstring(xml_text)
    res3 = engine.convert(elem)
    assert "<SituationNumber>42</SituationNumber>" in res3


def test_engine_multiple_messages_in_batch():
    """Engine converts repeated messages in a single batch into multiple PtSituationElements."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [[mapping]]
    name = "msg-id"
    source.message = "KV15"
    source.path = "KV15messages/STOPMESSAGE/messagecodenumber"
    target.path = "SituationNumber"
    operation = "to_string"

    [[mapping]]
    name = "msg-text"
    source.message = "KV15"
    source.path = "KV15messages/STOPMESSAGE/messagecontent"
    target.path = "Description"
    operation = "direct"
    """
    engine = MappingEngine.from_toml_string(toml_str)
    batch_xml = """
    <KV15messages>
      <STOPMESSAGE>
        <messagecodenumber>101</messagecodenumber>
        <messagecontent>First message</messagecontent>
      </STOPMESSAGE>
      <STOPMESSAGE>
        <messagecodenumber>102</messagecodenumber>
        <messagecontent>Second message</messagecontent>
      </STOPMESSAGE>
    </KV15messages>
    """
    output_xml = engine.convert(batch_xml)
    root = ET.fromstring(output_xml)

    situations = root.findall(f".//{SIRI_NS}PtSituationElement")
    assert len(situations) == 2

    sit_nums = [s.find(f"{SIRI_NS}SituationNumber").text for s in situations]
    assert sit_nums == ["101", "102"]
