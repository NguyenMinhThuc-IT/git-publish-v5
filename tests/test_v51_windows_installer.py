"""Offline structural checks for the Windows installer."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "installers" / "install.ps1"


def read_installer():
    assert INSTALLER.is_file()
    return INSTALLER.read_text(encoding="utf-8")


def test_installer_is_not_empty():
    source = read_installer()

    assert len(source) > 1000
    assert "publish.py" in source


def test_installer_checks_dependencies():
    source = read_installer()

    assert '"git", "gh"' in source
    assert '"py", "python3", "python"' in source
    assert "3, 10" in source


def test_installer_uses_user_scope_and_backups():
    source = read_installer()

    assert "publish.cmd" in source
    assert "publish.ps1" in source
    assert 'Join-Path $HOME' in source
    assert "Copy-Item" in source
    assert '"User"' in source
