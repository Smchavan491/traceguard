from types import SimpleNamespace

import httpx
import pytest
from openai import RateLimitError

from app.llm import ask_llm, build_messages

def make_client(outcomes):
    """A fake client. Each call returns the next outcome: text, or an exception to raise."""
    calls = {"n": 0}

    def create(**kwargs):
        outcome = outcomes[calls["n"]]
        calls["n"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        message = SimpleNamespace(content=outcome)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client, calls


def rate_limit_error():
    response = httpx.Response(429, request=httpx.Request("POST", "http://test"))
    return RateLimitError("rate limited", response=response, body=None)


def test_success_on_first_try():
    client, calls = make_client(["hello"])
    assert ask_llm("sys", "user", client=client, sleep=lambda s: None) == "hello"
    assert calls["n"] == 1


def test_retries_then_succeeds():
    client, calls = make_client([rate_limit_error(), rate_limit_error(), "ok"])
    waits = []
    assert ask_llm("sys", "user", client=client, sleep=waits.append) == "ok"
    assert calls["n"] == 3
    assert waits == [20, 40]


def test_gives_up_after_max_retries():
    client, calls = make_client([rate_limit_error()] * 5)
    with pytest.raises(RateLimitError):
        ask_llm("sys", "user", client=client, max_retries=3, sleep=lambda s: None)
    assert calls["n"] == 3  # tried exactly 3 times, never loops forever

def test_build_messages_puts_system_first():
    messages = build_messages("rules here", "checkout is slow")   # run the function

    assert messages[0]["role"] == "system"       # check the first message's role
    assert messages[0]["content"] == "rules here"  # check what it says