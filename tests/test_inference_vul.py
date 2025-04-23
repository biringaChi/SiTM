import os
import tempfile
import shutil
import numpy as np

import pytest

from sitm_core.inference.dance import InferenceVul
from sitm_core.utils.config import config

@pytest.fixture(scope="module")
def setup_detector():
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.txt")
    lines = [
        "", 
        "username = 'admin'",
        "password = 'secret123'",
        "api_key = 'abcdef'",
    ]
    with open(test_file, "w") as f:
        f.write("\n".join(lines))
    detector = InferenceVul(model_path = str(config.dance_model_path))
    yield detector, test_file
    shutil.rmtree(temp_dir)

def test_preprocess_file_lines(setup_detector):
    detector, test_file = setup_detector
    raw, non_empty = detector.preprocess_file_lines(test_file)
    assert len(raw) == 4
    assert len(non_empty) == 3
    assert "password" in non_empty[1]

def test_get_embeddings(setup_detector):
    detector, test_file = setup_detector
    _, non_empty = detector.preprocess_file_lines(test_file)
    embeddings = detector.get_embeddings(non_empty)
    assert isinstance(embeddings, list)
    assert all(isinstance(x, np.ndarray) for x in embeddings)

def test_run_inference(setup_detector):
    detector, test_file = setup_detector
    raw, non_empty = detector.preprocess_file_lines(test_file)
    embeddings = detector.get_embeddings(non_empty)
    result = detector.run_inference(embeddings, raw)
    assert isinstance(result, dict)
    assert len(result) == 4
    assert "Line 2" in result
    assert "credential_type" in result["Line 2"]

def test_has_credentials(setup_detector):
    detector, test_file = setup_detector
    assert detector.has_credentials(test_file)
