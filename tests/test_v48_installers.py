"""Offline installer tests for Git Publish V4.8."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
LINUX_INSTALLER = ROOT / "installers" / "install.sh"
MAC_INSTALLER = ROOT / "installers" / "install-macos.sh"


def run_installer(home: Path):
    """Install into a temporary HOME, never the real HOME."""
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["GH_CONFIG_DIR"] = str(home / ".config" / "gh")
    env["GH_PROMPT_DISABLED"] = "1"

    return subprocess.run(
        ["bash", str(LINUX_INSTALLER)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_installer_syntax():
    """Both installer scripts must have valid Bash syntax."""
    for script in (LINUX_INSTALLER, MAC_INSTALLER):
        assert script.is_file(), f"Missing: {script}"

        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr


def test_new_installation(tmp_path):
    """The installer must create an executable launcher."""
    home = tmp_path / "home"
    home.mkdir()

    result = run_installer(home)

    assert result.returncode == 0, result.stdout + result.stderr

    launcher = home / ".local" / "bin" / "publish"

    assert launcher.is_file()
    assert os.access(launcher, os.X_OK)

    content = launcher.read_text(encoding="utf-8")
    assert str(ROOT / "publish.py") in content


def test_existing_launcher_is_backed_up(tmp_path):
    """The installer must preserve the previous launcher."""
    home = tmp_path / "home"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)

    launcher = bin_dir / "publish"
    launcher.write_text(
        "#!/bin/sh\necho old-publish\n",
        encoding="utf-8",
    )

    result = run_installer(home)

    assert result.returncode == 0, result.stdout + result.stderr

    backups = list(bin_dir.glob("publish.backup.*"))

    assert len(backups) == 1
    assert "old-publish" in backups[0].read_text(
        encoding="utf-8"
    )

    assert "old-publish" not in launcher.read_text(
        encoding="utf-8"
    )


@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="Only applicable to non-macOS systems",
)
def test_macos_installer_rejects_linux():
    """macOS entry point must reject other operating systems."""
    result = subprocess.run(
        ["bash", str(MAC_INSTALLER)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode != 0
    assert "macOS" in result.stdout + result.stderr
