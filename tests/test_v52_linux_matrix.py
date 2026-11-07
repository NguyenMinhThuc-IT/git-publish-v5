"""Tests for V5.2 Linux container test runner."""

import subprocess
import sys
from pathlib import Path

from tools.linux_matrix import MATRIX, create_test_source


ROOT = Path(__file__).resolve().parents[1]


def test_linux_matrix_contains_target_distros():
    expected = {
        "ubuntu24",
        "ubuntu26",
        "debian",
        "fedora",
        "arch",
        "kali",
    }
    assert expected.issubset(MATRIX)


def test_staged_source_excludes_git_and_secrets(tmp_path):
    destination = tmp_path / "source"
    destination.mkdir()

    create_test_source(destination)

    assert (destination / "publish.py").is_file()
    assert (destination / "installers/install.sh").is_file()

    assert not (destination / ".git").exists()
    assert not (destination / ".env").exists()
    assert not (destination / "src/gitpublish/__pycache__").exists()


def test_matrix_list_without_docker():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/linux_matrix.py"),
            "--list",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "ubuntu24" in result.stdout
    assert "fedora" in result.stdout
    assert "arch" in result.stdout
    assert "kali" in result.stdout
