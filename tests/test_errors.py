"""Tests for deterministic, actionable error handling."""

import pytest
from kv_to_sx.config import MappingConfig
from kv_to_sx.engine import MappingEngine
from kv_to_sx.exceptions import (
    ConfigurationError,
    MappingError,
    UnsupportedOperationError,
    XmlParseError,
)


def test_missing_required_field_raises_error(mapping_engine: MappingEngine):
    """Missing required field must raise MappingError with rule, message, and field."""
    xml_missing_text = """<KV15messages><STOPMESSAGE><messagecodenumber>100</messagecodenumber></STOPMESSAGE></KV15messages>"""
    with pytest.raises(MappingError) as exc_info:
        mapping_engine.convert(xml_missing_text)

    err_msg = str(exc_info.value)
    assert "kv15-message-text" in err_msg
    assert "KV15" in err_msg
    assert "KV15messages/STOPMESSAGE/messagecontent" in err_msg
    assert "missing or empty" in err_msg


def test_invalid_datetime_value_raises_error(mapping_engine: MappingEngine):
    """Invalid datetime format must raise MappingError identifying the field and rule."""
    xml_invalid_date = """<KV15messages><STOPMESSAGE><messagecodenumber>100</messagecodenumber><messagecontent>Test</messagecontent><messagestarttime>not-a-datetime</messagestarttime></STOPMESSAGE></KV15messages>"""
    with pytest.raises(MappingError) as exc_info:
        mapping_engine.convert(xml_invalid_date)

    err_msg = str(exc_info.value)
    assert "kv15-message-start" in err_msg
    assert "not-a-datetime" in err_msg


def test_invalid_integer_value_raises_error(mapping_engine: MappingEngine):
    """Invalid integer format must raise MappingError identifying field and rule."""
    xml_invalid_int = """<KV17cvlinfo><KV17JOURNEY><journeynumber>1001</journeynumber><lineplanningnumber>1</lineplanningnumber></KV17JOURNEY><KV17MUTATEJOURNEYSTOP><timestamp>2026-10-16T10:00:00Z</timestamp><SHORTEN><userstopcode>123</userstopcode><passagesequencenumber>four</passagesequencenumber></SHORTEN></KV17MUTATEJOURNEYSTOP></KV17cvlinfo>"""
    with pytest.raises(MappingError) as exc_info:
        mapping_engine.convert(xml_invalid_int)

    err_msg = str(exc_info.value)
    assert "kv17-stop-sequence-as-text" in err_msg
    assert "passagesequencenumber" in err_msg
    assert "four" in err_msg


def test_missing_template_variable_raises_error(mapping_engine: MappingEngine):
    """Missing template placeholder variable must raise MappingError."""
    xml_missing_var = """<KV17cvlinfo><KV17JOURNEY><journeynumber>1001</journeynumber><lineplanningnumber>1</lineplanningnumber></KV17JOURNEY><KV17MUTATEJOURNEYSTOP><timestamp>2026-10-16T10:00:00Z</timestamp><SHORTEN><passagesequencenumber>4</passagesequencenumber></SHORTEN></KV17MUTATEJOURNEYSTOP></KV17cvlinfo>"""
    with pytest.raises(MappingError) as exc_info:
        mapping_engine.convert(xml_missing_var)

    err_msg = str(exc_info.value)
    assert "kv17-shorten-description" in err_msg
    assert "userstopcode" in err_msg


def test_unsupported_operation_raises_error():
    """Unsupported mapping operation must raise UnsupportedOperationError."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"

    [[mapping]]
    name = "unknown-op"
    source.message = "KV15"
    source.path = "MSG/text"
    target.path = "Description"
    operation = "fancy_math"
    """
    engine = MappingEngine.from_toml_string(toml_str)
    with pytest.raises(UnsupportedOperationError) as exc_info:
        engine.convert("<MSG><text>abc</text></MSG>")

    err_msg = str(exc_info.value)
    assert "unknown-op" in err_msg
    assert "fancy_math" in err_msg


def test_invalid_xml_raises_error(mapping_engine: MappingEngine):
    """Malformed input XML must raise XmlParseError."""
    with pytest.raises(XmlParseError):
        mapping_engine.convert("<KV15><unclosed>")


def test_missing_value_omit_behavior():
    """Optional missing value with missing_value='omit' omits target field without error."""
    toml_str = """
    [config]
    source_format = "xml"
    target_format = "siri-sx"
    missing_value = "omit"

    [[mapping]]
    name = "optional-field"
    source.message = "KV15"
    source.path = "MSG/opt"
    target.path = "SituationNumber"
    operation = "to_string"
    required = false
    """
    engine = MappingEngine.from_toml_string(toml_str)
    output = engine.convert("<MSG></MSG>")
    assert "SituationNumber" not in output
