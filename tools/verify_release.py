"""Verify a trusted local candidate ZIP/checksum, then test its extracted source."""

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_snapshot import ARCHIVE_ROOT, verify_snapshot


def verify_checksum(archive: Path, checksum: Path) -> str:
    fields = checksum.read_text(encoding="ascii").strip().split(maxsplit=1)
    if len(fields) != 2 or fields[1].lstrip("*") != archive.name:
        raise RuntimeError("Checksum không ghi đúng tên artifact.")
    digest = sha256(archive.read_bytes()).hexdigest()
    if fields[0].lower() != digest:
        raise RuntimeError("Checksum SHA-256 không khớp artifact.")
    return digest


def read_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    counts = {name: sum(int(suite.get(name, "0")) for suite in suites)
        for name in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    if not suites or counts["tests"] <= 0:
        raise RuntimeError("Không có kết quả pytest trong JUnit.")
    return counts


def verify_release(archive: Path, checksum: Path, timeout: int = 120) -> dict:
    digest = verify_checksum(archive, checksum)
    count = verify_snapshot(archive)
    report = {"artifact": archive.name, "sha256": digest, "source_files": count,
        "checksum": "PASS", "manifest": "PASS", "runtime": sys.version.split()[0]}
    with tempfile.TemporaryDirectory(prefix="gitpublish-release-qa-") as temporary:
        temporary = Path(temporary)
        with ZipFile(archive) as zipped:
            zipped.extractall(temporary / "source")
        source = temporary / "source" / ARCHIVE_ROOT
        python_files = list(source.rglob("*.py"))
        for path in python_files:
            text = path.read_text(encoding="utf-8")
            ast.parse(text, filename=str(path), feature_version=(3, 10))
            compile(text, str(path), "exec", dont_inherit=True)
        report["python_syntax"] = {"status": "PASS", "files": len(python_files), "grammar": "3.10"}
        env = os.environ.copy()
        for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
            env.pop(key, None)
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
            GH_CONFIG_DIR=str(temporary / "gh-config"), GH_PROMPT_DISABLED="1")
        junit = temporary / "pytest.xml"
        command = [sys.executable, "-B", "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider",
            f"--junitxml={junit}"]
        try:
            result = subprocess.run(command, cwd=source, env=env, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return {**report, "status": "FAIL", "reason": "Extracted pytest timed out"}
        report.update(returncode=result.returncode, output=result.stdout + result.stderr)
        if not junit.is_file():
            return {**report, "status": "FAIL", "reason": "Missing JUnit result"}
        report["pytest"] = read_junit(junit)
        report["status"] = "PASS" if result.returncode == 0 and not (
            report["pytest"]["failures"] or report["pytest"]["errors"]
        ) and report["pytest"]["passed"] > 0 else "FAIL"
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--checksum", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.report and args.report.exists():
        parser.error("Report already exists; use a new report path")
    try:
        report = verify_release(args.archive, args.checksum)
    except (OSError, RuntimeError, ValueError, SyntaxError, ET.ParseError, BadZipFile) as exc:
        report = {"status": "FAIL", "error": str(exc)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key != "output"},
        ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
