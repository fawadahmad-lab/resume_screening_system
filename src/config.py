"""Configuration loading and shared client setup.

Loads secrets from .env and model settings from config.yaml (falls back to
config.example.yaml). Provides a single Groq client factory for normalize.py
and score.py so all LLM calls share the same model settings.
"""

import logging
import os
import re
import time
from types import SimpleNamespace
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE = os.path.join(ROOT_DIR, "data", "results", "call_metrics.log")

logger = logging.getLogger(__name__)


def _load_yaml() -> Dict[str, Any]:
    """Load config.yaml if present, else config.example.yaml."""
    candidates = [
        os.path.join(ROOT_DIR, "config.yaml"),
        os.path.join(ROOT_DIR, "config.example.yaml"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
    return {}


_CONFIG: Dict[str, Any] = _load_yaml()
_LLM_CONFIG: Dict[str, Any] = _CONFIG.get("llm", {})
_LOGGING_CONFIG: Dict[str, Any] = _CONFIG.get("logging", {})
_PIPELINE_CONFIG: Dict[str, Any] = _CONFIG.get("pipeline", {})


def get_score_ensemble_n() -> int:
    """Number of scoring runs ensembled per candidate (median total wins)."""
    return int(_PIPELINE_CONFIG.get("score_ensemble_n", 3))


def get_llm_config() -> Dict[str, Any]:
    return _LLM_CONFIG


def get_model() -> str:
    return _LLM_CONFIG.get("model", "openai/gpt-oss-20b")


def get_provider() -> str:
    """LLM provider: 'groq' (default), 'ollama', or 'auto'.

    'auto' starts on Groq and falls back to Ollama for the remainder of the
    process once a Groq daily-token (TPD) exhaustion is detected.
    """
    return _LLM_CONFIG.get("provider", "groq")


def get_ollama_host() -> str:
    return _LLM_CONFIG.get("ollama_host", "https://ollama.com")


def get_ollama_model() -> str:
    """Model name for Ollama (its namespace differs from Groq's regexp)."""
    return _LLM_CONFIG.get("ollama_model", "gpt-oss:120b")


def get_temperature() -> float:
    return float(_LLM_CONFIG.get("temperature", 0.1))


def get_max_retries() -> int:
    return int(_LLM_CONFIG.get("max_retries", 1))


def get_call_interval() -> float:
    """Seconds to wait before each first LLM attempt (free-tier TPM pacing)."""
    return float(_LLM_CONFIG.get("call_interval_s", 0.0))


def get_timeout() -> int:
    return int(_LLM_CONFIG.get("timeout", 60))


def get_metrics_file() -> str:
    return _LOGGING_CONFIG.get("metrics_file", METRICS_FILE)


def rate_limit_sleep(exception: Exception) -> None:
    """Sleep until a Groq 429 rate-limit window closes.

    Groq embeds 'Please try again in Xs' (or 'XmYs') in rate-limit errors.
    Parse and sleep that duration + a small buffer so the next LLM attempt
    lands in a fresh TPM window (gpt-oss-20b has a tight 8k tokens/min
    limit). Falls back to a 20s sleep if the wait can't be parsed.
    """
    try:
        match = re.search(r"Please try again in (\d+(?:\.\d+)?)(s|m|h)", str(exception))
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            wait = value * {"s": 1, "m": 60, "h": 3600}[unit]
        else:
            wait = 20.0
    except Exception:
        wait = 20.0
    time.sleep(wait + 2.0)


_GROQ_CLIENT = None
_OLLAMA_CLIENT = None
_FALLBACK_TRIGGERED = False


class _OllamaResponse:
    """Minimal OpenAI/Groq-style response wrapper for an Ollama chat reply."""

    def __init__(self, content: str, prompt_tokens: int, completion_tokens: int):
        self.choices = [
            SimpleNamespace(message=SimpleNamespace(content=content))
        ]
        self.usage = SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class _OllamaChatCompletions:
    """Adapter: expose Groq-style chat.completions.create on the Ollama client.

    Translates Groq's response_format json_schema envelope into Ollama's
    `format=<schema dict>` parameter and returns an OpenAI-shaped response so
    normalize/score modules stay provider-agnostic.
    """

    def __init__(self, ollama_client):
        self._client = ollama_client

    def create(self, model, messages, temperature, response_format=None, **kwargs):
        schema = None
        if response_format:
            schema = response_format.get("json_schema", {}).get("schema")
        resp = self._client.chat(
            get_ollama_model(),
            messages=messages,
            format=schema or "json",
            options={"temperature": temperature},
            stream=False,
        )
        return _OllamaResponse(
            content=resp.message.content,
            prompt_tokens=getattr(resp, "prompt_eval_count", 0) or 0,
            completion_tokens=getattr(resp, "eval_count", 0) or 0,
        )


class _OllamaCompatClient:
    """Ollama client surfaced under the Groq chat.completions call shape."""

    def __init__(self, ollama_client):
        self.chat = SimpleNamespace(completions=_OllamaChatCompletions(ollama_client))


def _get_groq_client():
    global _GROQ_CLIENT
    if _GROQ_CLIENT is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Copy .env.example to .env and add your key."
            )
        from groq import Groq

        _GROQ_CLIENT = Groq(api_key=api_key)
    return _GROQ_CLIENT


def _get_ollama_client():
    global _OLLAMA_CLIENT
    if _OLLAMA_CLIENT is None:
        api_key = os.environ.get("OLLAMA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OLLAMA_API_KEY not set (needed for ollama provider/fallback)."
            )
        from ollama import Client as OllamaClient

        _OLLAMA_CLIENT = OllamaClient(
            host=get_ollama_host(),
            headers={"Authorization": "Bearer " + api_key},
        )
    return _OLLAMA_CLIENT


def _is_tpd_exhaustion(exception: Exception) -> bool:
    """Detect a Groq DAILY-token (TPD) exhaustion, as opposed to a transient
    8k/min TPM window wait that rate_limit_sleep() can ride out.

    Triggers on Groq rate-limit wording mentioning 'day', 'daily', or 'TPD'.
    Returns False for plain 'Please try again in Xs' TPM messages.
    """
    text = str(exception).lower()
    if any(needle in text for needle in ("daily", "day's", "per day", "tpd", "for the day")):
        return True
    return False


def get_client():
    """Return a cached, provider-appropriate LLM client.

    Provider resolution (see get_provider()):
      - provider == 'ollama': always the Ollama hosted client.
      - provider in ('groq', 'auto'): Groq; on TPD exhaustion when 'auto',
        falls back to Ollama for the remainder of the process and caches that
        decision (_FALLBACK_TRIGGERED).
    """
    global _FALLBACK_TRIGGERED
    provider = get_provider()

    if provider == "ollama" or _FALLBACK_TRIGGERED:
        return _get_ollama_client()
    try:
        return _get_groq_client()
    except RuntimeError:
        if provider == "auto":
            return _get_ollama_client()
        raise


def get_active_model() -> str:
    """Model name actually being used (Ollama name if the Ollama provider is
    active, else the configured Groq model)."""
    if get_provider() == "ollama" or _FALLBACK_TRIGGERED:
        return get_ollama_model()
    return get_model()


def fallback_to_ollama_if_tpd(exception: Exception) -> None:
    """Permanently switch the cached provider to Ollama on Groq TPD exhaustion.

    Called from normalize/score after a rate-limited attempt. Must be invoked
    BEFORE the retry loop re-creates a client so subsequent attempts (and the
    rest of the batch) use Ollama. Logs the transition loudly.
    """
    global _FALLBACK_TRIGGERED
    if get_provider() == "ollama" or _FALLBACK_TRIGGERED:
        return
    if not _is_tpd_exhaustion(exception):
        return
    _FALLBACK_TRIGGERED = True
    logger.warning(
        "Groq daily token (TPD) window exhausted (%s). Failing over to "
        "Ollama provider for the remainder of this process.",
        str(exception)[:300],
    )


def log_metrics(
    stage: str,
    candidate_id: str,
    model: str,
    latency_seconds: float,
    tokens_in: int,
    tokens_out: int,
) -> None:
    """Append latency/token usage for a normalize/score LLM call.

    Metric logging started at Phase 4 per AGENTS.md Section 12 so Day 4
    cost/latency analysis has a full history.
    """
    metrics_file = get_metrics_file()
    try:
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
        with open(metrics_file, "a") as f:
            f.write(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"stage={stage} candidate={candidate_id} model={model} "
                f"latency={latency_seconds:.2f}s tokens_in={tokens_in} "
                f"tokens_out={tokens_out}\n"
            )
    except Exception as e:  # logging must never break the pipeline
        logger.warning("Failed to write call metrics: %s", e)