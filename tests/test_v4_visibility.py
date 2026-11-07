"""Tests for existing GitHub repository visibility."""

import pytest
from src.gitpublish import cli
from src.gitpublish.github import GitHubError


@pytest.mark.parametrize(
    "github_private, expected_public",
    [("true", False), ("false", True)],
)
def test_existing_repository_visibility(
    monkeypatch, github_private, expected_public
):
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )
    monkeypatch.setattr(
        cli, "get_repository_url",
        lambda owner, name: "https://github.com/example/demo",
    )
    monkeypatch.setattr(
        cli, "run_gh",
        lambda *args: github_private,
    )

    def must_not_prompt():
        raise AssertionError(
            "Repository đã tồn tại không được hỏi visibility."
        )

    monkeypatch.setattr(
        cli, "choose_visibility", must_not_prompt
    )

    assert (
        cli.choose_repository_visibility("demo")
        is expected_public
    )


def test_new_repository_asks_visibility(monkeypatch):
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )
    monkeypatch.setattr(
        cli, "get_repository_url",
        lambda owner, name: None,
    )
    monkeypatch.setattr(
        cli, "choose_visibility", lambda: False
    )

    assert cli.choose_repository_visibility("new-demo") is False


def test_invalid_visibility_is_rejected(monkeypatch):
    monkeypatch.setattr(
        cli, "get_github_owner", lambda: "example"
    )
    monkeypatch.setattr(
        cli, "get_repository_url",
        lambda owner, name: "https://github.com/example/demo",
    )
    monkeypatch.setattr(
        cli, "run_gh", lambda *args: "unknown"
    )

    with pytest.raises(GitHubError):
        cli.choose_repository_visibility("demo")
