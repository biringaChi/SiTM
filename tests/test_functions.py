import os
import tempfile
from sitm_core.utils.functions import is_c_type_file, get_all_c_files, generate_dummy_header

def test_is_c_type_file():
    assert is_c_type_file("main.c")
    assert is_c_type_file("header.hpp")
    assert is_c_type_file("module.cxx")
    assert not is_c_type_file("script.py")
    assert not is_c_type_file("readme.txt")

def test_get_all_c_files_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, "a.c")
        file2 = os.path.join(tmpdir, "b.py")
        with open(file1, "w") as f: f.write("int main() {}")
        with open(file2, "w") as f: f.write("print('hi')")
        files = get_all_c_files(tmpdir)
        assert file1 in files
        assert file2 not in files

def test_generate_dummy_header_combined():
    cpp_symbols = {"MyClass", "ns::Thing", "uint8_t"}
    cpp_result = generate_dummy_header(cpp_symbols, is_c=False)
    assert "class MyClass" in cpp_result
    assert "namespace ns" in cpp_result
    assert "typedef int uint8_t;" in cpp_result
    assert "#define REGISTER_STATE_CHECK(x) x" in cpp_result

    c_symbols = {"size_t", "unknown_type"}
    c_result = generate_dummy_header(c_symbols, is_c=True)
    assert "typedef int size_t;" in c_result
    assert "typedef int unknown_type;" in c_result
    assert "#define REGISTER_STATE_CHECK" not in c_result