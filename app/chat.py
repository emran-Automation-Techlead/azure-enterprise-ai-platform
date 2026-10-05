"""Chooses the answer pipeline. AGENT_MODE=multi (default) uses the multi-agent pipeline;
AGENT_MODE=single restores the original single-pipeline behaviour (app/responsible_ai.py)."""
from app import config
from app.models import ChatResponse


def handle(question: str) -> ChatResponse:
    if config.get("AGENT_MODE", required=False, default="multi").lower() == "single":
        from app.responsible_ai import handle as single

        return single(question)
    from app.agents.pipeline import handle as multi

    return multi(question)
