"""Sensitive file detection and protection."""

import fnmatch
import os
from pathlib import Path

from .config import (
    SENSITIVE_DIRECTORIES,
    SENSITIVE_EXTENSIONS,
    SENSITIVE_NAMES,
    SENSITIVE_PATTERNS,
)
from .git import has_commits, is_git_repository, run_git


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()

    if name in {item.lower() for item in SENSITIVE_NAMES}:
        return True

    if path.is_dir() and name in {
        item.lower() for item in SENSITIVE_DIRECTORIES
    }:
        return True

    if path.suffix.lower() in SENSITIVE_EXTENSIONS:
        return True

    return any(
        fnmatch.fnmatchcase(name, pattern.lower())
        for pattern in SENSITIVE_PATTERNS
    )


def scan_project(project_dir: Path) -> list[Path]:
    """Find sensitive files and directories without entering .git."""

    project_dir = project_dir.resolve()
    detected: list[Path] = []

    def scan_error(error: OSError) -> None:
        raise RuntimeError("Không thể quét đầy đủ thư mục; đã chặn publish.") from error

    for root, dirs, files in os.walk(project_dir, followlinks=False, onerror=scan_error):
        root_path = Path(root)

        dirs[:] = sorted(
            [d for d in dirs if d != ".git"],
            key=str.lower,
        )

        sensitive_dirs = []

        for directory in dirs:
            path = root_path / directory
            if is_sensitive(path):
                detected.append(path)
                sensitive_dirs.append(directory)

        # Do not scan inside a directory already selected as sensitive.
        dirs[:] = [d for d in dirs if d not in sensitive_dirs]

        for filename in files:
            path = root_path / filename
            if is_sensitive(path):
                detected.append(path)

    return sorted(
        set(detected),
        key=lambda p: str(p).lower(),
    )


def scan_git_sensitive_paths(project_dir: Path) -> list[Path]:
    """Inspect path names only, including deleted secrets in reachable history."""
    if not is_git_repository(project_dir):
        return []
    names = run_git(project_dir, "ls-files", "--cached", "-z").split(chr(0))
    if has_commits(project_dir):
        names += run_git(
            project_dir, "log", "--all", "--format=", "--name-only",
            "--no-renames", "-z",
        ).split(chr(0))
    found = set()
    for name in filter(None, names):
        relative = Path(name)
        # Git tree entries are relative; reject malformed names defensively.
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Đường dẫn Git không hợp lệ; đã chặn publish.")
        for index, part in enumerate(relative.parts[:-1]):
            if part.lower() in SENSITIVE_DIRECTORIES:
                found.add(project_dir.joinpath(*relative.parts[:index + 1]))
                break
        else:
            if is_sensitive(project_dir / relative):
                found.add(project_dir / relative)
    return sorted(found)


def _ignore_entry(project_dir: Path, item: Path) -> str:
    relative = item.relative_to(project_dir).as_posix()
    if any(c in relative for c in "\r\n\0"):
        raise RuntimeError("Không thể bảo vệ tên file chứa ký tự xuống dòng/NUL.")
    # Escape Git ignore glob syntax and whitespace, without broadening the rule.
    escaped = "".join("\\" + c if c in "\\*?[]#! " else c for c in relative)
    return escaped + ("/" if item.is_dir() and not item.is_symlink() else "")


def choose_sensitive_files(
    files: list[Path],
    project_dir: Path,
) -> list[Path]:
    """Protect all detected sensitive paths by default."""
    print("\n" + "=" * 50)
    print("🛡️ FILE PROTECTION")
    print("=" * 50)

    if not files:
        print("✓ Không phát hiện file/thư mục nhạy cảm.")
        return []

    for index, path in enumerate(files, 1):
        relative = path.relative_to(project_dir)
        suffix = "/" if path.is_dir() else ""
        print(f"{index}. {relative}{suffix}")

    print("\nEnter. Bảo vệ TẤT CẢ (mặc định)")
    print("Nhập số: Chỉ bảo vệ các mục được chọn")
    print("0. Không bảo vệ mục nào (có rủi ro)")

    while True:
        value = input(
            "\n🔒 Lựa chọn [Enter=All]: "
        ).strip()

        if not value:
            selected = list(files)
        elif value == "0":
            selected = []
        else:
            try:
                indexes = [
                    int(item)
                    for item in value.replace(",", " ").split()
                ]
            except ValueError:
                print("❌ Vui lòng nhập số hợp lệ.")
                continue

            if (
                not indexes
                or any(i < 1 or i > len(files) for i in indexes)
            ):
                print("❌ Lựa chọn không hợp lệ.")
                continue

            selected = [
                files[i - 1]
                for i in dict.fromkeys(indexes)
            ]

        unprotected = [
            path for path in files if path not in selected
        ]

        if unprotected:
            print("\n⚠ CÁC MỤC SẼ KHÔNG ĐƯỢC BẢO VỆ:")
            for path in unprotected:
                print(f"  ! {path.relative_to(project_dir)}")

            acknowledgment = input(
                "⚠ Tiếp tục mà không bảo vệ các file trên? [y/N]: "
            ).strip().lower()

            if acknowledgment not in ("y", "yes"):
                print("✓ Đã từ chối bỏ bảo vệ. Chọn lại.")
                continue

        print("\n🔐 Các mục được bảo vệ:")
        if selected:
            for path in selected:
                print(f"✓ {path.relative_to(project_dir)}")
        else:
            print("Không có (người dùng đã xác nhận rủi ro).")

        return selected



def ensure_gitignore(
    project_dir: Path,
    protected: list[Path],
) -> list[str]:
    """Add protected paths to .gitignore and untrack them if necessary."""

    gitignore = project_dir / ".gitignore"
    if gitignore.is_symlink():
        raise RuntimeError(".gitignore là symlink; đã dừng để bảo vệ file đích.")
    entries = [_ignore_entry(project_dir, item) for item in protected]
    existing = []

    if gitignore.exists():
        existing = gitignore.read_text(
            encoding="utf-8",
        ).splitlines()

    added = []

    for entry in entries:
        if entry not in existing:
            existing.append(entry)
            added.append(entry)

    if added:
        with gitignore.open("w", encoding="utf-8", newline="\n") as file:
            file.write("\n".join(existing) + "\n")
        print("\n🔒 Đã cập nhật .gitignore:")
        for entry in added:
            print(f"✓ {entry}")

    # Remove protected paths from the Git index without deleting local files.
    if protected:
        for item in protected:
            relative = item.relative_to(project_dir).as_posix()
            run_git(
                project_dir,
                "--literal-pathspecs",
                "rm",
                "--cached",
                "--ignore-unmatch",
                "-r",
                "--",
                relative,
            )

    return added


def preflight_sensitive_files(
    project_dir: Path,
    protected: list[Path],
) -> None:
    """Block publication of protected paths in index or Git history."""
    if not protected:
        return

    tracked = set(
        filter(
            None,
            run_git(
                project_dir, "ls-files", "-z", "--cached"
            ).split(chr(0)),
        )
    )

    for item in protected:
        relative = item.relative_to(project_dir).as_posix()
        prefix = relative.rstrip("/") + "/"

        if relative in tracked or any(
            name.startswith(prefix) for name in tracked
        ):
            raise RuntimeError(
                f"File được bảo vệ vẫn đang được Git theo dõi: "
                f"{relative}. Đã chặn publish."
            )

        if has_commits(project_dir):
            history = run_git(
                project_dir,
                "--literal-pathspecs",
                "log",
                "--all",
                "--format=%h",
                "--",
                relative,
            ).strip()

            if history:
                raise RuntimeError(
                    f"File nhạy cảm '{relative}' tồn tại trong "
                    "lịch sử Git. .gitignore không xóa lịch sử. "
                    "Đã chặn publish để tránh đưa dữ liệu cũ "
                    "lên GitHub. Hãy kiểm tra và làm sạch lịch sử "
                    "Git trước khi tiếp tục."
                )

    print("✓ Kiểm tra Git index và lịch sử file bảo vệ: OK.")
