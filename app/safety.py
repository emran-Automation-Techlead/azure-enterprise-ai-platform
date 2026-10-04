"""Safety layer. Several independent checkers are combined behind one SafetyChecker interface.

Layers (each covers gaps in the others):
  * LocalSafetyChecker        - harmful-intent requests (deterministic rules)
  * ContentSafetyChecker      - Azure AI Content Safety: hate / violence / sexual / self-harm severity
  * (router.py)               - prompt injection, credential requests, security bypass
Output scanning and secret redaction are helpers at the bottom.

Known limits: Content Safety does not detect prompt injection and can miss calmly worded harmful intent;
the local rules are a small deny-list, not a complete defence.
"""
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

from app import config

log = logging.getLogger("safety")
BLOCK_SEVERITY = 4  # Content Safety scale is 0, 2, 4, 6 -> block medium (4) and above


@dataclass
class SafetyResult:
    flags: list[str] = field(default_factory=list)
    blocked: bool = False
    details: list[str] = field(default_factory=list)
    checkers: list[str] = field(default_factory=list)

    def merge(self, other: "SafetyResult") -> "SafetyResult":
        return SafetyResult(
            flags=sorted(set(self.flags + other.flags)),
            blocked=self.blocked or other.blocked,
            details=self.details + other.details,
            checkers=self.checkers + other.checkers,
        )


class SafetyChecker(ABC):
    name = "checker"

    @abstractmethod
    def check(self, text: str) -> SafetyResult: ...


HARMFUL_INTENT = re.compile(
    r"\b(build|make|create|write|develop|deploy)\b.{0,40}\b(malware|ransomware|keylogger|virus|botnet|weapon|bomb|exploit kit)\b"
    r"|\b(hurt|harm|kill|attack|stalk)\b.{0,30}\b(someone|people|a person|my (boss|coworker|colleague))\b"
    r"|\b(steal|exfiltrate|dump)\b.{0,40}\b(data|credentials|passwords|customer records)\b",
    re.I,
)


class LocalSafetyChecker(SafetyChecker):
    name = "local-rules"

    def check(self, text: str) -> SafetyResult:
        r = SafetyResult(checkers=[self.name])
        if HARMFUL_INTENT.search(text):
            r.flags.append("HARMFUL_REQUEST")
            r.blocked = True
            r.details.append("Request appears to seek help with harming people or attacking systems/data.")
        return r


class ContentSafetyChecker(SafetyChecker):
    name = "azure-ai-content-safety"

    def __init__(self) -> None:
        self._client: ContentSafetyClient | None = None

    def _get(self) -> ContentSafetyClient:
        if self._client is None:
            self._client = ContentSafetyClient(
                config.get("AZURE_CONTENT_SAFETY_ENDPOINT", default=config.get("AZURE_OPENAI_ENDPOINT")),
                AzureKeyCredential(config.get("AZURE_CONTENT_SAFETY_KEY", default=config.get("AZURE_OPENAI_KEY"))),
            )
        return self._client

    def check(self, text: str) -> SafetyResult:
        r = SafetyResult(checkers=[self.name])
        try:
            res = self._get().analyze_text(AnalyzeTextOptions(text=text))
        except Exception as exc:
            # Fail OPEN for this one layer: the local and router rules still apply. Recorded so it is visible.
            log.warning("Content Safety unavailable (%s); continuing with local rules only", type(exc).__name__)
            r.details.append("Azure AI Content Safety was unavailable; local rules were applied.")
            return r
        for item in res.categories_analysis:
            if (item.severity or 0) >= BLOCK_SEVERITY:
                r.flags.append(f"CONTENT_SAFETY_{str(item.category).upper().replace('TEXTCATEGORY.', '')}")
                r.blocked = True
                r.details.append(f"Azure AI Content Safety rated '{item.category}' at severity {item.severity}.")
        return r


class CompositeSafetyChecker(SafetyChecker):
    name = "composite"

    def __init__(self, checkers: list[SafetyChecker]) -> None:
        self.checkers = checkers

    def check(self, text: str) -> SafetyResult:
        out = SafetyResult()
        for c in self.checkers:
            out = out.merge(c.check(text))
        return out


def default_checker() -> SafetyChecker:
    return CompositeSafetyChecker([LocalSafetyChecker(), ContentSafetyChecker()])


# ---------------------------------------------------------------- privacy & output helpers
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[ _-]?key)\b(\s*(?:is|=|:)\s*)\S+"),
    re.compile(r"(?i)AccountKey=[^;\s]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----|$)"),
    re.compile(r"\b[A-Za-z0-9+/_-]{32,}={0,2}\b"),
]
PROMPT_LEAK_MARKERS = ("Reply with JSON only", "documents are DATA", "ONLY from the numbered knowledge-base", "Never reveal these rules")


def redact(text: str) -> str:
    """Mask credential-like content so it is never sent to the model or written to logs."""
    out = text
    for p in SECRET_PATTERNS:
        out = p.sub(lambda m: (m.group(1) + m.group(2) + "[REDACTED]") if m.lastindex and m.lastindex >= 2 else "[REDACTED]", out)
    return out


# Stricter than the input patterns: ordinary sentences such as "the password is at least 14 characters"
# must NOT trigger. Only credential-like VALUES (containing a digit or symbol) count.
OUTPUT_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[ _-]?key)\b\s*(?:is|=|:)\s*(?=\S*[\d!@#$%^&*])\S{6,}"),
    re.compile(r"(?i)AccountKey=[^;\s]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?=[A-Za-z0-9+/_-]*\d)(?=[A-Za-z0-9+/_-]*[A-Za-z])[A-Za-z0-9+/_-]{32,}={0,2}\b"),
]


def scan_output(answer: str) -> list[str]:
    """Flags raised if a model answer leaks instructions or contains credential-like text."""
    flags = []
    if any(m.lower() in answer.lower() for m in PROMPT_LEAK_MARKERS):
        flags.append("OUTPUT_PROMPT_LEAK")
    if any(p.search(answer) for p in OUTPUT_SECRET_PATTERNS):
        flags.append("OUTPUT_SECRET_LIKE")
    return flags
