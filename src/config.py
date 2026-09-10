"""Configuration loading and shared client setup.

Loads secrets from .env and model settings from config.yaml (falls back to
config.example.yaml). Provides a single Groq client factory for normalize.py
and score.py so all LLM calls share the same model settings.
"""

import logging
import os
import time
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
    return _LLM_CONFIG.get("model", "openai/gpt-oss-120b")


def get_temperature() -> float:
    return float(_LLM_CONFIG.get("temperature", 0.1))


def get_max_retries() -> int:
    return int(_LLM_CONFIG.get("max_retries", 1))


def get_timeout() -> int:
    return int(_LLM_CONFIG.get("timeout", 60))


def get_metrics_file() -> str:
    return _LOGGING_CONFIG.get("metrics_file", METRICS_FILE)


def get_client():
    """Create (and lazily cache) a Groq client."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Copy .env.example to .env and add your key."
        )
    from groq import Groq

    return Groq(api_key=api_key)


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