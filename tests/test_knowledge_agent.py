"""Knowledge agent tests with the RAG pipeline faked, so they run offline."""
from app import rag
from app.agents import knowledge_agent
from app.search import SearchError


def test_grounded_answer_carries_sources(monkeypatch):
    monkeypatch.setattr(rag, "answer", lambda q: rag.RAGResult(
        answer="Reset via portal [DOC-003]", grounded=True, grounding_score=0.82, tokens=50,
        sources=[{"id": "DOC-003", "title": "Password Policy", "category": "policy", "relevance": 0.82}]))
    m = knowledge_agent.run("password reset policy?")
    assert m.status == "success" and m.grounded and m.answer_kind == "ENTERPRISE_GROUNDED_RESPONSE"
    assert m.sources[0].id == "DOC-003" and m.findings[0].basis == "KNOWN_FROM_SOURCES"
    assert m.findings[0].source_ids == ["DOC-003"]


def test_nothing_found_returns_no_relevant_knowledge(monkeypatch):
    monkeypatch.setattr(rag, "answer", lambda q: rag._fallback("below threshold", 0.3))
    m = knowledge_agent.run("tell me about an unknown incident")
    assert m.status == "no_knowledge" and m.summary == "NO_RELEVANT_KNOWLEDGE" and not m.grounded
    assert m.sources == [] and m.findings[0].basis == "UNKNOWN"


def test_search_outage_does_not_raise(monkeypatch):
    def down(q):
        raise SearchError("down")
    monkeypatch.setattr(rag, "answer", down)
    m = knowledge_agent.run("anything")
    assert m.status == "error" and not m.grounded and m.findings[0].basis == "UNKNOWN"
