"""Tests for output formatting."""

import json

from bunq_cli.output import format_output


def test_json_format_list():
    data = [{"id": 1, "name": "Test"}]
    result = format_output(data, fmt="json")
    parsed = json.loads(result)
    assert parsed == data


def test_json_format_dict():
    data = {"id": 1, "name": "Test"}
    result = format_output(data, fmt="json")
    parsed = json.loads(result)
    assert parsed == data


def test_table_format_list():
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    result = format_output(data, fmt="table")
    assert "Alice" in result
    assert "Bob" in result
    assert "id" in result


def test_table_format_dict():
    data = {"id": 1, "name": "Test"}
    result = format_output(data, fmt="table")
    assert "name" in result
    assert "Test" in result


def test_table_with_columns():
    data = [{"id": 1, "name": "Alice", "email": "a@b.c"}]
    result = format_output(data, fmt="table", columns=["id", "name"])
    assert "Alice" in result
    assert "a@b.c" not in result


def test_json_format_empty_list():
    result = format_output([], fmt="json")
    assert json.loads(result) == []
