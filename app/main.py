import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import config, router, telemetry
from app.llm import LLMError
from app.models import ChatRequest, ChatResponse, SafetyCheckRequest, SafetyCheckResponse
from app.chat import handle
from app.safety import default_checker, redact
from app.search import SearchError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")
telemetry.setup()

app = FastAPI(title="Enterprise Azure AI Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    with telemetry.Timer() as t:
        try:
            resp = handle(req.question)
        except config.ConfigError as exc:
            raise HTTPException(500, str(exc)) from exc
        except (LLMError, SearchError) as exc:
            raise HTTPException(502, str(exc)) from exc
        except Exception as exc:
            log.exception("chat failed")
            raise HTTPException(500, "Something unexpected went wrong. Please try again.") from exc
    log.info("chat ok latency_ms=%d type=%s risk=%s", t.ms, resp.query_type, resp.risk_level)
    return resp


@app.post("/evaluate")
def evaluate(repeats: int = 1):
    """Run the Portfolio Multi-Agent Evaluation (12 cases). Slow: makes real model calls."""
    if not 1 <= repeats <= 3:
        raise HTTPException(422, "repeats must be between 1 and 3.")
    from evaluation.evaluate import run  # imported lazily so the API starts without the evaluation package

    try:
        return run(repeats)
    except config.ConfigError as exc:
        raise HTTPException(500, str(exc)) from exc
    except (LLMError, SearchError) as exc:
        raise HTTPException(502, str(exc)) from exc


@app.post("/safety-check", response_model=SafetyCheckResponse)
def safety_check(req: SafetyCheckRequest):
    """Run the safety layers on a piece of text without answering it."""
    text = redact(req.text)
    rules = router.apply_rules(text)
    result = default_checker().check(text)
    flags = sorted(set(rules.safety_flags + result.flags))
    blocked = rules.blocked or result.blocked
    return SafetyCheckResponse(
        safe=not flags,
        blocked=blocked,
        flags=flags,
        details=rules.reasons + result.details,
        checkers_used=["router-rules"] + result.checkers,
    )
