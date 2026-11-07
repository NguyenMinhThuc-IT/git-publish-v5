"""Security and visibility tests for Git Publish V4."""

from types import SimpleNamespace

import pytest

from src.gitpublish.cli import (
    assert_repository_visibility,
    choose_visibility,
)
from src.gitpublish.git import (
    commit,
    initialize_git,
    run_git,
)
from src.gitpublish.github import GitHubError
from src.gitpublish.security import (
    choose_sensitive_files,
    ensure_gitignore,
    preflight_sensitive_files,
)


def test_private_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert choose_visibility() is False


def test_public_selection(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert choose_visibility() is True


def test_protect_all_by_default(tmp_path, monkeypatch):
    paths = [tmp_path / ".env", tmp_path / "server.key"]
    for path in paths:
        path.write_text("FAKE TEST DATA", encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _: "")
    assert choose_sensitive_files(paths, tmp_path) == paths


def test_disable_protection_requires_confirmation(tmp_path, monkeypatch):
    secret = tmp_path / ".env"
    secret.write_text("FAKE TEST DATA", encoding="utf-8")

    answers = iter(["0", "n", "0", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert choose_sensitive_files([secret], tmp_path) == []


def test_tracked_secret_blocks_publish(tmp_path):
    initialize_git(tmp_path)
    secret = tmp_path / ".env"
    secret.write_text("FAKE TEST DATA", encoding="utf-8")
    run_git(tmp_path, "add", "-f", ".env")

    with pytest.raises(RuntimeError, match="đang được Git theo dõi"):
        preflight_sensitive_files(tmp_path, [secret])


def test_secret_in_history_blocks_publish(tmp_path):
    initialize_git(tmp_path)
    run_git(tmp_path, "config", "user.name", "V4 Test")
    run_git(tmp_path, "config", "user.email", "test@example.com")

    secret = tmp_path / ".env"
    secret.write_text("FAKE TEST DATA", encoding="utf-8")
    run_git(tmp_path, "add", "-f", ".env")
    commit(tmp_path, "Test historical secret")

    ensure_gitignore(tmp_path, [secret])

    with pytest.raises(RuntimeError, match="lịch sử Git"):
        preflight_sensitive_files(tmp_path, [secret])


def test_new_protected_secret_is_safe(tmp_path):
    initialize_git(tmp_path)

    secret = tmp_path / ".env"
    secret.write_text("FAKE TEST DATA", encoding="utf-8")

    ensure_gitignore(tmp_path, [secret])
    run_git(tmp_path, "add", "-A")

    preflight_sensitive_files(tmp_path, [secret])


def test_public_repo_rejected_when_private_requested(monkeypatch):
    result = SimpleNamespace(
        returncode=0,
        stdout="false\n",
        stderr="",
    )

    monkeypatch.setattr(
        "src.gitpublish.cli.subprocess.run",
        lambda *args, **kwargs: result,
    )

    with pytest.raises(GitHubError, match="Đã chặn push"):
        assert_repository_visibility(
            "https://github.com/example/demo",
            is_public=False,
        )


def test_private_repo_accepted_when_private_requested(monkeypatch):
    result = SimpleNamespace(
        returncode=0,
        stdout="true\n",
        stderr="",
    )

    monkeypatch.setattr(
        "src.gitpublish.cli.subprocess.run",
        lambda *args, **kwargs: result,
    )

    assert_repository_visibility(
        "https://github.com/example/demo",
        is_public=False,
    )
