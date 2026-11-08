"""Run Git Publish installer smoke tests in Linux containers."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_snapshot import audit_source_files, collect_source_files

APT = (
    "apt-get update -qq && "
    "DEBIAN_FRONTEND=noninteractive "
    "apt-get install -y python3 python3-pytest git gh bash"
)

MATRIX = {
    "ubuntu24": ("ubuntu:24.04", APT),
    "ubuntu26": ("ubuntu:26.04", APT),
    "debian": ("debian:stable-slim", APT),
    "fedora": (
        "fedora:latest",
        "dnf install -y python3 python3-pytest git gh bash",
    ),
    "arch": (
        "archlinux:latest",
        "pacman -Syu --noconfirm --needed "
        "python python-pytest git github-cli bash",
    ),
    "kali": ("kalilinux/kali-rolling", APT),
}


def create_test_source(destination: Path) -> None:
    """Copy only required source files, without .git or secrets."""
    files = collect_source_files(ROOT)
    if audit_source_files(files, ROOT):
        raise RuntimeError("Source có mẫu thông tin xác thực; không đưa vào container.")
    for source in files:
        relative = source.relative_to(ROOT)
        target = destination / relative

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    if not (destination / "publish.py").exists():
        raise RuntimeError("Missing publish.py in test source.")


def container_script(package_command: str) -> str:
    return f"""set -eu
{package_command}

export HOME=/tmp/git-publish-v52-home
export GH_CONFIG_DIR="$HOME/.config/gh"
export GH_PROMPT_DISABLED=1
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN DISPLAY WAYLAND_DISPLAY

mkdir -p "$HOME"

bash -n /workspace/installers/install.sh
bash /workspace/installers/install.sh

test -x "$HOME/.local/bin/publish"

python3 - <<'CHECKPY'
import sys
sys.path.insert(0, "/workspace")

from src.gitpublish.config import APP_VERSION
from src.gitpublish.cli import run
from src.gitpublish.git import prepare_remote_for_push
from src.gitpublish.security import scan_project

assert APP_VERSION == "5.0.1"
print(sys.version)
print("Python imports: OK")
CHECKPY

cd /workspace
python3 -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/gitpublish-pytest

# Run the real launcher without credentials; failure must occur before Git writes.
cd /tmp
set +e
"$HOME/.local/bin/publish" </dev/null > /tmp/launcher-output 2>&1
launcher_status=$?
set -e
test "$launcher_status" -eq 1
grep -q 'Git Publish v5.0.1' /tmp/launcher-output
grep -q 'gh auth login' /tmp/launcher-output

git --version
gh --version | head -n 1

echo "INSTALLER SMOKE TEST PASSED"
"""


def run_one(name: str, runtime: str) -> dict:
    image, install = MATRIX[name]

    with tempfile.TemporaryDirectory(
        prefix="gitpublish-v52-"
    ) as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        create_test_source(source)

        command = [
            runtime,
            "run",
            "--rm",
            "--security-opt=no-new-privileges",
            "--mount",
            f"type=bind,source={source},"
            "target=/workspace,readonly",
            "--workdir",
            "/tmp",
            "--env",
            "GH_PROMPT_DISABLED=1",
            image,
            "/bin/sh",
            "-c",
            container_script(install),
        ]

        print(f"\n===== TEST {name}: {image} =====", flush=True)

        try:
            result = subprocess.run(
                command,
                check=False,
                timeout=900,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"FAIL: {exc}")
            return {"status": "FAIL", "image": image, "reason": type(exc).__name__}

        output = result.stdout + result.stderr
        print(output, end="", flush=True)

        if result.returncode:
            print(f"FAIL: {name} (exit {result.returncode})")
            return {"status": "FAIL", "image": image, "returncode": result.returncode, "output": output}

        digest = None
        try:
            inspected = subprocess.run(
                [runtime, "image", "inspect", "--format", "{{.Id}}", image],
                capture_output=True, text=True, timeout=30, check=False,
            )
            if inspected.returncode == 0:
                digest = inspected.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        print(f"PASS: {name}")
        return {"status": "PASS", "image": image, "image_id": digest, "returncode": 0, "output": output}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Git Publish Linux portability checks"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list",
        action="store_true",
        help="List supported test environments",
    )
    group.add_argument(
        "--run",
        choices=[*MATRIX, "all"],
        help="Run tests using Docker or Podman",
    )

    parser.add_argument(
        "--runtime",
        choices=["docker", "podman"],
        help="Container runtime to use",
    )
    parser.add_argument("--report", type=Path, help="Write per-distro results to JSON")

    args = parser.parse_args()

    if args.list:
        if args.report:
            parser.error("--report requires --run")
        for name, (image, _) in MATRIX.items():
            print(f"{name:10} {image}")
        return 0

    runtime = args.runtime

    if runtime is None:
        runtime = next(
            (
                candidate
                for candidate in ("docker", "podman")
                if shutil.which(candidate)
            ),
            None,
        )

    selected = (
        list(MATRIX) if args.run == "all" else [args.run]
    )
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": runtime,
        "results": {},
    }

    def finish(code: int) -> int:
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return code

    reason = None
    if runtime is None or not shutil.which(runtime):
        reason = "Docker/Podman unavailable; container NOT TESTED"
    else:
        try:
            info = subprocess.run([runtime, "info"], capture_output=True, text=True, timeout=30, check=False)
            if info.returncode:
                reason = "Container runtime inaccessible; container NOT TESTED"
        except (OSError, subprocess.TimeoutExpired):
            reason = "Container runtime info failed; container NOT TESTED"
    if reason:
        print(reason)
        report["results"] = {
            name: {"status": "SKIPPED", "image": MATRIX[name][0], "reason": reason}
            for name in selected
        }
        return finish(2)

    for name in selected:
        report["results"][name] = run_one(name, runtime)

    if any(result["status"] != "PASS" for result in report["results"].values()):
        return finish(1)

    print("\nAll selected Linux smoke tests passed.")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
