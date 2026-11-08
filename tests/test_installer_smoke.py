"""Run the native installer and launchers with a harmless temporary entry point."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_native_installer_and_launchers(tmp_path):
    for tool in ("git", "gh"):
        assert shutil.which(tool), f"Required installer dependency unavailable: {tool}"

    source = tmp_path / "source with spaces tiếng Việt"
    installers = source / "installers"
    installers.mkdir(parents=True)
    for name in ("install.sh", "install-macos.sh", "install.ps1", "windows-common.ps1"):
        shutil.copy2(ROOT / "installers" / name, installers / name)

    # Only this probe is executed by the real generated launchers.
    (source / "publish.py").write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['GITPUBLISH_SMOKE_RESULT']).write_text(\n"
        "    json.dumps(sys.argv[1:], ensure_ascii=False), encoding='utf-8')\n"
        "print('INSTALLER_SMOKE_OK')\n"
        "sys.exit(7)\n",
        encoding="utf-8",
    )

    home = tmp_path / "home with spaces tiếng Việt"
    home.mkdir()
    bindir = home / ".local" / "bin"
    output = tmp_path / "launcher-result.json"
    env = os.environ.copy()
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
        env.pop(key, None)
    env.update({
        "HOME": str(home),
        "USERPROFILE": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GH_CONFIG_DIR": str(home / ".config" / "gh"),
        "GH_PROMPT_DISABLED": "1",
        "GITPUBLISH_SMOKE_RESULT": str(output),
    })

    if sys.platform == "win32":
        shell = shutil.which("powershell")
        assert shell, "Windows PowerShell unavailable"
        command = [shell, "-NoProfile", "-NonInteractive", "-File",
                   str(installers / "install.ps1"), "-BinDir", str(bindir), "-NoPathUpdate", "-PythonPath", sys.executable]
        launchers = [
            [shell, "-NoProfile", "-NonInteractive", "-File", str(bindir / "publish-runner.ps1")],
            [str(bindir / "publish.cmd")],
        ]
        expected_files = [bindir / "publish-runner.ps1", bindir / "publish.cmd"]
    else:
        assert sys.platform in ("linux", "darwin"), "Requires Linux, macOS or Windows"
        shell = shutil.which("bash")
        assert shell, "Bash unavailable"
        script = "install-macos.sh" if sys.platform == "darwin" else "install.sh"
        command = [shell, str(installers / script)]
        launchers = [[str(bindir / "publish")]]
        expected_files = [bindir / "publish"]

    result = subprocess.run(command, cwd=source, env=env, input="", capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    for launcher in expected_files:
        assert launcher.is_file(), f"Launcher missing: {launcher}"
        if sys.platform != "win32":
            assert os.access(launcher, os.X_OK), f"Launcher is not executable: {launcher}"

    arguments = ["đối số có khoảng trắng", "second argument"]
    for launcher in launchers:
        output.unlink(missing_ok=True)
        result = subprocess.run(launcher + arguments, cwd=home, env=env, input="",
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=30)
        assert result.returncode == 7, result.stdout + result.stderr
        assert "INSTALLER_SMOKE_OK" in result.stdout, result.stdout + result.stderr
        assert json.loads(output.read_text(encoding="utf-8")) == arguments
