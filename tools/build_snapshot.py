"""Build and verify an allowlisted local source ZIP, without Git history."""

import argparse
import json
import os
import re
import stat
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.gitpublish.config import APP_VERSION

ARCHIVE_ROOT = f"git-publish-{APP_VERSION}"
MANIFEST = "SOURCE_MANIFEST.json"
ROOT_FILES = {"publish.py", "README.md", "CHANGELOG.md", "LICENSE", "requirements.txt", ".gitignore", "setup.cmd"}
INSTALLERS = {"install.sh", "install-macos.sh", "install.ps1", "windows-common.ps1", "setup-windows.ps1"}
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv", "env",
    "node_modules", ".mypy_cache", ".aws", ".ssh", ".gnupg", ".config",
    ".agents", ".codex",
}
SENSITIVE_NAMES = {
    "credentials", "secrets", "secret", "token", "password", "id_rsa", "id_ed25519",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt"}
CONTENT_RULES = {
    "private-key-header": re.compile(rb"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    "github-fine-grained-token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{60,255}\b"),
    "aws-access-key-id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def audit_source_bytes(data: bytes, relative: str) -> list[dict]:
    """Report locations/rule IDs only; never expose matched credential values."""
    return [
        {"path": relative, "line": data.count(b"\n", 0, match.start()) + 1, "rule": rule}
        for rule, pattern in CONTENT_RULES.items() for match in pattern.finditer(data)
    ]


def audit_source_files(files: list[Path], root: Path = ROOT) -> list[dict]:
    return [finding for path in files
        for finding in audit_source_bytes(path.read_bytes(), path.relative_to(root).as_posix())]


def allowed_relative(relative: PurePosixPath) -> bool:
    """Accept source/documentation paths; this is not a content secret scanner."""
    if relative.is_absolute() or any(part in {".", ".."} for part in relative.parts):
        return False
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if any(any(c in part for c in '\\<>:"|?*') or any(ord(c) < 32 for c in part)
        or part.endswith((" ", ".")) or part.split(".")[0].lower() in reserved
        for part in relative.parts):
        return False
    if any(part.lower() in SKIP_DIRS for part in relative.parts):
        return False
    name = relative.name.lower()
    if (name.startswith(".env") or ".bak" in name
        or relative.stem.lower() in SENSITIVE_NAMES
        or relative.suffix.lower() in SENSITIVE_SUFFIXES):
        return False
    parts = relative.parts
    if len(parts) == 1:
        return parts[0] in ROOT_FILES
    if parts[:2] == ("src", "gitpublish") and len(parts) == 3:
        return relative.suffix == ".py"
    if len(parts) == 2:
        if parts[0] == "tests":
            return (name.startswith("test_") or name == "conftest.py") and relative.suffix == ".py"
        if parts[0] == "tools":
            return relative.suffix == ".py"
        if parts[0] == "docs":
            return relative.suffix == ".md"
        if parts[0] == "installers":
            return parts[1] in INSTALLERS
    return False


def is_excluded(path: Path, root: Path = ROOT) -> bool:
    relative = path.relative_to(root)
    if not allowed_relative(PurePosixPath(relative.as_posix())):
        return True
    return any((root / Path(*relative.parts[:i])).is_symlink()
        for i in range(1, len(relative.parts) + 1))


def collect_source_files(root: Path = ROOT) -> list[Path]:
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        current = Path(directory)
        if current == root:
            dirs[:] = [d for d in dirs if d in {"src", "tests", "docs", "tools", "installers"}
                and not (current / d).is_symlink()]
        else:
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not (current / d).is_symlink()]
        for name in names:
            path = current / name
            if not is_excluded(path, root) and path.is_file():
                files.append(path)
    return sorted(files)


def build_snapshot(root: Path = ROOT, output: Path | None = None) -> tuple[Path, str, int]:
    root = root.resolve()
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        output = root / "dist" / f"git-publish-{APP_VERSION}-{stamp}.zip"
    files = collect_source_files(root)
    if audit_source_files(files, root):
        raise RuntimeError("Source có mẫu thông tin xác thực; đã chặn tạo ZIP. Không in giá trị.")
    required = {"publish.py", "README.md", "src/gitpublish/config.py"}
    if not required.issubset({p.relative_to(root).as_posix() for p in files}):
        raise RuntimeError("Thiếu file nguồn bắt buộc; không tạo ZIP.")
    output.parent.mkdir(parents=True, exist_ok=True)
    hashes = {}
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            data = path.read_bytes()
            hashes[relative] = sha256(data).hexdigest()
            info = ZipInfo.from_file(path, arcname=f"{ARCHIVE_ROOT}/{relative}")
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
        archive.writestr(f"{ARCHIVE_ROOT}/{MANIFEST}",
            json.dumps(hashes, ensure_ascii=False, indent=2) + "\n")
    verify_snapshot(output)
    return output, sha256(output.read_bytes()).hexdigest(), len(files)


def verify_snapshot(path: Path) -> int:
    """Validate member policy, CRC and file hashes without extracting the ZIP."""
    with ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len({name.casefold() for name in names}):
            raise RuntimeError("ZIP có đường dẫn trùng lặp.")
        for info in infos:
            relative = PurePosixPath(info.filename)
            if (not relative.parts or relative.parts[0] != ARCHIVE_ROOT or info.is_dir()
                or relative.as_posix() != info.filename):
                raise RuntimeError("ZIP có cấu trúc không hợp lệ.")
            member = PurePosixPath(*relative.parts[1:])
            if member.as_posix() != MANIFEST and not allowed_relative(member):
                raise RuntimeError("ZIP chứa đường dẫn ngoài allowlist.")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise RuntimeError("ZIP chứa symlink.")
        if archive.testzip() is not None:
            raise RuntimeError("ZIP không vượt qua CRC check.")
        if f"{ARCHIVE_ROOT}/{MANIFEST}" not in names:
            raise RuntimeError("ZIP thiếu source manifest.")
        manifest = json.loads(archive.read(f"{ARCHIVE_ROOT}/{MANIFEST}"))
        actual = {name[len(ARCHIVE_ROOT) + 1:]: sha256(archive.read(name)).hexdigest()
            for name in names if name != f"{ARCHIVE_ROOT}/{MANIFEST}"}
        if manifest != actual or not {"publish.py", "README.md", "src/gitpublish/config.py"}.issubset(actual):
            raise RuntimeError("Manifest ZIP không khớp nội dung hoặc thiếu file bắt buộc.")
        if any(audit_source_bytes(archive.read(f"{ARCHIVE_ROOT}/{name}"), name) for name in actual):
            raise RuntimeError("ZIP có mẫu thông tin xác thực; đã chặn. Không in giá trị.")
        return len(actual)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path, help="New ZIP path (must not already exist)")
    group.add_argument("--verify", type=Path, help="Verify an existing ZIP without extraction")
    group.add_argument("--audit", action="store_true", help="Audit allowlisted source; locations/rule IDs only")
    args = parser.parse_args()
    if args.audit:
        files = collect_source_files()
        findings = audit_source_files(files)
        print(json.dumps({"status": "FAIL" if findings else "PASS", "files": len(files),
            "findings": findings, "scope": "Known credential patterns only; manual review remains required"},
            ensure_ascii=False, indent=2))
        if findings:
            raise SystemExit(1)
        return
    if args.verify:
        print(f"PASS: ZIP verified ({verify_snapshot(args.verify)} source files)")
        return
    output, digest, count = build_snapshot(output=args.output)
    print(f"PASS: {output}\nSource files: {count}\nSHA256: {digest}")
    print("Allowlist/manifest verified. Manual content review is still required before release.")


if __name__ == "__main__":
    main()
