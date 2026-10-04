# AI System Card

**System name:** Enterprise Azure AI Platform
**Purpose:** Enterprise IT knowledge and incident assistance.
**Version:** portfolio MVP.

## Intended users
IT support engineers and enterprise employees.

## Intended use
Knowledge retrieval and troubleshooting assistance, grounded in enterprise documents, with citations.

## Not intended for
- autonomous production changes
- employment decisions
- financial decisions
- medical decisions
- legal decisions
- safety-critical decisions
- bypassing security controls

## How it works (summary)
Route → hybrid retrieval (Azure AI Search) → grounding gate → grounded generation (Azure OpenAI `gpt-4.1-mini`) → Responsible AI review → response with sources, risk level, human-review status and AI disclosure.

## Human oversight
High-risk responses, conflicting sources, insufficient evidence, sensitive input and security-sensitive requests set `human_review_required` and show "Human review recommended". The assistant gives advice only; it cannot take actions.

## Data
**Synthetic enterprise data only** (20 invented Markdown documents). No real employer, customer or personal data.

## Evaluation
Portfolio Responsible AI Evaluation: 10 cases × 3 runs, 8 dimensions; 35 automated tests (23 offline, 12 live). This does not establish production-level safety.

## Known limitations
- Small corpus (20 documents) and small evaluation set.
- The grounding threshold is a calibration on about 12 questions and is fragile near the boundary.
- Conflicting-source detection depends on the model and is not fully consistent (evaluation case TC09 fails).
- Hybrid ranking can place a loosely related document first.
- Content Safety does not detect prompt injection and can miss calmly worded harmful intent; router and local rules cover part of this gap.
- Redaction of secrets can leave a question too vague to answer.
- No demographic fairness testing; no multilingual support; English only.
- Public Container App URL has no user authentication (a **PRODUCTION ENHANCEMENT**).

## Contact / accountability
Portfolio project by its author; not a supported product.
