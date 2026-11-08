"""Windows runtime checks are explicitly skipped when the runtime is absent."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "installers/install.ps1"


def test_windows_installer_failure_and_policy_review():
    source = INSTALLER.read_text(encoding="utf-8")
    assert "Set-ExecutionPolicy" not in source
    assert "-ExecutionPolicy Bypass" in source
    assert "Resolve-Path -LiteralPath" in source
    assert "ReparsePoint" in source
    assert "$Backups.ContainsKey($target)" in source
    assert "finally {" in source
    assert "ExpandEnvironmentVariables" in source
    assert "-X utf8" in source
    assert "DisableDelayedExpansion" in source


@pytest.mark.parametrize("shell", ["powershell", "pwsh"])
@pytest.mark.parametrize("script_name", ["install.ps1", "windows-common.ps1", "setup-windows.ps1"])
def test_windows_installer_parser_when_available(shell, script_name):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} unavailable; PowerShell syntax NOT TESTED")
    # Parser only: never executes the installer or writes a user's PATH.
    script = """$tokens = $null; $errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $env:GITPUBLISH_TEST_INSTALLER, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { $errors | Out-String | Write-Output; exit 1 }
exit 0
"""
    result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", script],
        env={**os.environ, "GITPUBLISH_TEST_INSTALLER": str(ROOT / "installers" / script_name)},
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("shell", ["powershell", "pwsh"])
@pytest.mark.skipif(sys.platform != "win32", reason="CHƯA KIỂM THỬ TRÊN WINDOWS: requires Windows")
def test_windows_install_and_launch_in_temporary_directory(tmp_path, shell):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} unavailable")
    if not all(shutil.which(tool) for tool in ("git", "gh")):
        pytest.skip("Git/gh unavailable; no automatic installation")
    source = tmp_path / "source with spaces [1] tiếng Việt"
    (source / "installers").mkdir(parents=True)
    shutil.copy2(INSTALLER, source / "installers/install.ps1")
    shutil.copy2(ROOT / "installers/windows-common.ps1", source / "installers/windows-common.ps1")
    # A harmless entry point verifies argument forwarding and exit codes.
    (source / "publish.py").write_text(
        "import sys\nprint('OFFLINE:' + sys.argv[1])\nsys.exit(7)\n", encoding="utf-8")
    bindir = tmp_path / "bin with spaces"
    command = [executable, "-NoProfile", "-NonInteractive", "-File",
        str(source / "installers/install.ps1"), "-BinDir", str(bindir), "-NoPathUpdate", "-PythonPath", sys.executable]
    for _ in range(2):
        result = subprocess.run(command, capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr
    assert list(bindir.glob("publish.cmd.backup.*"))
    assert list(bindir.glob("publish-runner.ps1.backup.*"))
    assert not list(bindir.glob("*.tmp"))
    for launcher in (
        [executable, "-NoProfile", "-NonInteractive", "-File", str(bindir / "publish-runner.ps1"), "space argument"],
        [str(bindir / "publish.cmd"), "space argument"],
    ):
        result = subprocess.run(launcher, capture_output=True, timeout=30)
        assert result.returncode == 7, result.stderr
        assert b"OFFLINE:space argument" in result.stdout
