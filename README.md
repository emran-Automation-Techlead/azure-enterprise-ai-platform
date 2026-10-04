# Enterprise Azure AI Platform

**Intelligent IT Knowledge, Incident & Responsible AI Assistant**: a RAG application on Azure where Responsible AI, grounding, security, observability and human oversight are *architectural controls around the generative AI layer*, not an afterthought.

![python](https://img.shields.io/badge/python-3.11-blue) ![azure](https://img.shields.io/badge/Azure-OpenAI%20%7C%20AI%20Search%20%7C%20Content%20Safety-0078D4) ![tests](https://img.shields.io/badge/tests-35%20passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green)

> **Portfolio project with 100% synthetic data.** It demonstrates engineering patterns for responsible AI. It is **not** a certified legal, regulatory, compliance or safety assessment.

![Grounded response with sources and the Responsible AI panel](docs/screenshots/05-rag-grounded-response.png)

## Business Problem
IT organisations keep their knowledge in runbooks, policies and past incidents. A generic chatbot answers confidently from its training data and will invent fixes and policies that sound right, which is dangerous for things like security controls and production changes. Engineers need answers **from the company's own documents**, with sources, and a clear signal when a human should step in.

## Solution
An assistant that routes each question, retrieves enterprise documents from Azure AI Search, answers **only** from them with Azure OpenAI, and then passes the result through a Responsible AI layer that checks safety, grounding and conflicts and decides whether a human should review.

## Architecture
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
**Portfolio Responsible AI Evaluation**: 10 hand-written cases × 3 runs across 8 dimensions (`python -m evaluation.evaluate`). It is a small portfolio evaluation and **does not prove production-level AI safety**.

![Evaluation](docs/screenshots/16-responsible-ai-evaluation.png)

| Dimension | Result |
|---|---|
| Classification, grounding, transparency, consistency | 10/10 each |
| Refusal | 3/3 |
| Safety | 3/3 |
| Prompt injection | 1/1 |
| **Human oversight** | **9/10** |

The one failure (TC09, "What is the VPN troubleshooting procedure?") is left visible on purpose: the model sometimes cites both VPN documents and surfaces their genuine conflict (45 vs 30 minute timeout), triggering review. The conflict flag is model-dependent.

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

The public URL is intentionally not published (it has no user authentication), and the demo deployment is short-lived. Foundry model deployment: [screenshot](docs/screenshots/02-ai-foundry-model.png) · Search index: [screenshot](docs/screenshots/03-ai-search.png).

## Testing
```bash
pytest tests -q                    # 35 tests (23 offline + 12 live)
pytest tests/test_offline.py -q    # offline only, no Azure calls
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

## Future Improvements
Private endpoints and token authentication to AI services; API Management (auth, throttling, versioning); semantic ranker and Prompt Shields; claim-level conflict detection; per-user document access control; CI/CD and IaC; larger evaluation set in CI; multi-tenant design; separate UI/API containers.

## Interview Talking Points
[docs/interview.md](docs/interview.md): a 60 to 90 second pitch and 25 questions with answers.

## License
MIT
