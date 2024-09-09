import os

import py

from src.main import _assign, _recompute

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_e2e(tmpdir: py.path.local) -> None:
    # Happy test that this works
    output_file_path = _assign(
        os.path.join(TEST_DATA_DIR, "mock_scores.csv"), auto_yes_prompt=True, data_dir=TEST_DATA_DIR, output_dir=tmpdir
    )
    _recompute(output_file_path, os.path.join(TEST_DATA_DIR, "mock_scores.csv"), auto_yes_prompt=True)
