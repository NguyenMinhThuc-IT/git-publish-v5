"""Core tests for Git Publish V4."""

import pytest

from src.gitpublish.config import APP_VERSION
from src.gitpublish.git import (
    initialize_git,
    is_git_repository,
    run_git,
    stage_files,
    has_staged_changes,
    has_commits,
    get_current_branch,
    commit,
)
from src.gitpublish.github import (
    GitHubError,
    validate_repo_name,
)
from src.gitpublish.security import (
    scan_project,
    ensure_gitignore,
)


def setup_test_repo(tmp_path):
    """Create an isolated Git repository for testing."""
    initialize_git(tmp_path)
    run_git(tmp_path, "config", "user.name", "Git Publish Test")
    run_git(tmp_path, "config", "user.email", "test@example.com")
    return tmp_path


def test_version():
    # V5 release candidate replaces the V4 runtime version.
    from src.gitpublish import __version__
    assert APP_VERSION == __version__ == "5.0.0rc1"


def test_valid_repo_name():
    validate_repo_name("my-python-project_01")


@pytest.mark.parametrize(
    "name",
    ["-invalid", "name with spaces", "project.git", "..", ""],
)
def test_invalid_repo_name(name):
    with pytest.raises(GitHubError):
        validate_repo_name(name)


def test_git_initialize(tmp_path):
    assert not is_git_repository(tmp_path)

    initialize_git(tmp_path)

    assert is_git_repository(tmp_path)
    assert get_current_branch(tmp_path) == "main"


def test_git_stage_and_commit(tmp_path):
    project = setup_test_repo(tmp_path)

    (project / "main.py").write_text(
        'print("Hello Git Publish")\n',
        encoding="utf-8",
    )

    stage_files(project)

    assert has_staged_changes(project)

    commit(project, "Initial commit")

    assert has_commits(project)
    assert not has_staged_changes(project)


def test_no_changes_after_commit(tmp_path):
    project = setup_test_repo(tmp_path)

    (project / "README.md").write_text(
        "# Demo\n",
        encoding="utf-8",
    )

    stage_files(project)
    commit(project, "First commit")

    stage_files(project)

    assert not has_staged_changes(project)


def test_sensitive_file_detection(tmp_path):
    (tmp_path / ".env").write_text(
        "TOKEN=example\n",
        encoding="utf-8",
    )
    (tmp_path / "server.key").write_text(
        "example-key\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "print('safe')\n",
        encoding="utf-8",
    )

    detected = {p.name for p in scan_project(tmp_path)}

    assert ".env" in detected
    assert "server.key" in detected
    assert "main.py" not in detected


def test_protection_preserves_local_file(tmp_path):
    project = setup_test_repo(tmp_path)

    secret = project / ".env"
    secret.write_text(
        "TOKEN=example\n",
        encoding="utf-8",
    )

    # Simulate a sensitive file already tracked by Git.
    run_git(project, "add", "-f", ".env")
    commit(project, "Add test file")

    ensure_gitignore(project, [secret])

    # The local file must remain untouched.
    assert secret.exists()

    # Git must no longer track the protected file.
    tracked = run_git(project, "ls-files", "--", ".env")
    assert tracked.strip() == ""

    # The file must be protected by .gitignore.
    gitignore = (project / ".gitignore").read_text(
        encoding="utf-8"
    )
    assert ".env" in gitignore.splitlines()
