"""Safe telemetry. Application Insights is enabled only when a connection string is configured.

Only counts, latency and categories are recorded. Question and answer text, credentials and tokens are never logged.
"""
import logging
import time

from app import config

log = logging.getLogger("telemetry")


def setup() -> bool:
    cs = config.get("APPLICATIONINSIGHTS_CONNECTION_STRING", required=False)
    if not cs:
        log.info("Application Insights not configured; using console logging only.")
        return False
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=cs)
        log.info("Application Insights telemetry enabled.")
        return True
    except Exception:  # monitoring must never take the app down
        log.exception("Could not enable Application Insights.")
        return False


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.ms = int((time.perf_counter() - self.start) * 1000)
        return False
