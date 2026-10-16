"""Shared fixtures for kv-to-sx tests."""

from pathlib import Path
import pytest

from kv_to_sx.config import MappingConfig
from kv_to_sx.engine import MappingEngine

MAPPING_TOML_PATH = Path(__file__).resolve().parent.parent / "mapping.toml"


@pytest.fixture
def mapping_config() -> MappingConfig:
    """Fixture returning MappingConfig loaded from root mapping.toml."""
    return MappingConfig.from_file(MAPPING_TOML_PATH)


@pytest.fixture
def mapping_engine(mapping_config: MappingConfig) -> MappingEngine:
    """Fixture returning MappingEngine loaded with root mapping.toml."""
    return MappingEngine(mapping_config)


@pytest.fixture
def sample_kv17_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<KV17cvlinfo xmlns="http://bison.connekt.nl/tmi8/kv17/msg">
  <KV17JOURNEY>
    <dataownercode>ARR</dataownercode>
    <lineplanningnumber>315</lineplanningnumber>
    <operatingday>2026-10-16</operatingday>
    <journeynumber>1042</journeynumber>
    <reinforcementnumber>0</reinforcementnumber>
  </KV17JOURNEY>
  <KV17MUTATEJOURNEYSTOP>
    <timestamp>2026-10-16T10:15:30Z</timestamp>
    <SHORTEN>
      <userstopcode>57000101</userstopcode>
      <passagesequencenumber>4</passagesequencenumber>
    </SHORTEN>
  </KV17MUTATEJOURNEYSTOP>
</KV17cvlinfo>"""


@pytest.fixture
def sample_kv8_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<bison:BISON xmlns:bison="http://bison.connekt.nl/tmi8/kv8/msg">
  <TimingPoint>
    <KV8generalmessages>
      <GENERALMESSAGEUPDATE>
        <dataownercode>GVB</dataownercode>
        <timingpointcode>30005123</timingpointcode>
        <messagestarttime>2026-10-16T08:00:00Z</messagestarttime>
        <messagecontent>Elevator out of order at platform 2</messagecontent>
      </GENERALMESSAGEUPDATE>
    </KV8generalmessages>
  </TimingPoint>
</bison:BISON>"""


@pytest.fixture
def sample_kv15_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<KV15messages xmlns="http://bison.connekt.nl/tmi8/kv15/msg">
  <STOPMESSAGE>
    <messagecodenumber>90210</messagecodenumber>
    <userstopcode>34001234</userstopcode>
    <messagecontent>Track maintenance | Bus substitution in place until 18:00</messagecontent>
    <messagestarttime>2026-10-16T07:30:00Z</messagestarttime>
    <delimiter>|</delimiter>
  </STOPMESSAGE>
</KV15messages>"""
