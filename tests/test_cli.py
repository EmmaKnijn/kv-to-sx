"""Tests for the command-line interface: stdin input, file input, exit codes, output options."""

import io
from pathlib import Path
import pytest

from kv_to_sx.cli import main

MAPPING_FILE = str(Path(__file__).resolve().parent.parent / "mapping.toml")
KV17_FILE = str(Path(__file__).resolve().parent.parent / "examples" / "kv17_input.xml")
KV8_FILE = str(Path(__file__).resolve().parent.parent / "examples" / "kv8_input.xml")
KV15_FILE = str(Path(__file__).resolve().parent.parent / "examples" / "kv15_input.xml")


def test_cli_file_input(capsys):
    """CLI reads input from a file argument and outputs SIRI XML to stdout."""
    exit_code = main(["-m", MAPPING_FILE, KV17_FILE])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "<SituationNumber>1042</SituationNumber>" in captured.out
    assert "<LineRef>315</LineRef>" in captured.out
    assert captured.err == ""


def test_cli_stdin_implicit(monkeypatch, capsys):
    """CLI reads input from stdin when no file argument is provided."""
    xml_content = Path(KV17_FILE).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(xml_content))

    exit_code = main(["-m", MAPPING_FILE])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "<SituationNumber>1042</SituationNumber>" in captured.out


def test_cli_stdin_dash(monkeypatch, capsys):
    """CLI reads input from stdin when '-' is supplied."""
    xml_content = Path(KV17_FILE).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(xml_content))

    exit_code = main(["-m", MAPPING_FILE, "-"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "<SituationNumber>1042</SituationNumber>" in captured.out


def test_cli_file_and_stdin_identical(monkeypatch, capsys):
    """File input and stdin input produce identical converted output."""
    # File input
    main(["-m", MAPPING_FILE, KV8_FILE])
    file_out = capsys.readouterr().out

    # Stdin input
    xml_content = Path(KV8_FILE).read_text(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(xml_content))
    main(["-m", MAPPING_FILE, "-"])
    stdin_out = capsys.readouterr().out

    assert file_out == stdin_out


def test_cli_output_file(tmp_path):
    """CLI writes to file when -o is specified."""
    out_file = tmp_path / "output.xml"
    exit_code = main(["-m", MAPPING_FILE, "-o", str(out_file), KV15_FILE])
    assert exit_code == 0

    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<SituationNumber>90210</SituationNumber>" in content


def test_cli_nonexistent_input_file(capsys):
    """CLI exits with code 1 and error message on missing input file."""
    exit_code = main(["-m", MAPPING_FILE, "nonexistent.xml"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Input file 'nonexistent.xml' not found" in captured.err


def test_cli_nonexistent_mapping_file(capsys):
    """CLI exits with code 1 and error message on missing mapping file."""
    exit_code = main(["-m", "nonexistent_mapping.toml", KV17_FILE])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Mapping configuration file 'nonexistent_mapping.toml' not found" in captured.err


def test_cli_empty_stdin(monkeypatch, capsys):
    """CLI exits with code 1 on empty stdin."""
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    exit_code = main(["-m", MAPPING_FILE, "-"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Standard input is empty" in captured.err
