"""Verify release gate failures with fixtures; no nested suite/container execution."""

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import build_snapshot as packaging
from tools import verify_release as verification


@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / "source"
    (root / "src/gitpublish").mkdir(parents=True)
    for name in ("publish.py", "README.md", "src/gitpublish/config.py"):
        (root / name).write_text("# synthetic fixture\n", encoding="utf-8")
    archive, digest, _ = packaging.build_snapshot(root, tmp_path / "candidate.zip")
    checksum = tmp_path / "candidate.zip.sha256"
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return archive, checksum


def test_release_checksum_detects_modified_archive_before_running_code(candidate, monkeypatch):
    archive, checksum = candidate
    archive.write_bytes(archive.read_bytes() + b"tampered")
    monkeypatch.setattr(verification.subprocess, "run", lambda *a, **k: pytest.fail("Must not execute tampered source"))
    with pytest.raises(RuntimeError, match="SHA-256"):
        verification.verify_release(archive, checksum)


def test_checksum_requires_matching_filename(candidate):
    archive, checksum = candidate
    checksum.write_text(sha256(archive.read_bytes()).hexdigest() + "  other.zip\n", encoding="ascii")
    with pytest.raises(RuntimeError, match="tên"):
        verification.verify_checksum(archive, checksum)


def test_junit_counts_pass_fail_skip_and_errors(tmp_path):
    junit = tmp_path / "tests.xml"
    junit.write_text('<testsuites><testsuite tests="7" failures="1" errors="1" skipped="2"/></testsuites>', encoding="utf-8")
    assert verification.read_junit(junit) == {"tests": 7, "failures": 1, "errors": 1, "skipped": 2, "passed": 3}


def test_empty_test_run_cannot_pass_gate(tmp_path):
    junit = tmp_path / "tests.xml"
    junit.write_text('<testsuites><testsuite tests="0"/></testsuites>', encoding="utf-8")
    with pytest.raises(RuntimeError, match="JUnit"):
        verification.read_junit(junit)


@pytest.mark.parametrize("returncode,failures,skipped,expected", [
    (0, 0, 1, "PASS"), (1, 1, 1, "FAIL"), (0, 1, 1, "FAIL"), (0, 0, 2, "FAIL"),
])
def test_extracted_suite_result_is_not_misreported(candidate, monkeypatch, returncode, failures, skipped, expected):
    def run(command, **kwargs):
        assert kwargs["env"].get("GH_TOKEN") is None
        assert kwargs["env"]["GIT_CONFIG_GLOBAL"] == verification.os.devnull
        assert str(kwargs["cwd"]).endswith(packaging.ARCHIVE_ROOT)
        junit = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml=")))
        junit.write_text(f'<testsuites><testsuite tests="2" failures="{failures}" errors="0" skipped="{skipped}"/></testsuites>', encoding="utf-8")
        return SimpleNamespace(returncode=returncode, stdout="synthetic output", stderr="")
    monkeypatch.setenv("GH_TOKEN", "SYNTHETIC_ENV_ONLY")
    monkeypatch.setattr(verification.subprocess, "run", run)
    report = verification.verify_release(*candidate)
    assert report["status"] == expected
    assert report["checksum"] == report["manifest"] == "PASS"


def test_missing_junit_is_a_failed_gate(candidate, monkeypatch):
    monkeypatch.setattr(verification.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="synthetic", stderr=""))
    report = verification.verify_release(*candidate)
    assert report["status"] == "FAIL"
    assert report["reason"] == "Missing JUnit result"


def test_extracted_suite_timeout_is_a_failed_gate(candidate, monkeypatch):
    def timeout(*args, **kwargs):
        raise verification.subprocess.TimeoutExpired("synthetic", 1)
    monkeypatch.setattr(verification.subprocess, "run", timeout)
    report = verification.verify_release(*candidate, timeout=1)
    assert report["status"] == "FAIL"
    assert report["reason"] == "Extracted pytest timed out"
