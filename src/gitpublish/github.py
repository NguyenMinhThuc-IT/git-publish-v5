"""GitHub CLI integration for Git Publish."""

import re
import shutil
import subprocess
from pathlib import Path

from .config import COMMAND_TIMEOUT
from .git import add_remote, get_remote_url


class GitHubError(RuntimeError):
    """Raised when GitHub CLI operations fail."""


class RepositoryNotFound(GitHubError):
    """The GitHub repository API explicitly returned HTTP 404."""


def run_gh(*args: str, cwd: Path | None = None) -> str:
    if not shutil.which("gh"):
        raise GitHubError(
            "Không tìm thấy GitHub CLI (gh). Hãy cài đặt GitHub CLI."
        )

    try:
        result = subprocess.run(
            ["gh", *args],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=COMMAND_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitHubError(
            f"GitHub CLI quá thời gian chờ: gh {' '.join(args)}"
        ) from exc
    except OSError as exc:
        raise GitHubError("Không thể chạy GitHub CLI.") from exc

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        if args[:1] == ("api",) and re.search(r"\bHTTP 404\b", message):
            raise RepositoryNotFound("GitHub repository API trả về HTTP 404.")
        raise GitHubError(
            message or f"GitHub CLI failed: gh {' '.join(args)}"
        )

    return result.stdout.strip()


def check_github_login() -> None:
    try:
        run_gh("auth", "status")
    except GitHubError as exc:
        raise GitHubError(
            "Không xác minh được đăng nhập GitHub CLI. "
            "Kiểm tra kết nối/quyền và chạy: gh auth login"
        ) from exc


def get_github_owner() -> str:
    owner = run_gh("api", "user", "--jq", ".login")
    if not owner:
        raise GitHubError("Không lấy được GitHub username.")
    return owner


def validate_repo_name(repo_name: str) -> str:
    name = repo_name.strip()

    if not name:
        raise GitHubError("Tên repository không được để trống.")

    if len(name) > 100:
        raise GitHubError("Tên repository không được dài quá 100 ký tự.")

    if name in {".", ".."} or name.startswith("-"):
        raise GitHubError("Tên repository không hợp lệ.")

    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise GitHubError(
            "Tên repository chỉ được chứa chữ, số, dấu chấm, "
            "gạch ngang và gạch dưới."
        )

    if name.endswith(".git"):
        raise GitHubError("Không nhập đuôi .git vào tên repository.")

    return name


def normalize_remote(url: str) -> str:
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"([A-Za-z0-9-]+)/([A-Za-z0-9._-]+?)(?:\.git)?/?",
        url.strip(), flags=re.IGNORECASE,
    )
    if not match:
        raise GitHubError("Origin không phải URL GitHub được hỗ trợ; đã chặn publish.")
    owner, name = match.groups()
    validate_repo_name(name)
    return f"https://github.com/{owner}/{name}".lower()


def get_repository_url(owner: str, repo_name: str) -> str | None:
    try:
        return run_gh(
            "api",
            f"repos/{owner}/{validate_repo_name(repo_name)}",
            "--jq",
            ".html_url",
        )
    except RepositoryNotFound:
        return None


def create_github_repo(
    project_dir: Path,
    repo_name: str,
    is_public: bool,
) -> str:
    """Create or reuse the authenticated user's GitHub repository."""

    repo_name = validate_repo_name(repo_name)
    owner = get_github_owner()
    expected = f"https://github.com/{owner}/{repo_name}"
    current_remote = get_remote_url(project_dir, "origin")
    if current_remote and normalize_remote(current_remote) != normalize_remote(expected):
        raise GitHubError("Remote 'origin' đang trỏ tới repository khác. Đã chặn publish.")

    print()
    print("🌍 GitHub Repository...")

    url = get_repository_url(owner, repo_name)

    if url is None:
        visibility = "--public" if is_public else "--private"
        print("📦 Creating GitHub repository...")

        run_gh(
            "repo",
            "create",
            repo_name,
            visibility,
            cwd=project_dir,
        )

        url = get_repository_url(owner, repo_name)

    if not url:
        raise GitHubError("Không lấy được URL của GitHub repository.")
    if normalize_remote(url) != normalize_remote(expected):
        raise GitHubError("GitHub trả về URL repository khác đích; đã chặn publish.")

    expected_remote = f"{url}.git"
    current_remote = get_remote_url(project_dir, "origin")

    if current_remote is None:
        print("🔗 Adding origin...")
        add_remote(project_dir, expected_remote)
    elif normalize_remote(current_remote) == normalize_remote(expected_remote):
        print(f"✓ origin đã trỏ đúng repository: {url}")
    else:
        raise GitHubError(
            "Remote 'origin' đang trỏ tới repository khác.\n"
            f"Hiện tại: {current_remote}\n"
            f"Mục tiêu: {expected_remote}\n"
            "Git Publish không tự ý thay đổi remote để tránh push nhầm dự án. "
            "Hãy kiểm tra và sửa remote thủ công trước khi chạy lại."
        )

    return url
