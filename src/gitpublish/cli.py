"""Main application workflow for Git Publish."""

import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from .clipboard import copy_to_clipboard
from .config import APP_NAME, APP_VERSION
from .git import (
    GitCommandError,
    commit,
    get_remote_url,
    get_staged_files,
    has_commits,
    initialize_git,
    prepare_remote_for_push,
    push,
    stage_files,
    validate_project_repository,
)
from .github import (
    GitHubError,
    check_github_login,
    create_github_repo,
    get_github_owner,
    get_repository_url,
    run_gh,
    normalize_remote,
    validate_repo_name,
)
from .security import (
    choose_sensitive_files,
    ensure_gitignore,
    preflight_sensitive_files,
    scan_project,
    scan_git_sensitive_paths,
)
from .ui import (
    ask_text,
    print_header,
    show_git_preview,
)


def check_requirements() -> None:
    missing = [
        command
        for command in ("git", "gh")
        if not shutil.which(command)
    ]

    if missing:
        raise RuntimeError(
            "Thiếu chương trình cần thiết: "
            + ", ".join(missing)
            + ". Hãy cài đặt trước khi sử dụng."
        )

    print("✓ Git")
    print("✓ GitHub CLI")


def ask_yes_no(question: str, default: bool = False) -> bool:
    """Read a yes/no answer with a safe default."""
    hint = "[Y/n]" if default else "[y/N]"

    while True:
        try:
            answer = input(f"{question} {hint}: ").strip().lower()
        except EOFError:
            raise RuntimeError(
                "Không nhận được dữ liệu nhập từ Terminal."
            ) from None

        if not answer:
            return default

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("❌ Vui lòng nhập y hoặc n.")


def choose_visibility() -> bool:
    """Choose repository visibility. Private is the default."""
    print("\n🌐 Repository visibility")

    while True:
        choice = input(
            "Công khai repository? [y/N]: "
        ).strip().lower()

        if choice in ("", "n", "no"):
            print("🔒 Visibility: Private")
            return False

        if choice in ("y", "yes"):
            print("🌍 Visibility: Public")
            return True

        print("❌ Vui lòng nhập y hoặc n.")


def assert_repository_visibility(url: str, is_public: bool) -> None:
    """Verify the actual GitHub visibility before pushing."""
    try:
        result = subprocess.run(
            [
                "gh", "repo", "view", url,
                "--json", "isPrivate",
                "--jq", ".isPrivate",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitHubError(
            "Hết thời gian kiểm tra quyền repository trên GitHub."
        ) from exc

    if result.returncode != 0:
        raise GitHubError(
            "Không xác minh được quyền truy cập repository. "
            "Đã chặn push. "
            + result.stderr.strip()
        )

    actual = result.stdout.strip().lower()

    if actual not in ("true", "false"):
        raise GitHubError(
            f"GitHub trả về trạng thái không hợp lệ: {actual!r}"
        )

    actual_private = actual == "true"
    expected_private = not is_public

    if actual_private != expected_private:
        actual_label = "Private" if actual_private else "Public"
        expected_label = "Private" if expected_private else "Public"

        raise GitHubError(
            f"Repository thực tế đang {actual_label}, "
            f"nhưng bạn chọn {expected_label}. "
            "Đã chặn push để tránh công khai dữ liệu ngoài ý muốn."
        )

    print(
        "✓ Repository visibility đã xác minh: "
        + ("Private" if actual_private else "Public")
    )


def choose_repository_visibility(repo_name: str) -> bool:
    """Reuse visibility for existing repositories."""
    owner = get_github_owner()
    url = get_repository_url(owner, repo_name)

    if url is None:
        print("\n📦 Repository mới.")
        return choose_visibility()

    result = run_gh(
        "repo",
        "view",
        f"{owner}/{repo_name}",
        "--json",
        "isPrivate",
        "--jq",
        ".isPrivate",
    ).strip().lower()

    if result not in ("true", "false"):
        raise GitHubError(
            "Không xác định được quyền truy cập repository."
        )

    is_public = result == "false"

    print("\n✓ Repository đã tồn tại:")
    print(f"  {url}")
    print(
        "✓ Visibility: "
        + ("Public" if is_public else "Private")
    )
    print("✓ Giữ nguyên quyền truy cập hiện tại.")

    return is_public


def detect_repo_name_from_origin(
    project_dir: Path,
) -> str | None:
    """Read the repository name from a GitHub origin."""
    origin = get_remote_url(project_dir)

    if not origin:
        return None

    normalize_remote(origin)
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|"
        r"ssh://git@github\.com/)"
        r"([^/]+)/([^/]+?)(?:\.git)?/?",
        origin.strip(),
        flags=re.IGNORECASE,
    )

    if not match:
        raise GitHubError(
            "Origin hiện tại không phải URL GitHub được hỗ trợ:\n"
            f"{origin}\n"
            "Đã dừng để tránh publish nhầm repository."
        )

    owner, repo_name = match.groups()
    current_owner = get_github_owner()

    if owner.casefold() != current_owner.casefold():
        raise GitHubError(
            f"Origin thuộc tài khoản '{owner}', "
            f"nhưng bạn đăng nhập '{current_owner}'. "
            "Đã dừng để tránh publish nhầm."
        )

    return validate_repo_name(repo_name)


def get_user_options(
    project_dir: Path,
) -> tuple[str, bool, bool, bool]:
    repo_name = detect_repo_name_from_origin(project_dir)

    if repo_name:
        print(f"✓ Repository name từ origin: {repo_name}")
    else:
        while True:
            repo_name = ask_text("📦 Repository name: ")
            try:
                repo_name = validate_repo_name(repo_name)
                break
            except GitHubError as exc:
                print(f"❌ {exc}")

    is_public = choose_repository_visibility(repo_name)

    copy_url = ask_yes_no(
        "📋 Copy GitHub URL after push?",
        default=True,
    )
    open_browser = ask_yes_no(
        "🌐 Open GitHub after push?",
        default=False,
    )

    return repo_name, is_public, copy_url, open_browser


def main() -> int:
    project_dir = Path.cwd().resolve()

    print_header(f"{APP_NAME} v{APP_VERSION}")
    print(f"📁 Project: {project_dir}\n")

    check_requirements()
    validate_project_repository(project_dir)
    check_github_login()

    (
        repo_name,
        is_public,
        copy_url,
        open_browser,
    ) = get_user_options(project_dir)

    # 1. Detect and protect sensitive files.
    detected = sorted(set(scan_project(project_dir) + scan_git_sensitive_paths(project_dir)))
    selected = choose_sensitive_files(detected, project_dir)

    # 2. Initialize Git before using Git index operations.
    initialize_git(project_dir)

    if selected:
        ensure_gitignore(project_dir, selected)

    # 3. Stage changes after protection rules are applied.
    stage_files(project_dir)

    preflight_sensitive_files(project_dir, selected)

    staged = get_staged_files(project_dir)
    protected_names = [
        path.relative_to(project_dir).as_posix()
        for path in selected
    ]

    show_git_preview(staged, protected_names)

    # 3. Commit only when there are staged changes.
    if staged:
        if not ask_yes_no("Xác nhận các file trên và tạo commit?"):
            print("\n❌ Đã hủy. Staging area được giữ nguyên.")
            return 0

        commit_message = ask_text("📝 Commit message: ")
        commit(project_dir, commit_message)
        print("✓ Commit created.")
    else:
        print("ℹ Không có thay đổi mới để commit.")

        if not has_commits(project_dir):
            raise GitCommandError(
                "Repository chưa có commit nào. "
                "Hãy thêm file hoặc thay đổi trước khi publish."
            )

        if not ask_yes_no("Tiếp tục push các commit hiện có?"):
            print("\n❌ Đã hủy.")
            return 0

    # 4. Create or reuse the GitHub repository and verify origin.
    url = create_github_repo(
        project_dir,
        repo_name,
        is_public,
    )

    assert_repository_visibility(url, is_public)

    # 5. Push the current branch. Failure is reported, never hidden.
    # Check remote history before pushing.
    sync_status = prepare_remote_for_push(
        project_dir,
        confirm_fast_forward=lambda question: ask_yes_no(question),
    )

    if sync_status == "cancelled":
        print("❌ Đã hủy đồng bộ. Không thực hiện push.")
        return 0

    # Verify protected files again after any local update.
    preflight_sensitive_files(project_dir, selected)
    # Include newly fetched history and paths introduced by fast-forward.
    new_sensitive = set(scan_project(project_dir) + scan_git_sensitive_paths(project_dir)) - set(detected)
    if new_sensitive:
        preflight_sensitive_files(project_dir, sorted(new_sensitive))

    if sync_status in ("up_to_date", "fast_forwarded"):
        print("✓ Không có commit mới cần push.")
    else:
        print("\n🚀 Pushing to GitHub...")
        push(project_dir)

    # 6. Success actions only run after a successful push.
    print("\n" + "=" * 54)
    print("✅ PUBLISH THÀNH CÔNG!")
    print("=" * 54)
    print(f"\n🔗 Repository: {url}")

    if copy_url:
        if copy_to_clipboard(url):
            print("📋 URL đã được copy vào clipboard.")
        else:
            print("⚠ Không tìm thấy clipboard utility hoặc không thể copy.")
            print(f"   Bạn có thể copy URL thủ công: {url}")

    if open_browser:
        try:
            opened = webbrowser.open(url)
            if opened:
                print("🌐 Đã gửi yêu cầu mở trình duyệt.")
            else:
                print("⚠ Không thể mở trình duyệt trong môi trường hiện tại.")
        except Exception as exc:
            print(f"⚠ Không thể mở trình duyệt: {exc}")

    return 0


def run() -> None:
    # Windows legacy consoles may not encode Vietnamese/emoji output.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy bởi người dùng.")
        exit_code = 130
    except EOFError:
        print("\n❌ Đã dừng: không nhận được dữ liệu nhập từ Terminal.")
        exit_code = 1
    except (GitCommandError, GitHubError, RuntimeError, OSError) as exc:
        print(f"\n❌ Publish thất bại:\n{exc}")
        exit_code = 1
    except Exception as exc:
        print(f"\n❌ Lỗi không mong đợi: {exc}")
        exit_code = 1

    raise SystemExit(exit_code)
