"""Matrix control flow is exercised offline, without starting containers."""

import json
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from tools import linux_matrix as matrix


def test_missing_runtime_reports_skipped_for_every_distro(tmp_path, monkeypatch):
    report = tmp_path / "matrix.json"
    monkeypatch.setattr(sys, "argv", ["matrix", "--run", "all", "--report", str(report)])
    monkeypatch.setattr(matrix.shutil, "which", lambda _: None)
    monkeypatch.setattr(matrix.subprocess, "run", lambda *a, **k: pytest.fail("Must not start runtime"))
    assert matrix.main() == 2
    results = json.loads(report.read_text(encoding="utf-8"))["results"]
    assert set(results) == set(matrix.MATRIX)
    assert {r["status"] for r in results.values()} == {"SKIPPED"}


def test_matrix_continues_after_a_failure_and_reports_all(tmp_path, monkeypatch):
    report = tmp_path / "matrix.json"
    monkeypatch.setattr(sys, "argv", ["matrix", "--run", "all", "--report", str(report)])
    monkeypatch.setattr(matrix.shutil, "which", lambda _: "/fake/docker")
    monkeypatch.setattr(matrix.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    visited = []
    def run_one(name, runtime):
        visited.append(name)
        return {"status": "FAIL" if name == "ubuntu24" else "PASS"}
    monkeypatch.setattr(matrix, "run_one", run_one)
    assert matrix.main() == 1
    assert visited == list(matrix.MATRIX)
    assert len(json.loads(report.read_text(encoding="utf-8"))["results"]) == 6


def test_runtime_permission_failure_does_not_start_containers(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["matrix", "--run", "fedora"])
    monkeypatch.setattr(matrix.shutil, "which", lambda _: "/fake/podman")
    monkeypatch.setattr(matrix.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
    monkeypatch.setattr(matrix, "run_one", lambda *a: pytest.fail("Must not run container"))
    assert matrix.main() == 2


def test_matrix_stages_regression_suite_and_documentation(tmp_path):
    matrix.create_test_source(tmp_path)
    assert (tmp_path / "tests/test_v5_core.py").is_file()
    assert (tmp_path / "tools/linux_matrix.py").is_file()
    assert (tmp_path / "installers/install.ps1").is_file()
    assert (tmp_path / "README.md").is_file()


@pytest.mark.skipif(shutil.which("sh") is None, reason="POSIX shell (sh) unavailable")
def test_container_script_is_valid_and_runs_headless_regressions():
    script = matrix.container_script("true")
    result = subprocess.run(["sh", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "python3 -B -m pytest" in script
    assert "DISPLAY WAYLAND_DISPLAY" in script
    assert '"$HOME/.local/bin/publish"' in script


def test_matrix_copy_rejects_symlinked_parent(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "publish.py").write_text("# safe", encoding="utf-8")
    external = tmp_path / "external"
    external.mkdir()
    (external / "credential.py").write_text("# synthetic excluded fixture", encoding="utf-8")
    (root / "src").mkdir()
    try:
        (root / "src/gitpublish").symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks unavailable")
    monkeypatch.setattr(matrix, "ROOT", root)
    destination = tmp_path / "stage"
    matrix.create_test_source(destination)
    assert not (destination / "src/gitpublish/credential.py").exists()


def test_matrix_staging_uses_same_private_file_policy_as_zip(tmp_path, monkeypatch):
    root = tmp_path / "source"
    package = root / "src/gitpublish"
    package.mkdir(parents=True)
    (root / "publish.py").write_text("# synthetic entry", encoding="utf-8")
    (package / "credentials.py").write_text("SYNTHETIC_PRIVATE_FIXTURE", encoding="utf-8")
    (package / "cli.py").write_text("# safe module", encoding="utf-8")
    monkeypatch.setattr(matrix, "ROOT", root)
    destination = tmp_path / "staged"
    matrix.create_test_source(destination)
    assert (destination / "src/gitpublish/cli.py").is_file()
    assert not (destination / "src/gitpublish/credentials.py").exists()
