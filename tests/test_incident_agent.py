"""Incident agent tests with retrieval and the model faked, so they run offline."""
import json

import pytest

from app import llm, rag
from app.agents import incident_agent

DOCS = [
    {"id": "DOC-001", "title": "VPN Runbook", "category": "runbook", "content": "Check RADIUS.", "last_reviewed": "2025"},
    {"id": "DOC-002", "title": "MFA Troubleshooting", "category": "runbook", "content": "Check NPS.", "last_reviewed": "2025"},
]


def retrieval(monkeypatch, ok=True):
    result = (
        rag.Retrieval(docs=DOCS, relevance={"DOC-001": 0.8, "DOC-002": 0.7}, top_score=0.8)
        if ok
        else rag.Retrieval(top_score=0.3, fallback_reason="below threshold")
    )
    monkeypatch.setattr(rag, "retrieve", lambda q: result)


def model(monkeypatch, findings):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: {"text": json.dumps({"findings": findings}), "tokens": 40})


def raises(exc):
    def _f(*a, **k):
        raise exc
    return _f


def test_labels_known_inference_unknown(monkeypatch):
    retrieval(monkeypatch)
    model(monkeypatch, [
        {"text": "Check RADIUS [DOC-001]", "basis": "KNOWN_FROM_SOURCES", "source_ids": ["DOC-001"]},
        {"text": "Possibly a certificate expiry", "basis": "INFERENCE", "source_ids": []},
        {"text": "Number of affected users is not stated", "basis": "UNKNOWN", "source_ids": []},
    ])
    m = incident_agent.run("VPN auth failing")
    assert m.status == "success" and m.grounded
    assert [f.basis for f in m.findings] == ["KNOWN_FROM_SOURCES", "INFERENCE", "UNKNOWN"]
    assert [s.id for s in m.sources] == ["DOC-001"]


def test_fake_source_is_downgraded_to_inference(monkeypatch):
    retrieval(monkeypatch)
    model(monkeypatch, [{"text": "Do X [DOC-999]", "basis": "KNOWN_FROM_SOURCES", "source_ids": ["DOC-999"]}])
    m = incident_agent.run("VPN failing")
    assert m.findings[0].basis == "INFERENCE" and not m.grounded and m.status == "no_knowledge"


def test_weak_retrieval_never_calls_model(monkeypatch):
    retrieval(monkeypatch, ok=False)
    monkeypatch.setattr(llm, "chat", raises(AssertionError("model must not be called")))
    m = incident_agent.run("unknown incident")
    assert m.status == "no_knowledge" and m.summary == "NO_RELEVANT_KNOWLEDGE"


def test_model_outage_returns_error(monkeypatch):
    retrieval(monkeypatch)
    monkeypatch.setattr(llm, "chat", raises(llm.LLMError("down")))
    assert incident_agent.run("VPN failing").status == "error"


def test_bad_json_returns_error(monkeypatch):
    retrieval(monkeypatch)
    monkeypatch.setattr(llm, "chat", lambda *a, **k: {"text": "oops", "tokens": 1})
    assert incident_agent.run("VPN failing").status == "error"
