"""
lesson_extractor: Layer 5 (optional). Maps trace.jsonl → LessonEntry → EvolutionStore.

Schema mismatch note:
    MetaClaw backend is EvolutionStore (JSONL at configurable path) accepting LessonEntry
    records. No SKILL.md file format — registration is via EvolutionStore.append().
    This is guarded by config.arc.metaclaw_enabled (default False).
"""

import json
import re
from pathlib import Path


# Mapping from trace event types → (LessonCategory, severity)
_EVENT_MAPPINGS: list[tuple[dict, str, str]] = [
    # condition dict, category name, severity
    ({"event_type": "sequential_thinking", "isRevision": True}, "PIPELINE", "warning"),
    ({"event_type": "decision", "phase": "peer_review"}, "ANALYSIS", "info"),
    ({"status": "FAILED"}, "PIPELINE", "error"),
]

# Regex for adversarial test catch patterns
_ADVERSARIAL_PATTERN = re.compile(
    r"(hallucinated|fake.doi|invalid.citation|adversarial|injection)",
    re.IGNORECASE,
)


def extract_lessons_from_trace(trace_jsonl_path: str) -> list[dict]:
    """
    Read trace.jsonl and return list of LessonEntry-compatible dicts.

    Mappings:
        event_type=sequential_thinking, isRevision=True  → category=PIPELINE, severity=warning
        event_type=decision, phase=peer_review           → category=ANALYSIS, severity=info
        adversarial catch (detected by message pattern)  → category=EXPERIMENT, severity=error
        pipeline failure (status=FAILED in narration)    → category=PIPELINE, severity=error

    Args:
        trace_jsonl_path: Path to trace.jsonl written by scripts/trace_logger.py.

    Returns:
        List of LessonEntry-compatible dicts with fields:
            stage, category, severity, description, timestamp
    """
    trace_path = Path(trace_jsonl_path)
    if not trace_path.exists():
        return []

    lessons: list[dict] = []

    for line in trace_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        lesson = _event_to_lesson(event)
        if lesson:
            lessons.append(lesson)

    return lessons


def register_lessons_with_metaclaw(
    lessons: list[dict],
    evolution_store_path: str,
) -> None:
    """
    Register extracted lessons with ARC's EvolutionStore.

    Guarded by EvolutionStore import — no-ops gracefully if metaclaw is unavailable.
    Caller is responsible for checking config.arc.metaclaw_enabled before calling.

    Args:
        lessons:              List of LessonEntry-compatible dicts from extract_lessons_from_trace().
        evolution_store_path: Path to EvolutionStore JSONL file.
    """
    if not lessons:
        return

    try:
        from researchclaw.evolution import EvolutionStore, LessonEntry, LessonCategory
    except ImportError:
        # metaclaw not available — no-op
        return

    store = EvolutionStore(path=evolution_store_path)

    for lesson_dict in lessons:
        try:
            category_str = lesson_dict.get("category", "PIPELINE")
            category = getattr(LessonCategory, category_str, LessonCategory.PIPELINE)

            entry = LessonEntry(
                stage=lesson_dict.get("stage", "unknown"),
                category=category,
                severity=lesson_dict.get("severity", "info"),
                description=lesson_dict.get("description", ""),
                timestamp=lesson_dict.get("timestamp", ""),
            )
            store.append(entry)
        except Exception:
            continue


def _event_to_lesson(event: dict) -> dict | None:
    """
    Convert a single trace event dict to a LessonEntry dict, or None if not lesson-worthy.
    """
    event_type = event.get("event_type", "")
    message = str(event.get("message", event.get("content", "")))
    phase = event.get("phase", event.get("stage", "unknown"))
    timestamp = event.get("timestamp", event.get("ts", ""))

    # Adversarial catch (highest priority check)
    if _ADVERSARIAL_PATTERN.search(message):
        return {
            "stage": phase,
            "category": "EXPERIMENT",
            "severity": "error",
            "description": f"Adversarial condition detected in trace: {message[:200]}",
            "timestamp": timestamp,
        }

    # Pipeline failure
    if event.get("status") == "FAILED" or event_type == "pipeline_failed":
        return {
            "stage": phase,
            "category": "PIPELINE",
            "severity": "error",
            "description": f"Pipeline failure at {phase}: {message[:200]}",
            "timestamp": timestamp,
        }

    # Sequential thinking revision
    if event_type == "sequential_thinking" and event.get("isRevision"):
        return {
            "stage": phase,
            "category": "PIPELINE",
            "severity": "warning",
            "description": f"Sequential thinking revision at {phase}: {message[:200]}",
            "timestamp": timestamp,
        }

    # Peer review decision
    if event_type == "decision" and str(event.get("phase", "")).lower() == "peer_review":
        return {
            "stage": "peer_review",
            "category": "ANALYSIS",
            "severity": "info",
            "description": f"Peer review decision: {message[:200]}",
            "timestamp": timestamp,
        }

    return None
