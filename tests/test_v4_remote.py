"""Offline tests for Git Publish V4.3 remote synchronization."""

import subprocess

import pytest

from src.gitpublish.git import (
    GitCommandError,
    add_remote,
    commit,
    initialize_git,
    prepare_remote_for_push,
    push,
    run_git,
    stage_files,
)


def setup_repositories(tmp_path):
    """Create a local project and an isolated bare remote."""
    remote = tmp_path / "remote.git"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
    )

    local = tmp_path / "local"
    local.mkdir()

    initialize_git(local)

    run_git(local, "config", "user.name", "Git Publish Test")
    run_git(local, "config", "user.email", "test@example.com")

    (local / "main.py").write_text(
        "print('Hello V4')\n",
        encoding="utf-8",
    )

    stage_files(local)
    commit(local, "Initial commit")
    add_remote(local, str(remote))

    return local, remote


def clone_repository(tmp_path, remote):
    """Simulate another developer or GitHub-side changes."""
    second = tmp_path / "second"

    subprocess.run(
        [
            "git", "clone", "--branch", "main",
            str(remote), str(second),
        ],
        check=True,
        capture_output=True,
    )

    run_git(second, "config", "user.name", "Git Publish Test")
    run_git(second, "config", "user.email", "test@example.com")

    return second


def add_commit(project, filename):
    (project / filename).write_text(
        "test content\n",
        encoding="utf-8",
    )

    stage_files(project)
    commit(project, f"Add {filename}")


def test_new_remote_branch(tmp_path):
    local, _ = setup_repositories(tmp_path)

    assert prepare_remote_for_push(local) == "new"


def test_remote_already_up_to_date(tmp_path):
    local, _ = setup_repositories(tmp_path)

    push(local)

    assert prepare_remote_for_push(local) == "up_to_date"


def test_local_has_new_commit(tmp_path):
    local, _ = setup_repositories(tmp_path)

    push(local)
    add_commit(local, "local.py")

    assert prepare_remote_for_push(local) == "ahead"


def test_fast_forward_when_approved(tmp_path):
    local, remote = setup_repositories(tmp_path)

    push(local)

    second = clone_repository(tmp_path, remote)
    add_commit(second, "remote.py")
    push(second)

    status = prepare_remote_for_push(
        local,
        confirm_fast_forward=lambda _: True,
    )

    assert status == "fast_forwarded"
    assert (local / "remote.py").exists()


def test_decline_remote_update(tmp_path):
    local, remote = setup_repositories(tmp_path)

    push(local)

    second = clone_repository(tmp_path, remote)
    add_commit(second, "remote.py")
    push(second)

    old_head = run_git(local, "rev-parse", "HEAD")

    status = prepare_remote_for_push(
        local,
        confirm_fast_forward=lambda _: False,
    )

    assert status == "cancelled"
    assert run_git(local, "rev-parse", "HEAD") == old_head
    assert not (local / "remote.py").exists()


def test_diverged_history_is_blocked(tmp_path):
    local, remote = setup_repositories(tmp_path)

    push(local)

    second = clone_repository(tmp_path, remote)

    add_commit(local, "local.py")
    add_commit(second, "remote.py")
    push(second)

    old_head = run_git(local, "rev-parse", "HEAD")

    with pytest.raises(
        GitCommandError,
        match="LỊCH SỬ GIT KHÁC NHAU",
    ):
        prepare_remote_for_push(local)

    # Confirm no local history was overwritten.
    assert run_git(local, "rev-parse", "HEAD") == old_head
    assert (local / "local.py").exists()


def test_fast_forward_does_not_overwrite_ignored_local_file(tmp_path):
    local, remote = setup_repositories(tmp_path)
    (local / ".gitignore").write_text("local-data.txt\n", encoding="utf-8")
    stage_files(local)
    commit(local, "Ignore local data")
    push(local)
    second = clone_repository(tmp_path, remote)
    (second / "local-data.txt").write_text("REMOTE SYNTHETIC DATA", encoding="utf-8")
    run_git(second, "add", "-f", "local-data.txt")
    commit(second, "Remote adds colliding file")
    push(second)
    local_data = local / "local-data.txt"
    local_data.write_text("LOCAL SYNTHETIC DATA TO KEEP", encoding="utf-8")
    before = run_git(local, "rev-parse", "HEAD")

    with pytest.raises(GitCommandError):
        prepare_remote_for_push(local, confirm_fast_forward=lambda _: True)

    assert local_data.read_text(encoding="utf-8") == "LOCAL SYNTHETIC DATA TO KEEP"
    assert run_git(local, "rev-parse", "HEAD") == before


def test_remote_changes_after_prepare_cannot_be_overwritten_by_push(tmp_path):
    local, remote = setup_repositories(tmp_path)
    push(local)
    second = clone_repository(tmp_path, remote)
    add_commit(local, "local.py")
    assert prepare_remote_for_push(local) == "ahead"
    add_commit(second, "concurrent.py")
    push(second)
    remote_head = run_git(second, "rev-parse", "HEAD")
    local_head = run_git(local, "rev-parse", "HEAD")
    with pytest.raises(GitCommandError):
        push(local)
    assert run_git(remote, "rev-parse", "main") == remote_head
    assert run_git(local, "rev-parse", "HEAD") == local_head
