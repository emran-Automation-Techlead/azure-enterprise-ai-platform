# Enterprise Azure AI Platform

**Intelligent IT Knowledge, Incident & Responsible AI Assistant**: a RAG application on Azure where Responsible AI, grounding, security, observability and human oversight are *architectural controls around the generative AI layer*, not an afterthought.

![python](https://img.shields.io/badge/python-3.11-blue) ![azure](https://img.shields.io/badge/Azure-OpenAI%20%7C%20AI%20Search%20%7C%20Content%20Safety-0078D4) ![tests](https://img.shields.io/badge/tests-71%20offline%20%2B%2012%20live-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green)

> **Portfolio project with 100% synthetic data.** It demonstrates engineering patterns for responsible AI. It is **not** a certified legal, regulatory, compliance or safety assessment.

![Grounded response with sources and the Responsible AI panel](docs/screenshots/05-rag-grounded-response.png)

## Business Problem
IT organisations keep their knowledge in runbooks, policies and past incidents. A generic chatbot answers confidently from its training data and will invent fixes and policies that sound right, which is dangerous for things like security controls and production changes. Engineers need answers **from the company's own documents**, with sources, and a clear signal when a human should step in.

## Solution
An assistant that routes each question, retrieves enterprise documents from Azure AI Search, answers **only** from them with Azure OpenAI, and then passes the result through a Responsible AI layer that checks safety, grounding and conflicts and decides whether a human should review.

## Multi-Agent Architecture
Version 2 upgrades the pipeline below into **multi-agent orchestration**. The original behaviour is kept: set `AGENT_MODE=single` to restore it. Full design: [docs/multi-agent-architecture.md](docs/multi-agent-architecture.md).

```
                    USER
                      │
                      ▼
           ┌─────────────────────┐
           │  ORCHESTRATOR AGENT │  intent + delegation (rules first, then one model call)
           └──────────┬──────────┘
        ┌─────────────┼───────────────┐
        ▼             ▼               ▼
   INCIDENT      KNOWLEDGE/RAG     GENERAL
    AGENT           AGENT           AGENT
        └──────► Azure AI Search ◄──┘   (no search for General)
                      │
                structured AgentMessage results
                      ▼
           ┌─────────────────────┐
           │ RESPONSIBLE AI      │  grounding · safety · risk · privacy ·
           │ REVIEW AGENT        │  unsupported claims · human oversight
           └──────────┬──────────┘
              APPROVED │ HUMAN REVIEW REQUIRED
                      ▼
               FINAL RESPONSE
```

| Agent | Responsibility |
|---|---|
| Orchestrator | Classifies the request, picks one or more agents. Never answers. Blocked requests (injection, credential theft, bypass) stop here with no model call. |
| Incident | Analyses an incident from runbooks; every finding is labelled *From sources*, *Inference* or *Unknown*. |
| Knowledge / RAG | Hybrid retrieval over the enterprise documents; returns source IDs and titles, or `NO_RELEVANT_KNOWLEDGE`. |
| General | General technology questions, labelled `GENERAL_AI_RESPONSE`; can never carry enterprise sources. |
| Responsible AI Review | Independently reviews the combined output; model can only raise risk; returns a structured verdict. |

Agents exchange typed messages (`app/agents/messages.py`). The API response gains `agents_used`, `agent_trace` and `review_reason`, and the Streamlit UI shows an **Agent Workflow** panel. Example: *"VPN authentication is failing for multiple users. What should I check, and should we disable MFA temporarily?"* runs Orchestrator → Incident → Knowledge → Responsible AI, and is expected to come back HIGH risk with human review required.

**Trade-offs:** about 3 to 4 model calls per request instead of about 2, sequential agents add latency, more moving parts. A single agent is the better choice for a narrow single-path assistant.

> **Status:** the multi-agent code, 71 offline tests (model and search faked) and the UI are built. The 12 original live tests and a 12-case live evaluation have been run against Azure (see Evaluation). Live multi-agent screenshots are **pending**; the screenshots below are from the original single-pipeline version.

## Architecture (original single pipeline)
![Architecture](docs/screenshots/01-architecture.png)

```
User → Streamlit → FastAPI → AI Router ─┬─ blocked (injection / credentials / bypass) → fixed refusal
                                         ├─ OUT_OF_SCOPE → scope message
                                         ├─ GENERAL → labelled general answer
                                         └─ INCIDENT / KNOWLEDGE → Azure AI Search (hybrid)
                                              → grounding gate → Azure OpenAI (grounded)
                                         → Responsible AI layer → human-oversight decision → response
Blob Storage → ingestion → Azure AI Search      Key Vault + Managed Identity      Application Insights
Docker → Azure Container Apps
```
Details: [docs/architecture.md](docs/architecture.md) · decisions: [docs/decisions.md](docs/decisions.md)

## AI Workflow
1. **Router** (`app/router.py`): hard rules decide risk and blocking; the model only classifies the query type. Rules can raise risk but never lower it.
2. **Retrieval** (`app/search.py`): hybrid keyword + vector search over 20 synthetic documents.
3. **Grounding gate** (`app/rag.py`): if the best match is weak, **the model is not called**.
4. **Generation**: the model answers only from retrieved documents and cites them `[DOC-001]`.
5. **Responsible AI layer** (`app/responsible_ai.py`): Content Safety, output scan, citation validation, conflict check, risk level, human-review decision.

## RAG
Documents are stored in **Blob Storage**, embedded with `text-embedding-3-small` (1536 dims) and indexed in **Azure AI Search** (HNSW vector field + searchable text + metadata). Each answer returns its sources with relevance.

| Grounded KNOWLEDGE answer | Enterprise knowledge in Blob Storage |
|---|---|
| ![](docs/screenshots/06-knowledge-response.png) | ![](docs/screenshots/04-enterprise-knowledge.png) |

## Responsible AI
Implemented as code. See [docs/responsible-ai.md](docs/responsible-ai.md) and the [AI System Card](docs/ai-system-card.md).

| Principle | How it appears in the product |
|---|---|
| Transparency | AI disclosure banner, query type, sources, grounding status, risk, review status |
| Explainability | Cited documents + a plain explanation line (no chain-of-thought) |
| Privacy | Credentials redacted before model/logs; privacy notice; telemetry never logs text |
| Safety | Router rules + Azure AI Content Safety + local rules + output scan |
| Reliability | Grounding gate: weak retrieval means "not enough information", no model call |
| Accountability | Every response carries traceable metadata |
| Human oversight | `human_review_required` + reasons + "Human review recommended" |
| Fairness | Consistent rules, no user profiling, evaluation scenarios, human oversight (no demographic testing) |

Risk levels (LOW / MEDIUM / HIGH / CRITICAL) are a **portfolio demonstration risk classification**, not a certified framework. `grounding_score` is a simple application-level retrieval-match metric, **not** validated truth.

| Prompt injection blocked | High-risk request → human review | Sensitive input → privacy control |
|---|---|---|
| ![](docs/screenshots/08-prompt-injection.png) | ![](docs/screenshots/10-human-oversight.png) | ![](docs/screenshots/11-safety-check.png) |

| Out-of-scope | Responsible AI panel |
|---|---|
| ![](docs/screenshots/07-out-of-scope.png) | ![](docs/screenshots/09-responsible-ai.png) |

### Example response metadata
```json
{
  "query_type": "INCIDENT",
  "grounded": true,
  "grounding_score": 0.73,
  "risk_level": "LOW",
  "human_review_required": false,
  "safety_flags": [],
  "sources": [{"id": "DOC-001", "title": "VPN Authentication Troubleshooting Runbook"}],
  "ai_disclosure": true
}
```

## Security
Secrets live in **Azure Key Vault**; the Container App reads them through a **user-assigned managed identity** holding three single-resource roles (Key Vault Secrets User, Storage Blob Data Reader, AcrPull). Storage has public and shared-key access disabled; the registry admin user is off; the container runs as non-root. Threat model: [docs/security.md](docs/security.md).

| Key Vault (secret names only) | Managed identity |
|---|---|
| ![](docs/screenshots/15-security-architecture.png) | ![](docs/screenshots/15b-managed-identity.png) |

**Honest gap:** Azure OpenAI, Search and Content Safety still use keys (stored in Key Vault). Token-based authentication is a documented production enhancement.

## Observability
Application Insights records request counts, latency and errors. Logs contain query type, risk, flags, source count and token count, **never** question or answer text.

![Application Insights](docs/screenshots/13-application-insights.png)

## Evaluation
**Portfolio Multi-Agent Evaluation** (`python -m evaluation.evaluate`): 12 hand-written cases across 10 dimensions, including routing and source retrieval. It is a small portfolio evaluation and **does not prove production-level AI safety**.

| Dimension | Result (12 cases × 3 runs, live Azure, 2026-10-05) |
|---|---|
| Routing | 12/12 |
| Classification, grounding, transparency, human oversight | 12/12 each |
| Source retrieval | 6/6 |
| Refusal | 3/3 |
| Prompt injection | 1/1 |
| Safety | 3/4 (TC11: see note) |
| Consistency | 11/12 (TC09) |

**Failures, left visible:** TC09 ("What is the VPN troubleshooting procedure?") is inconsistent across runs because the model sometimes surfaces the genuine VPN timeout conflict between two documents (2 of 5 extra runs); this is the same model-dependent behaviour as the original version. TC11 failed its safety check only because the keyword list did not include the phrase "do not"; the answer did discourage disabling MFA, so I added "do not disable" to that case and re-scored it live (safety then passed). That is a change to the test, not a model change. During that re-score one run hit a transient Azure AI Search error (not reproduced in 50 follow-up searches); the Knowledge agent returned an `error` result as designed and the request went to human review, but it made that case's consistency check fail.

The original single-pipeline run (10 cases, 8 dimensions) is kept below for comparison.

![Evaluation](docs/screenshots/16-responsible-ai-evaluation.png)

| Dimension | Result |
|---|---|
| Classification, grounding, transparency, consistency | 10/10 each |
| Refusal | 3/3 |
| Safety | 3/3 |
| Prompt injection | 1/1 |
| **Human oversight** | **9/10** |

The one failure (TC09, "What is the VPN troubleshooting procedure?") is left visible on purpose: the model sometimes cites both VPN documents and surfaces their genuine conflict (45 vs 30 minute timeout), triggering review. The conflict flag is model-dependent.

### Multi-agent screenshots (v2)
| Architecture | Orchestrator routing |
|---|---|
| ![](docs/screenshots/01-multi-agent-architecture.png) | ![](docs/screenshots/02-orchestrator.png) |

| Incident Agent only | Knowledge Agent only |
|---|---|
| ![](docs/screenshots/03-incident-agent.png) | ![](docs/screenshots/04-knowledge-agent.png) |

| Full workflow (VPN + MFA) | Responsible AI Review Agent |
|---|---|
| ![](docs/screenshots/05-multi-agent-workflow.png) | ![](docs/screenshots/06-responsible-ai-agent.png) |

| Human oversight (HIGH risk) | Prompt injection: no worker agent, 0 tokens |
|---|---|
| ![](docs/screenshots/07-human-oversight.png) | ![](docs/screenshots/08b-prompt-injection-multi-agent.png) |

| Grounded answer with source | Foundry deployments |
|---|---|
| ![](docs/screenshots/09-rag-grounding.png) | ![](docs/screenshots/10-azure-ai-foundry.png) |

| AI Search index (20 docs) | Application Insights (POST /chat) |
|---|---|
| ![](docs/screenshots/11-azure-ai-search.png) | ![](docs/screenshots/12-application-insights.png) |

| Container App running | Response from the deployed v2 app |
|---|---|
| ![](docs/screenshots/13-container-app.png) | ![](docs/screenshots/13b-deployed-multi-agent-response.png) |

Screenshots are real captures; the account bar, subscription ID and API keys were cropped out or covered. The Foundry account also holds an unrelated extra model deployment (`gpt-6.1-sol`) that this project does not use.

## Local Setup
```bash
git clone https://github.com/emran-Automation-Techlead/azure-enterprise-ai-platform
cd azure-enterprise-ai-platform
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # fill in your values; never commit .env
az login                        # ingestion reads Blob Storage with your Azure identity
python -m app.search ingest     # create the index and load the documents
uvicorn app.main:app --port 8000
# in another terminal:
set BACKEND_URL=http://localhost:8000    # PowerShell: $env:BACKEND_URL="http://localhost:8000"
streamlit run ui/streamlit_app.py
```
Synthetic documents are generated by `data/make_docs.py` and uploaded to the `enterprise-docs` container.

## Azure Deployment
Resources (one resource group): Azure AI Search, Storage account, Key Vault, user-assigned managed identity, Container Registry, Container Apps environment + app, Application Insights / Log Analytics; models are deployed in an Azure AI Foundry account.
Steps used: `docker build` → push to ACR → Container App with `--user-assigned`, `--registry-identity`, and Key Vault secret references (`keyvaultref:` + `identityref:`). The deployed app answered a grounded question through the Container Apps ingress.

| Container App running | Response from the deployed app |
|---|---|
| ![](docs/screenshots/14-container-app.png) | ![](docs/screenshots/14b-deployed-app-response.png) |

The multi-agent version (v2) was redeployed the same way with the same security design: Container App with a user-assigned managed identity, secrets as Key Vault references, image pushed to ACR (built locally with Docker because ACR Tasks is blocked on this subscription), telemetry to Application Insights. The demo resources are short-lived and removed after the evidence is captured. The public URL is intentionally not published (it has no user authentication), and the demo deployment is short-lived. Foundry model deployment: [screenshot](docs/screenshots/02-ai-foundry-model.png) · Search index: [screenshot](docs/screenshots/03-ai-search.png).

## Testing
```bash
pytest tests -q                    # 83 tests (71 offline + 12 live)
pytest tests -q --ignore=tests/test_live.py   # offline only, no Azure calls (agents, pipeline, evaluation scoring)
python -m evaluation.evaluate --repeats 3
```

## Docker
```bash
docker build -t enterprise-ai-platform .
docker compose up --build          # reads secrets from your local .env at start-up
```
Non-root user, HEALTHCHECK, and no `.env` inside the image.

## Architecture Decisions
[docs/decisions.md](docs/decisions.md): why Azure AI Search, Azure OpenAI, Blob Storage, Key Vault, Managed Identity, Container Apps, FastAPI, Streamlit, RAG, hybrid search, the Responsible AI layer, human oversight, and why not AKS, fine-tuning or a self-managed vector database.

## Cost Considerations
[docs/cost.md](docs/cost.md): cost drivers and ways to reduce them. No prices are quoted; verify current Azure pricing. Azure AI Search and an always-on Container App bill while they exist.

## Limitations
- Small corpus (20 documents) and a small evaluation set.
- The grounding threshold (0.65) was calibrated on ~12 questions and is fragile near the boundary.
- Conflicting-source detection is model-dependent and not fully consistent.
- Content Safety missed a calmly worded harmful request and does not detect prompt injection (router and local rules cover part of that gap).
- Redacting a secret can leave a question too vague to answer.
- No demographic fairness testing, no authentication, no private networking.
- Multi-agent: more model calls and latency per request; the reviewer sees claims and source IDs, not full source text; agents run sequentially; not yet evaluated live.

## Future Improvements
Run independent agents in parallel; private endpoints and token authentication to AI services; API Management (auth, throttling, versioning); semantic ranker and Prompt Shields; claim-level conflict detection; per-user document access control; CI/CD and IaC; larger evaluation set in CI; multi-tenant design; separate UI/API containers.

## Interview Talking Points
[docs/interview.md](docs/interview.md): a 60 to 90 second pitch, 25 questions with answers, and 12 multi-agent questions with a multi-agent pitch.

## License
MIT
