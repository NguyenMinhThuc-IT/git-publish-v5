"""Git operations for Git Publish."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from .config import COMMAND_TIMEOUT, DEFAULT_BRANCH


class GitCommandError(RuntimeError):
    """Raised when a Git command fails."""

    def __init__(self, message: str, returncode: int | None = None):
        super().__init__(message)
        self.returncode = returncode


def run_git(
    project_dir: Path,
    *args: str,
    timeout: int = COMMAND_TIMEOUT,
) -> str:
    command = ["git", *map(str, args)]

    try:
        result = subprocess.run(
            command,
            cwd=project_dir,
            text=True,
            encoding="utf-8",
            errors="surrogateescape",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitCommandError("Không tìm thấy Git. Hãy cài đặt Git.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitCommandError(
            f"Lệnh Git quá thời gian chờ: git {' '.join(args)}"
        ) from exc

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise GitCommandError(
            message or f"Git command failed: git {' '.join(args)}",
            returncode=result.returncode,
        )

    # NUL-separated path output must preserve leading/trailing whitespace.
    return result.stdout if "-z" in args else result.stdout.rstrip("\r\n")


def is_git_repository(project_dir: Path) -> bool:
    try:
        # Both worktrees (true) and bare repositories (false) are Git repos.
        return run_git(project_dir, "rev-parse", "--is-inside-work-tree") in {"true", "false"}
    except GitCommandError as exc:
        if exc.returncode == 128 and not (project_dir / ".git").exists():
            return False
        raise


def validate_project_repository(project_dir: Path) -> None:
    """Reject a parent repository and detached HEAD before changing files."""
    if is_git_repository(project_dir):
        if run_git(project_dir, "rev-parse", "--is-bare-repository") == "true":
            raise GitCommandError("Bare repository không có working tree; đã chặn publish.")
        root = Path(run_git(project_dir, "rev-parse", "--show-toplevel"))
        if root.resolve() != project_dir.resolve():
            raise GitCommandError("Hãy chạy publish tại thư mục gốc repository.")
        get_current_branch(project_dir)
    elif (project_dir / ".git").exists():
        raise GitCommandError("Không thể sử dụng Git repository hiện tại.")


def initialize_git(project_dir: Path) -> None:
    validate_project_repository(project_dir)
    if not is_git_repository(project_dir):
        print("📦 Initializing Git...")
        run_git(project_dir, "init")
        run_git(project_dir, "branch", "-M", DEFAULT_BRANCH)
    else:
        print("✓ Git repository already exists.")


def stage_files(project_dir: Path) -> None:
    run_git(project_dir, "add", "-A")


def get_staged_files(project_dir: Path) -> list[str]:
    output = run_git(
        project_dir,
        "diff",
        "--cached",
        "--name-status",
        "--no-renames",
        "-z",
    )
    fields = output.rstrip(chr(0)).split(chr(0)) if output else []
    # repr only for control characters; normal Unicode remains readable.
    return [
        f"{status}\t{path if all(c.isprintable() for c in path) else repr(path)}"
        for status, path in zip(fields[::2], fields[1::2])
    ]


def has_staged_changes(project_dir: Path) -> bool:
    return bool(get_staged_files(project_dir))


def has_commits(project_dir: Path) -> bool:
    try:
        run_git(project_dir, "rev-parse", "--verify", "--quiet", "HEAD")
        return True
    except GitCommandError as exc:
        if exc.returncode == 1:
            return False
        raise


def get_current_branch(project_dir: Path) -> str:
    branch = run_git(project_dir, "branch", "--show-current")
    if not branch:
        raise GitCommandError(
            "Git đang ở detached HEAD. Hãy chọn một branch."
        )
    return branch


def get_remote_url(project_dir: Path, remote: str = "origin") -> str | None:
    if not is_git_repository(project_dir):
        return None
    if remote not in run_git(project_dir, "remote").splitlines():
        return None
    urls = run_git(project_dir, "remote", "get-url", "--all", remote).splitlines()
    push_urls = run_git(project_dir, "remote", "get-url", "--push", "--all", remote).splitlines()
    if len(urls) != 1 or len(push_urls) != 1 or urls != push_urls:
        raise GitCommandError("Origin có nhiều URL hoặc URL push khác fetch; đã chặn publish.")
    return urls[0]


def add_remote(project_dir: Path, url: str, remote: str = "origin") -> None:
    run_git(project_dir, "remote", "add", remote, url)


def set_remote_url(
    project_dir: Path,
    url: str,
    remote: str = "origin",
) -> None:
    run_git(project_dir, "remote", "set-url", remote, url)


def commit(project_dir: Path, message: str) -> None:
    if not message.strip():
        raise GitCommandError("Commit message không được để trống.")

    if not has_staged_changes(project_dir):
        raise GitCommandError("Không có thay đổi nào trong staging area.")

    run_git(project_dir, "commit", "-m", message.strip())


def prepare_remote_for_push(
    project_dir: Path,
    remote: str = "origin",
    branch: str | None = None,
    confirm_fast_forward: Callable[[str], bool] | None = None,
) -> str:
    """Check remote history without force push or automatic merge."""

    target = branch or get_current_branch(project_dir)

    if not has_commits(project_dir):
        raise GitCommandError("Repository chưa có commit để push.")

    print("\n🔍 Kiểm tra lịch sử GitHub...")

    ref = f"refs/heads/{target}"

    heads = run_git(
        project_dir, "ls-remote", "--heads", remote, ref
    )

    remote_exists = any(
        line.split("\t")[-1] == ref
        for line in heads.splitlines()
    )

    if not remote_exists:
        print("✓ Branch chưa tồn tại trên remote.")
        return "new"

    # Fetch without changing the current working tree.
    run_git(
        project_dir, "fetch", "--no-tags", remote, ref
    )

    counts = run_git(
        project_dir,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...FETCH_HEAD",
    ).split()

    if len(counts) != 2:
        raise GitCommandError(
            "Không xác định được trạng thái đồng bộ."
        )

    local_only, remote_only = map(int, counts)

    if remote_only == 0:
        if local_only == 0:
            print("✓ Local đã đồng bộ với GitHub.")
            return "up_to_date"

        print(f"✓ Có {local_only} commit local cần push.")
        return "ahead"

    if local_only == 0:
        print(f"⬇ GitHub có {remote_only} commit mới.")

        if (
            confirm_fast_forward is None
            or not confirm_fast_forward(
                "Cập nhật local bằng fast-forward?"
            )
        ):
            return "cancelled"

        run_git(
            project_dir, "merge", "--ff-only", "--no-overwrite-ignore", "FETCH_HEAD"
        )

        print("✓ Fast-forward thành công.")
        return "fast_forwarded"

    raise GitCommandError(
        "\n⚠ LỊCH SỬ GIT KHÁC NHAU!\n"
        f"Local có {local_only} commit riêng.\n"
        f"GitHub có {remote_only} commit riêng.\n"
        "Không tự merge hoặc force push.\n"
        "Kiểm tra bằng lệnh:\n"
        "git log --oneline --graph --left-right HEAD...FETCH_HEAD"
    )


def push(
    project_dir: Path,
    remote: str = "origin",
    branch: str | None = None,
) -> None:
    target_branch = branch or get_current_branch(project_dir)

    if not has_commits(project_dir):
        raise GitCommandError("Repository chưa có commit nào để push.")

    run_git(
        project_dir,
        "push",
        "--set-upstream",
        remote,
        target_branch,
        timeout=COMMAND_TIMEOUT,
    )


def push_to_github(project_dir: Path) -> None:
    push(project_dir)
