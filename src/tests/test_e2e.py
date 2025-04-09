import os

import py
import pytest

from src.main import _assign, _recompute

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.parametrize("use_flex_role_for_speed", [True, False])
def test_e2e(tmpdir: py.path.local, use_flex_role_for_speed: bool) -> None:
    # Happy test that this works
    output_file_path = _assign(
        os.path.join(TEST_DATA_DIR, "mock_scores.csv"),
        auto_yes_prompt=True,
        data_dir=TEST_DATA_DIR,
        output_dir=tmpdir,
        use_flex_role_for_speed=use_flex_role_for_speed,
    )
    assert os.path.exists(output_file_path)
    _recompute(output_file_path, os.path.join(TEST_DATA_DIR, "mock_scores.csv"), auto_yes_prompt=True)
    assert os.path.exists(output_file_path)
