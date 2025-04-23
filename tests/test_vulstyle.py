import os
import tempfile
import shutil

from sitm_core.inference.vulstyle import VulDetector

def test_vuldetector_extracts_functions():
    code = """
    int safe_add(int a, int b) {
        return a + b;
    }
    """
    tmpdir = tempfile.mkdtemp()
    file_path = os.path.join(tmpdir, "test.c")
    with open(file_path, "w") as f:
        f.write(code)

    detector = VulDetector(model_dir = "") 
    result = detector._extract_functions(file_path)

    shutil.rmtree(tmpdir)
    assert isinstance(result, list)
    assert len(result) == 1
    assert "safe_add" in result[0][0]

def test_vuldetector_has_vulnerability_false(monkeypatch):
    code = "int main() { return 0; }"
    tmpdir = tempfile.mkdtemp()
    file_path = os.path.join(tmpdir, "main.c")
    with open(file_path, "w") as f:
        f.write(code)

    detector = VulDetector(model_dir = "")
    class DummyModel:
        def predict(self, inputs): return [0 for _ in inputs], None
    monkeypatch.setattr(detector, "_get_model", lambda: DummyModel())

    assert detector.has_vulnerability(file_path) is False
    shutil.rmtree(tmpdir)
