"""Packaging tests use synthetic source trees, never account credentials."""

import json
import stat
from pathlib import PurePosixPath
from zipfile import ZipFile, ZipInfo

import pytest

from tools import build_snapshot as packaging


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    (root / "src/gitpublish").mkdir(parents=True)
    (root / "publish.py").write_text("# synthetic entry", encoding="utf-8")
    (root / "README.md").write_text("# synthetic readme", encoding="utf-8")
    (root / "src/gitpublish/config.py").write_text("# synthetic config", encoding="utf-8")
    return root


@pytest.mark.parametrize("name", [
    ".env", ".env.production", ".git/config", ".aws/credentials",
    "src/gitpublish/credentials.py", "tools/token.py", "docs/secrets.md",
    "src/gitpublish/__pycache__/config.pyc", "tests/.pytest_cache/nodeids",
    "installers/install.sh.bak-v47", "src/gitpublish/server.pem",
    "docs/../README.md", "/etc/passwd", "tools/../publish.py",
    "src/gitpublish/.config/private.py", "tests/test_bad\nname.py",
    "tools/CON.py", "tools/private:stream.py", "tools/file?.py",
])
def test_archive_policy_rejects_private_or_unexpected_paths(name):
    assert not packaging.allowed_relative(PurePosixPath(name))


def test_zip_excludes_synthetic_secrets_cache_and_symlinks(source, tmp_path):
    for name in (".env", ".aws/credentials", "src/gitpublish/credentials.py",
        "src/gitpublish/__pycache__/cache.pyc", "installers/install.sh.bak-v47"):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("SYNTHETIC_PRIVATE_MARKER", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "test_private.py").write_text("SYNTHETIC_PRIVATE_MARKER", encoding="utf-8")
    try:
        (source / "tests").symlink_to(outside, target_is_directory=True)
        (source / "src/gitpublish/link.py").symlink_to(outside / "test_private.py")
    except OSError:
        pytest.skip("Symlinks unavailable")
    output, digest, count = packaging.build_snapshot(source, tmp_path / "source.zip")
    assert len(digest) == 64
    assert count == packaging.verify_snapshot(output) == 3
    with ZipFile(output) as archive:
        assert all(b"SYNTHETIC_PRIVATE_MARKER" not in archive.read(name) for name in archive.namelist())
        assert len(archive.namelist()) == 4


def test_zip_does_not_overwrite_existing_artifact(source, tmp_path):
    output = tmp_path / "keep.zip"
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        packaging.build_snapshot(source, output)
    assert output.read_bytes() == b"keep"


@pytest.mark.parametrize("attack", ["traversal", "symlink", "manifest", "missing-manifest"])
def test_zip_verifier_rejects_tampering(source, tmp_path, attack):
    good, _, _ = packaging.build_snapshot(source, tmp_path / "good.zip")
    bad = tmp_path / "bad.zip"
    with ZipFile(good) as original, ZipFile(bad, "w") as archive:
        for info in original.infolist():
            if attack == "missing-manifest" and info.filename.endswith(packaging.MANIFEST):
                continue
            data = original.read(info)
            if attack == "manifest" and info.filename.endswith(packaging.MANIFEST):
                data = json.dumps({}).encode()
            archive.writestr(info, data)
        if attack == "traversal":
            archive.writestr(f"{packaging.ARCHIVE_ROOT}/../private", b"synthetic")
        if attack == "symlink":
            info = ZipInfo(f"{packaging.ARCHIVE_ROOT}/tools/link.py")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, b"/outside")
    with pytest.raises(RuntimeError):
        packaging.verify_snapshot(bad)


def test_actual_source_roundtrip_has_matching_manifest(tmp_path):
    output, _, count = packaging.build_snapshot(output=tmp_path / "source.zip")
    assert count > 30
    with ZipFile(output) as archive:
        archive.extractall(tmp_path / "unpacked")
        manifest = json.loads(archive.read(f"{packaging.ARCHIVE_ROOT}/{packaging.MANIFEST}"))
    extracted = tmp_path / "unpacked" / packaging.ARCHIVE_ROOT
    for name, expected in manifest.items():
        assert packaging.sha256((extracted / name).read_bytes()).hexdigest() == expected
    assert not (extracted / ".git").exists()
    for name in ("setup.cmd", "installers/install.ps1", "installers/windows-common.ps1", "installers/setup-windows.ps1"):
        assert (extracted / name).is_file()


@pytest.mark.parametrize("content", [
    "ghp_" + "a" * 36,
    "github_pat_" + "a" * 82,
    "AKIA" + "A" * 16,
    "-----BEGIN " + "PRIVATE KEY-----",
])
def test_content_audit_blocks_synthetic_credentials_without_reporting_values(source, tmp_path, content):
    private = source / "src/gitpublish/config.py"
    private.write_text("# fixture\n" + content, encoding="utf-8")
    findings = packaging.audit_source_files(packaging.collect_source_files(source), source)
    assert len(findings) == 1
    assert findings[0]["path"] == "src/gitpublish/config.py"
    assert findings[0]["line"] == 2
    assert content not in json.dumps(findings)
    output = tmp_path / "blocked.zip"
    with pytest.raises(RuntimeError, match="xác thực") as caught:
        packaging.build_snapshot(source, output)
    assert content not in str(caught.value)
    assert not output.exists()
