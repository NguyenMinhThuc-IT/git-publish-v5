"""Tests for V4.5 repository detection and reduced prompts."""

import pytest

from src.gitpublish import cli
from src.gitpublish.github import GitHubError


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/example/MyRepo.git",
        "git@github.com:example/MyRepo.git",
        "ssh://git@github.com/example/MyRepo.git",
    ],
)
def test_detect_existing_repo(tmp_path, monkeypatch, remote):
    monkeypatch.setattr(
        cli, "get_remote_url", lambda _: remote
    )
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )

    assert (
        cli.detect_repo_name_from_origin(tmp_path)
        == "MyRepo"
    )


def test_no_origin(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cli, "get_remote_url", lambda _: None
    )

    assert cli.detect_repo_name_from_origin(tmp_path) is None


def test_different_github_owner_is_blocked(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        cli, "get_remote_url",
        lambda _: "https://github.com/other/demo.git",
    )
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )

    with pytest.raises(GitHubError, match="tài khoản"):
        cli.detect_repo_name_from_origin(tmp_path)


def test_existing_repo_skips_name_prompt(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        cli, "get_remote_url",
        lambda _: "https://github.com/example/demo.git",
    )
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )

    def unexpected_prompt(_):
        raise AssertionError("Không được hỏi lại tên repo")

    monkeypatch.setattr(cli, "ask_text", unexpected_prompt)
    monkeypatch.setattr(
        cli, "choose_repository_visibility",
        lambda _: False,
    )
    monkeypatch.setattr(
        cli, "ask_yes_no",
        lambda question, default=False: default,
    )

    assert cli.get_user_options(tmp_path) == (
        "demo", False, True, False
    )
