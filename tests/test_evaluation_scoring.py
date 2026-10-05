"""Checks the evaluation harness itself offline: case file is complete and the new routing / source scores behave."""
import json

from evaluation.evaluate import CASES_FILE, DIMENSIONS, score_case

CASES = json.loads(CASES_FILE.read_text(encoding="utf-8"))
BY_ID = {c["id"][:4]: c for c in CASES}


def response(**kw):
    base = dict(answer="a", query_type="INCIDENT", risk_level="LOW", grounded=True, sources=[{"id": "DOC-001", "title": "VPN"}],
                conflict_detected=False, refused=False, safety_flags=[], privacy_notice="", ai_disclosure=True,
                ai_disclosure_text="AI", human_review_required=False,
                agents_used=["orchestrator", "incident_agent", "responsible_ai_agent"])
    return {**base, **kw}


def test_every_case_declares_the_new_fields():
    assert len(CASES) == 12
    for c in CASES:
        assert isinstance(c["expected_agents"], list) and all(isinstance(a, list) for a in c["expected_agents"]), c["id"]
        for f in ("expected_risk", "expected_grounding", "expected_human_review", "expected_behavior"):
            assert f in c, (c["id"], f)


def test_dimensions_include_routing_and_source_retrieval():
    assert "routing" in DIMENSIONS and "source_retrieval" in DIMENSIONS


def test_routing_passes_on_accepted_set_and_fails_otherwise():
    case = BY_ID["TC01"]
    assert score_case(case, response(), [response()])["routing"] is True
    wrong = response(agents_used=["orchestrator", "general_agent", "responsible_ai_agent"])
    assert score_case(case, wrong, [wrong])["routing"] is False
    no_review = response(agents_used=["orchestrator", "incident_agent"])
    assert score_case(case, no_review, [no_review])["routing"] is False


def test_multi_agent_case_requires_both_agents():
    case = BY_ID["TC11"]
    both = response(agents_used=["orchestrator", "incident_agent", "knowledge_agent", "responsible_ai_agent"])
    one = response()
    assert score_case(case, both, [both])["routing"] is True
    assert score_case(case, one, [one])["routing"] is False


def test_blocked_case_expects_no_worker_agent():
    case = BY_ID["TC06"]
    ok = response(agents_used=["orchestrator", "responsible_ai_agent"])
    assert score_case(case, ok, [ok])["routing"] is True


def test_source_retrieval_scored_only_when_documents_expected():
    assert score_case(BY_ID["TC01"], response(), [response()])["source_retrieval"] is True
    miss = response(sources=[{"id": "DOC-099", "title": "x"}])
    assert score_case(BY_ID["TC01"], miss, [miss])["source_retrieval"] is False
    assert score_case(BY_ID["TC05"], response(), [response()])["source_retrieval"] is None


def test_single_agent_responses_skip_routing():
    r = response(agents_used=[])
    assert score_case(BY_ID["TC01"], r, [r])["routing"] is None
