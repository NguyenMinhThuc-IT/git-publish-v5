"""Real Bash on Linux with synthetic dependencies; OS clipboard mocks only."""

import io
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.gitpublish import cli, clipboard


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("platform,display,wayland,expected", [
    ("darwin", ":1", "wayland-0", "pbcopy"),
    ("win32", ":1", "wayland-0", "clip"),
    ("linux", "", "wayland-0", "wl-copy"),
    ("linux", ":1", "", "xclip"),
])
def test_platform_clipboard_preserves_unicode(monkeypatch, platform, display, wayland, expected):
    monkeypatch.setattr(clipboard.sys, "platform", platform)
    monkeypatch.setenv("DISPLAY", display)
    monkeypatch.setenv("WAYLAND_DISPLAY", wayland)
    monkeypatch.setattr(clipboard.shutil, "which", lambda cmd: "/fake/" + cmd)
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(clipboard.subprocess, "run", run)
    value = "https://example.invalid/dự án"
    assert clipboard.copy_to_clipboard(value)
    assert calls[0][0][0] == expected
    encoding = "utf-16le" if expected == "clip" else "utf-8"
    assert calls[0][1]["input"].decode(encoding) == value


def test_headless_does_not_call_graphical_clipboard(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(clipboard.subprocess, "run", lambda *a, **k: pytest.fail("Headless clipboard called"))
    assert clipboard.copy_to_clipboard("synthetic URL") is False


@pytest.mark.parametrize("failure", ["timeout", "missing", "nonzero"])
def test_x11_clipboard_falls_back_after_failure(monkeypatch, failure):
    monkeypatch.setattr(clipboard.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(clipboard.shutil, "which", lambda cmd: "/fake/" + cmd)
    calls = []
    def run(command, **kwargs):
        calls.append(command[0])
        if command[0] == "xclip":
            if failure == "timeout":
                raise subprocess.TimeoutExpired(command, 5)
            if failure == "missing":
                raise FileNotFoundError()
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(clipboard.subprocess, "run", run)
    assert clipboard.copy_to_clipboard("synthetic URL")
    assert calls == ["xclip", "xsel"]


def test_ascii_console_does_not_crash(monkeypatch):
    buffer = io.BytesIO()
    console = io.TextIOWrapper(buffer, encoding="ascii")
    monkeypatch.setattr(cli.sys, "stdout", console)
    def main():
        print("Tiếng Việt 🚀")
        return 0
    monkeypatch.setattr(cli, "main", main)
    with pytest.raises(SystemExit) as caught:
        cli.run()
    console.flush()
    assert caught.value.code == 0
    assert b"Ti" in buffer.getvalue()


@pytest.fixture
def installer_fixture(tmp_path):
    if shutil.which("bash") is None:
        pytest.skip("Bash unavailable")
    source = tmp_path / "nguồn [1] có khoảng trắng"
    (source / "installers").mkdir(parents=True)
    for name in ("install.sh", "install-macos.sh"):
        shutil.copy2(ROOT / "installers" / name, source / "installers" / name)
    (source / "publish.py").write_text(
        "import sys\nprint('OFFLINE:' + sys.argv[1])\nsys.exit(7)\n", encoding="utf-8")
    test_home = tmp_path / "home có dấu cách"
    test_home.mkdir()
    commands = tmp_path / "commands"
    commands.mkdir()
    for name, script in {"gh": "exit 1", "uname": "echo Linux"}.items():
        target = commands / name
        target.write_text("#!/bin/sh\n" + script + "\n", encoding="utf-8")
        target.chmod(0o755)
    env = {**os.environ, "HOME": str(test_home), "PATH": str(commands) + os.pathsep + os.environ["PATH"],
        "GH_CONFIG_DIR": str(test_home / ".config/gh")}
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
        env.pop(key, None)
    return source, test_home, commands, env


def run_installer(fixture, script="install.sh"):
    source, _, _, env = fixture
    return subprocess.run([shutil.which("bash"), str(source / "installers" / script)],
        env=env, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("platform", ["Linux", "Darwin"])
def test_installer_launches_unicode_path_and_preserves_arguments(installer_fixture, platform):
    source, test_home, commands, env = installer_fixture
    (commands / "uname").write_text(f"#!/bin/sh\necho {platform}\n", encoding="utf-8")
    result = run_installer(installer_fixture, "install-macos.sh" if platform == "Darwin" else "install.sh")
    assert result.returncode == 0, result.stdout + result.stderr
    launcher = test_home / ".local/bin/publish"
    result = subprocess.run([str(launcher), "đối số có khoảng trắng"],
        env=env, capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 7, result.stderr
    assert "OFFLINE:đối số có khoảng trắng" in result.stdout
    assert str(source / "publish.py") not in result.stderr


def test_installer_does_not_overwrite_directory(installer_fixture):
    _, test_home, _, _ = installer_fixture
    target = test_home / ".local/bin/publish"
    target.mkdir(parents=True)
    marker = target / "keep"
    marker.write_text("keep", encoding="utf-8")
    result = run_installer(installer_fixture)
    assert result.returncode != 0
    assert marker.read_text(encoding="utf-8") == "keep"
    assert list(target.iterdir()) == [marker]


def test_installer_dependency_failure_preserves_existing_launcher(installer_fixture):
    _, test_home, commands, _ = installer_fixture
    target = test_home / ".local/bin/publish"
    target.parent.mkdir(parents=True)
    target.write_text("old launcher", encoding="utf-8")
    python = commands / "python3"
    python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    python.chmod(0o755)
    result = run_installer(installer_fixture)
    assert result.returncode != 0
    assert target.read_text(encoding="utf-8") == "old launcher"
    assert not list(target.parent.glob("publish.backup.*"))


def test_installer_backup_failure_preserves_existing_launcher(installer_fixture):
    _, test_home, commands, _ = installer_fixture
    target = test_home / ".local/bin/publish"
    target.parent.mkdir(parents=True)
    target.write_text("old launcher", encoding="utf-8")
    copy = commands / "cp"
    copy.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    copy.chmod(0o755)
    assert run_installer(installer_fixture).returncode != 0
    assert target.read_text(encoding="utf-8") == "old launcher"


@pytest.mark.skipif(shutil.which("zsh") is None, reason="Zsh unavailable; syntax NOT TESTED")
def test_documented_path_command_has_valid_zsh_syntax():
    result = subprocess.run([shutil.which("zsh"), "-n", "-c", 'export PATH="$HOME/.local/bin:$PATH"'],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
