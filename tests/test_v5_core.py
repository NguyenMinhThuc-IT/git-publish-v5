"""Offline regressions for V5; Git writes only to pytest temporary repositories."""

import subprocess
from types import SimpleNamespace

import pytest

from src.gitpublish import cli, git, github, security


@pytest.fixture
def repo(tmp_path):
    project = tmp_path / "dự án có khoảng trắng"
    project.mkdir()
    git.initialize_git(project)
    git.run_git(project, "config", "user.name", "Offline Test")
    git.run_git(project, "config", "user.email", "test@example.invalid")
    return project


def add_commit(repo, name="main.py"):
    (repo / name).write_text("# synthetic test data\n", encoding="utf-8")
    git.stage_files(repo)
    git.commit(repo, "Offline test")


@pytest.mark.parametrize("remote", [
    "https://github.com/example/Demo.git",
    "git@github.com:example/Demo.git",
    "ssh://git@github.com/example/Demo.git/",
])
def test_reuse_repository_preserves_origin(repo, monkeypatch, remote):
    git.add_remote(repo, remote)
    monkeypatch.setattr(github, "get_github_owner", lambda: "example")
    monkeypatch.setattr(github, "get_repository_url", lambda *a: "https://github.com/example/Demo")
    monkeypatch.setattr(github, "run_gh", lambda *a, **k: pytest.fail("Must not create repo"))
    assert github.create_github_repo(repo, "Demo", False).endswith("/Demo")
    assert git.get_remote_url(repo) == remote


def test_mismatched_remote_blocks_before_github_creation(repo, monkeypatch):
    git.add_remote(repo, "https://github.com/other/demo.git")
    monkeypatch.setattr(github, "get_github_owner", lambda: "example")
    monkeypatch.setattr(github, "get_repository_url", lambda *a: pytest.fail("Unexpected lookup"))
    with pytest.raises(github.GitHubError, match="repository khác"):
        github.create_github_repo(repo, "demo", False)
    assert git.get_remote_url(repo).endswith("other/demo.git")


@pytest.mark.parametrize("setting", ["pushurl", "url"])
def test_multiple_or_distinct_push_urls_blocked(repo, setting):
    git.add_remote(repo, "https://github.com/example/demo.git")
    git.run_git(repo, "config", "--add", f"remote.origin.{setting}", "https://github.com/other/demo.git")
    with pytest.raises(git.GitCommandError, match="URL"):
        git.get_remote_url(repo)


@pytest.mark.parametrize("url", [
    "https://github.com.evil.invalid/example/demo",
    "https://example:synthetic@github.com/example/demo",
    "https://github.com/example/demo?token=synthetic",
    "file:///tmp/demo", "git@other.invalid:example/demo",
])
def test_unsupported_remote_is_rejected(url):
    with pytest.raises(github.GitHubError):
        github.normalize_remote(url)


@pytest.mark.parametrize("message", ["network unavailable", "HTTP 401", "HTTP 403", "HTTP 500"])
def test_lookup_failure_is_not_missing_repository(monkeypatch, message):
    def fail(*args, **kwargs):
        raise github.GitHubError(message)
    monkeypatch.setattr(github, "run_gh", fail)
    with pytest.raises(github.GitHubError, match=message):
        github.get_repository_url("example", "demo")


def test_only_api_404_means_missing_repository(monkeypatch):
    monkeypatch.setattr(github.shutil, "which", lambda _: "/fake/gh")
    monkeypatch.setattr(github.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=1, stdout="", stderr="gh: Not Found (HTTP 404)"))
    assert github.get_repository_url("example", "demo") is None
    with pytest.raises(github.GitHubError):
        github.run_gh("auth", "status")


@pytest.mark.parametrize("module,runner,error", [
    (git, "run_git", git.GitCommandError),
    (github, "run_gh", github.GitHubError),
])
def test_subprocess_timeout_is_reported(tmp_path, monkeypatch, module, runner, error):
    monkeypatch.setattr(github.shutil, "which", lambda _: "/fake/gh")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("synthetic", 1)
    monkeypatch.setattr(module.subprocess, "run", timeout)
    with pytest.raises(error, match="thời gian"):
        getattr(module, runner)(tmp_path, "status") if module is git else github.run_gh("api", "user")


def test_git_probe_does_not_hide_timeout(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise git.GitCommandError("timeout")
    monkeypatch.setattr(git, "run_git", fail)
    with pytest.raises(git.GitCommandError, match="timeout"):
        git.is_git_repository(tmp_path)
    with pytest.raises(git.GitCommandError, match="timeout"):
        git.has_commits(tmp_path)


@pytest.mark.parametrize("state", ["detached", "subdirectory"])
def test_cli_blocks_invalid_worktree_before_auth_or_writes(repo, monkeypatch, state):
    add_commit(repo)
    target = repo
    if state == "detached":
        git.run_git(repo, "checkout", "--detach")
    else:
        target = repo / "subdir"
        target.mkdir()
    before = git.run_git(repo, "status", "--porcelain")
    monkeypatch.chdir(target)
    monkeypatch.setattr(cli, "check_requirements", lambda: None)
    monkeypatch.setattr(cli, "check_github_login", lambda: pytest.fail("Auth must not run"))
    with pytest.raises(git.GitCommandError):
        cli.main()
    assert git.run_git(repo, "status", "--porcelain") == before


def test_unicode_and_whitespace_paths_roundtrip(repo):
    name = "tệp tiếng Việt có khoảng trắng.py"
    add_commit(repo, name)
    (repo / name).write_text("# modified\n", encoding="utf-8")
    git.stage_files(repo)
    assert git.get_staged_files(repo) == [f"M\t{name}"]
    git.commit(repo, "Thay đổi tiếng Việt")
    assert not git.has_staged_changes(repo)


def test_deleted_secret_is_discovered_and_blocks(repo):
    add_commit(repo, ".env")
    git.run_git(repo, "rm", ".env")
    git.commit(repo, "Remove synthetic file")
    assert not (repo / ".env").exists()
    detected = security.scan_git_sensitive_paths(repo)
    assert repo / ".env" in detected
    with pytest.raises(RuntimeError, match="lịch sử Git"):
        security.preflight_sensitive_files(repo, detected)


def test_missing_staged_secret_is_discovered(repo):
    secret = repo / ".env"
    secret.write_text("SYNTHETIC=1", encoding="utf-8")
    git.stage_files(repo)
    secret.unlink()
    assert secret in security.scan_git_sensitive_paths(repo)


@pytest.mark.parametrize("name", ["bí mật [1].key", "!private.key", "#private.key", "space .key"])
def test_literal_sensitive_paths_do_not_untrack_other_files(repo, name):
    secret = repo / name
    other = repo / "bí mật 1.key"
    secret.write_text("synthetic", encoding="utf-8")
    other.write_text("synthetic", encoding="utf-8")
    git.stage_files(repo)
    security.ensure_gitignore(repo, [secret])
    git.stage_files(repo)
    tracked = git.run_git(repo, "ls-files", "-z").split(chr(0))
    assert name not in tracked
    assert other.name in tracked
    assert secret.read_text(encoding="utf-8") == "synthetic"


def test_gitignore_symlink_is_not_written(repo, tmp_path):
    target = tmp_path / "untouched"
    target.write_text("original", encoding="utf-8")
    try:
        (repo / ".gitignore").symlink_to(target)
    except OSError:
        pytest.skip("Symlinks unavailable")
    with pytest.raises(RuntimeError, match="symlink"):
        security.ensure_gitignore(repo, [repo / ".env"])
    assert target.read_text(encoding="utf-8") == "original"


def test_rejected_push_preserves_local_and_remote_history(repo, tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    git.add_remote(repo, str(remote))
    add_commit(repo)
    git.push(repo)
    second = tmp_path / "second"
    subprocess.run(["git", "clone", "--branch", "main", str(remote), str(second)], check=True, capture_output=True)
    git.run_git(second, "config", "user.name", "Offline Test")
    git.run_git(second, "config", "user.email", "test@example.invalid")
    add_commit(second, "remote.py")
    git.push(second)
    add_commit(repo, "local.py")
    old_head = git.run_git(repo, "rev-parse", "HEAD")
    remote_head = git.run_git(remote, "rev-parse", "main")
    with pytest.raises(git.GitCommandError):
        git.push(repo)
    assert git.run_git(repo, "rev-parse", "HEAD") == old_head
    assert git.run_git(remote, "rev-parse", "main") == remote_head


def prepare_cli(repo, monkeypatch):
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "check_requirements", lambda: None)
    monkeypatch.setattr(cli, "check_github_login", lambda: None)
    monkeypatch.setattr(cli, "get_user_options", lambda _: ("demo", False, True, True))
    monkeypatch.setattr(cli, "choose_sensitive_files", lambda files, _: files)


def test_cancel_before_commit_does_not_create_remote(repo, monkeypatch):
    (repo / "main.py").write_text("# offline", encoding="utf-8")
    prepare_cli(repo, monkeypatch)
    monkeypatch.setattr(cli, "ask_yes_no", lambda *a, **k: False)
    monkeypatch.setattr(cli, "create_github_repo", lambda *a: pytest.fail("Must not create remote"))
    assert cli.main() == 0
    assert not git.has_commits(repo)
    assert git.has_staged_changes(repo)


def test_push_failure_never_reports_success_or_runs_success_actions(repo, monkeypatch, capsys):
    add_commit(repo)
    prepare_cli(repo, monkeypatch)
    monkeypatch.setattr(cli, "ask_yes_no", lambda *a, **k: True)
    monkeypatch.setattr(cli, "create_github_repo", lambda *a: "https://github.com/example/demo")
    monkeypatch.setattr(cli, "assert_repository_visibility", lambda *a: None)
    monkeypatch.setattr(cli, "prepare_remote_for_push", lambda *a, **k: "ahead")
    def rejected(*args):
        raise git.GitCommandError("push rejected")
    monkeypatch.setattr(cli, "push", rejected)
    monkeypatch.setattr(cli, "copy_to_clipboard", lambda *a: pytest.fail("Must not copy"))
    monkeypatch.setattr(cli.webbrowser, "open", lambda *a: pytest.fail("Must not open"))
    with pytest.raises(SystemExit) as caught:
        cli.run()
    assert caught.value.code == 1
    assert "PUBLISH THÀNH CÔNG" not in capsys.readouterr().out


@pytest.mark.parametrize("exception,code", [(KeyboardInterrupt, 130), (EOFError, 1)])
def test_interrupted_input_exits_cleanly(monkeypatch, capsys, exception, code):
    def interrupt():
        raise exception()
    monkeypatch.setattr(cli, "main", interrupt)
    with pytest.raises(SystemExit) as caught:
        cli.run()
    assert caught.value.code == code
    assert "Lỗi không mong đợi" not in capsys.readouterr().out


@pytest.mark.parametrize("result", ["unknown", "", "false"])
def test_visibility_fails_closed(monkeypatch, result):
    monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=result, stderr=""))
    with pytest.raises(github.GitHubError):
        cli.assert_repository_visibility("https://github.com/example/demo", False)


def test_new_secret_from_remote_blocks_before_push(repo, monkeypatch):
    add_commit(repo)
    prepare_cli(repo, monkeypatch)
    monkeypatch.setattr(cli, "ask_yes_no", lambda *a, **k: True)
    monkeypatch.setattr(cli, "create_github_repo", lambda *a: "https://github.com/example/demo")
    monkeypatch.setattr(cli, "assert_repository_visibility", lambda *a: None)
    def synchronize(*args, **kwargs):
        add_commit(repo, "server.key")
        return "fast_forwarded"
    monkeypatch.setattr(cli, "prepare_remote_for_push", synchronize)
    monkeypatch.setattr(cli, "push", lambda *a: pytest.fail("Must not push"))
    with pytest.raises(RuntimeError, match="đang được Git theo dõi"):
        cli.main()


def test_scan_permission_error_blocks_instead_of_silently_skipping(repo, monkeypatch):
    def walk(*args, **kwargs):
        kwargs["onerror"](PermissionError("synthetic permission error"))
        return iter(())
    monkeypatch.setattr(security.os, "walk", walk)
    with pytest.raises(RuntimeError, match="quét đầy đủ"):
        security.scan_project(repo)


def test_gitignore_invalid_utf8_is_not_corrupted(repo):
    original = b"original\xff\n"
    (repo / ".gitignore").write_bytes(original)
    with pytest.raises(UnicodeDecodeError):
        security.ensure_gitignore(repo, [repo / ".env"])
    assert (repo / ".gitignore").read_bytes() == original


def test_unexpected_github_response_never_adds_origin(repo, monkeypatch):
    monkeypatch.setattr(github, "get_github_owner", lambda: "example")
    monkeypatch.setattr(github, "get_repository_url", lambda *a: "https://github.com/other/demo")
    with pytest.raises(github.GitHubError, match="khác đích"):
        github.create_github_repo(repo, "demo", False)
    assert git.get_remote_url(repo) is None


def test_cli_success_and_repeat_without_empty_commit(repo, tmp_path, monkeypatch, capsys):
    """Actual stage/commit/fetch/push; only GitHub/GUI boundaries are replaced."""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    (repo / "tệp dự án.py").write_text("# synthetic project\n", encoding="utf-8")
    prepare_cli(repo, monkeypatch)
    monkeypatch.setattr(cli, "ask_yes_no", lambda *a, **k: True)
    monkeypatch.setattr(cli, "ask_text", lambda *a: "Commit tiếng Việt")
    def create(*args):
        if git.get_remote_url(repo) is None:
            git.add_remote(repo, str(remote))
        return "https://github.com/example/demo"
    monkeypatch.setattr(cli, "create_github_repo", create)
    monkeypatch.setattr(cli, "assert_repository_visibility", lambda *a: None)
    monkeypatch.setattr(cli, "copy_to_clipboard", lambda *a: False)
    monkeypatch.setattr(cli.webbrowser, "open", lambda *a: False)
    assert cli.main() == 0
    first = git.run_git(repo, "rev-parse", "HEAD")
    assert git.run_git(remote, "rev-parse", "main") == first
    monkeypatch.setattr(cli, "commit", lambda *a: pytest.fail("Must not create empty commit"))
    monkeypatch.setattr(cli, "push", lambda *a: pytest.fail("Up-to-date repo must not push"))
    assert cli.main() == 0
    assert git.run_git(repo, "rev-parse", "HEAD") == first
    assert capsys.readouterr().out.count("PUBLISH THÀNH CÔNG") == 2


def test_bare_repository_is_blocked_without_reinitializing(tmp_path, monkeypatch):
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)
    before = {str(p.relative_to(bare)): p.read_bytes() for p in bare.rglob("*") if p.is_file()}
    monkeypatch.chdir(bare)
    monkeypatch.setattr(cli, "check_requirements", lambda: None)
    monkeypatch.setattr(cli, "check_github_login", lambda: pytest.fail("Auth must not run"))
    with pytest.raises(git.GitCommandError, match="Bare repository"):
        cli.main()
    assert {str(p.relative_to(bare)): p.read_bytes() for p in bare.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("directory", [".aws", ".ssh", ".gnupg"])
def test_credential_directories_protected_without_reading_contents(repo, directory):
    private = repo / directory
    private.mkdir()
    (private / "credentials").write_text("SYNTHETIC DATA", encoding="utf-8")
    assert private in security.scan_project(repo)
    git.stage_files(repo)
    git.commit(repo, "Synthetic private directory")
    git.run_git(repo, "rm", "-r", directory)
    git.commit(repo, "Remove synthetic directory")
    assert private in security.scan_git_sensitive_paths(repo)
    with pytest.raises(RuntimeError, match="lịch sử Git"):
        security.preflight_sensitive_files(repo, [private])


@pytest.mark.parametrize("name", [".netrc", ".npmrc", ".pypirc"])
def test_authentication_dotfiles_are_sensitive(repo, name):
    private = repo / name
    private.write_text("SYNTHETIC DATA", encoding="utf-8")
    assert private in security.scan_project(repo)
