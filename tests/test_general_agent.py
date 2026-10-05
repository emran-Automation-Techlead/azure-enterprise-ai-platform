"""General agent tests with the model faked, so they run offline."""
from app import llm
from app.agents import general_agent


def test_answer_is_labelled_and_never_grounded(monkeypatch):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: {"text": "Cloud computing is on-demand IT.", "tokens": 20})
    m = general_agent.run("Explain what cloud computing is.")
    assert m.answer_kind == "GENERAL_AI_RESPONSE" and not m.grounded and m.sources == []
    assert m.findings[0].text.startswith(general_agent.PREFIX)
    assert m.findings[0].basis == "INFERENCE"


def test_existing_prefix_is_not_duplicated(monkeypatch):
    text = f"{general_agent.PREFIX} Containers share a kernel."
    monkeypatch.setattr(llm, "chat", lambda *a, **k: {"text": text, "tokens": 5})
    assert general_agent.run("containers vs VMs").findings[0].text.count(general_agent.PREFIX) == 1


def test_outage_returns_error(monkeypatch):
    def down(*a, **k):
        raise llm.LLMError("down")
    monkeypatch.setattr(llm, "chat", down)
    assert general_agent.run("what is DNS").status == "error"
