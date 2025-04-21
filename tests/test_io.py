import tempfile
import pytest

from sitm.utils.io import (
    is_text_file,
    get_all_text_files,
    read_file_lines,
    read_source_code
)

@pytest.fixture
def temp_text_file():
    with tempfile.NamedTemporaryFile(mode = "w", delete = False) as f:
        f.write("This is a test.\nAnother line.")
        return f.name

@pytest.fixture
def temp_binary_file():
    with tempfile.NamedTemporaryFile(mode = "wb", delete = False) as f:
        f.write(b"\x00\x01\x02\x03")
        return f.name

def test_is_text_file_true(temp_text_file):
    assert is_text_file(temp_text_file) is True

def test_is_text_file_false(temp_binary_file):
    assert is_text_file(temp_binary_file) is False

def test_get_all_text_files_single_file(temp_text_file):
    result = get_all_text_files(temp_text_file)
    assert temp_text_file in result

def test_read_file_lines(temp_text_file):
    lines = read_file_lines(temp_text_file)
    assert isinstance(lines, list)
    assert lines[0].startswith("This is a test")

def test_read_source_code(temp_text_file):
    content = read_source_code(temp_text_file)
    assert "Another line" in content
