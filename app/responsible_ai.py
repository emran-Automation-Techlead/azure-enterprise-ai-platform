"""Responsible AI layer: wraps routing, safety, RAG and human-oversight rules into one traceable response.

Flow:  question -> redact secrets -> router -> safety checkers -> (refuse | RAG | general answer)
       -> output scan -> human-review decision -> ChatResponse (with metadata)

The risk classification is a "Portfolio demonstration risk classification", not a certified framework.
"""
import logging

from app import llm, rag, router
from app.models import ChatResponse, Source
from app.safety import SafetyChecker, default_checker, redact, scan_output

log = logging.getLogger("responsible-ai")
RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

PRIVACY_NOTICE = "Please avoid sharing passwords, authentication tokens, or other sensitive credentials."

REFUSALS = {
    "PROMPT_INJECTION": "I can't do that. I follow my configured policies and I can't reveal or change my instructions. "
    "I'm happy to help with an enterprise IT question instead.",
    "CREDENTIAL_REQUEST": "I can't provide or look up passwords, keys, tokens or other credentials. "
    "If someone needs access, they should use the self-service reset portal or contact the service desk, who will verify identity first.",
    "SECURITY_BYPASS": "I can't help bypass enterprise security controls. If a control is blocking legitimate work, "
    "raise it with Security Operations, who can authorise a documented, time-limited exception. Human review is recommended.",
    "HARMFUL_REQUEST": "I can't help with that request. This assistant supports enterprise IT troubleshooting and knowledge questions only.",
    "CONTENT_SAFETY": "I can't respond to that message. Please rephrase it as an enterprise IT question.",
}
OUT_OF_SCOPE_MSG = (
    "This assistant is designed for enterprise IT incident and knowledge questions, so I can't help with that. "
    "I don't have any enterprise information on that topic."
)
GENERAL_SYSTEM = (
    "You are an IT assistant. Answer the general technology question briefly (under 120 words). "
    "Begin with: 'General knowledge (not from the enterprise knowledge base):'. Do not claim anything about the company's own systems or policies."
)


def _raise(current: str, new: str) -> str:
    return new if RISK_ORDER.index(new) > RISK_ORDER.index(current) else current


def _refusal_text(flags: list[str]) -> str:
    for key in ("PROMPT_INJECTION", "SECURITY_BYPASS", "CREDENTIAL_REQUEST", "HARMFUL_REQUEST"):
        if key in flags:
            return REFUSALS[key]
    return REFUSALS["CONTENT_SAFETY"]


def handle(question: str, checker: SafetyChecker | None = None) -> ChatResponse:
    checker = checker or default_checker()
    safe_question = redact(question)  # nothing credential-like goes to the model or the logs
    decision = router.route(question)
    safety = checker.check(safe_question)

    flags = sorted(set(decision.safety_flags + safety.flags))
    risk = decision.risk_level
    blocked = decision.blocked or safety.blocked
    if safety.blocked:
        risk = _raise(risk, "HIGH")
    reasons: list[str] = list(decision.reasons) + list(safety.details)
    tokens = decision.tokens
    sources: list[Source] = []
    grounded, score, conflict, refused = False, 0.0, False, False
    query_type = decision.query_type
    explanation = ""

    if blocked:
        answer, refused, query_type = _refusal_text(flags), True, "OUT_OF_SCOPE"
        explanation = "The request was stopped by safety rules before any enterprise search or model answer."
    elif query_type == "OUT_OF_SCOPE":
        answer, refused = OUT_OF_SCOPE_MSG, True
        explanation = "The question was classified as outside enterprise IT, so no search or model answer was produced."
    elif query_type == "GENERAL":
        r = llm.chat([{"role": "system", "content": GENERAL_SYSTEM}, {"role": "user", "content": safe_question}])
        answer, tokens = r["text"], tokens + r["tokens"]
        explanation = "General technology question answered without enterprise documents, so it is not grounded."
    else:  # INCIDENT or KNOWLEDGE -> RAG
        result = rag.answer(safe_question)
        answer, grounded, score = result.answer, result.grounded, result.grounding_score
        conflict, tokens = result.conflict_detected, tokens + result.tokens
        sources = [Source(**s) for s in result.sources]
        if result.invalid_citations:
            flags.append("UNSUPPORTED_CITATION")
        explanation = (
            f"Response based on {len(sources)} retrieved enterprise document(s)."
            if grounded
            else f"No sufficiently relevant enterprise document was found. ({result.fallback_reason})"
        )

    # Output safety: never let leaked instructions or secret-like text out.
    out_flags = scan_output(answer)
    if out_flags:
        flags.extend(out_flags)
        answer, grounded, sources = "I can't share that content. Please ask an enterprise IT question.", False, []
        risk = _raise(risk, "HIGH")
        reasons.append("The generated answer was withheld by the output safety scan.")

    # Human oversight: decide when a person should review.
    review: list[str] = []
    if RISK_ORDER.index(risk) >= RISK_ORDER.index("MEDIUM"):
        review.append(f"Risk level {risk}.")
    if conflict:
        review.append("Knowledge-base sources conflict with each other.")
    if query_type in ("INCIDENT", "KNOWLEDGE") and not blocked and not grounded:
        review.append("Insufficient evidence in the knowledge base.")
    if "SENSITIVE_DATA_IN_INPUT" in flags:
        review.append("The message contained sensitive information.")
    if "UNSUPPORTED_CITATION" in flags:
        review.append("The answer cited a document that was not retrieved.")
    if "SECURITY_CONTROL_CHANGE" in flags or "SECURITY_BYPASS" in flags:
        review.append("Security-sensitive request.")

    if sources:
        disclosure = "This response was generated by AI using enterprise knowledge sources."
    elif query_type == "GENERAL" and not refused:
        disclosure = "This response was generated by AI from general knowledge. No enterprise knowledge sources were used."
    else:
        disclosure = "This response was generated by AI. No enterprise knowledge sources were used."

    notice = PRIVACY_NOTICE if "SENSITIVE_DATA_IN_INPUT" in flags or "CREDENTIAL_REQUEST" in flags else ""
    if review:
        answer = answer.rstrip() + "\n\n**Human review recommended.**"

    log.info(  # safe telemetry only: no question text, no answer text
        "chat type=%s risk=%s grounded=%s review=%s flags=%s sources=%d tokens=%d",
        query_type, risk, grounded, bool(review), flags, len(sources), tokens,
    )
    return ChatResponse(
        answer=answer,
        sources=sources,
        query_type=query_type,
        grounded=grounded,
        grounding_score=score,
        risk_level=risk,
        human_review_required=bool(review),
        human_review_reasons=review,
        safety_flags=flags,
        conflict_detected=conflict,
        refused=refused,
        privacy_notice=notice,
        ai_disclosure_text=disclosure,
        explanation=explanation,
        tokens_used=tokens,
    )
