import pytest
import json
from AI.llm.llm_interface import _parse_json

def test_parse_json_valid():
    raw = '```json\n{"name": "test"}\n```'
    parsed = _parse_json(raw, {})
    assert parsed == {"name": "test"}

def test_parse_json_no_fences():
    raw = '{"name": "test"}'
    parsed = _parse_json(raw, {})
    assert parsed == {"name": "test"}

def test_parse_json_with_preamble():
    raw = 'Here is the JSON:\n{"name": "test"}\nHope this helps!'
    parsed = _parse_json(raw, {})
    assert parsed == {"name": "test"}

def test_parse_json_fallback():
    raw = 'This is completely invalid.'
    parsed = _parse_json(raw, {"fallback": True})
    assert parsed == {"fallback": True}
    
def test_parse_json_list():
    raw = 'Some text\n[\n{"test": 1}\n]\nend'
    parsed = _parse_json(raw, [])
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["test"] == 1
