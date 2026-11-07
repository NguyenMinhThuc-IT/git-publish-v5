"""Tests for Y/n confirmation prompts."""

import pytest

from src.gitpublish.cli import ask_yes_no


@pytest.mark.parametrize(
    "answer, default, expected",
    [
        ("y", False, True),
        ("yes", False, True),
        ("n", True, False),
        ("no", True, False),
        ("", True, True),
        ("", False, False),
    ],
)
def test_yes_no_choices(monkeypatch, answer, default, expected):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert ask_yes_no("Continue?", default=default) is expected


def test_invalid_answer_asks_again(monkeypatch):
    answers = iter(["abc", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert ask_yes_no("Continue?") is True
