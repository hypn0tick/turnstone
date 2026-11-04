import json
import os
import re

PREBUILT_PATTERNS = [
    r"sk-ant-api\d{2}-[A-Za-z0-9_-]{20,}",
    r"sk-proj-[A-Za-z0-9_-]{20,}",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"ghp_[A-Za-z0-9]{36}",
    r"AKIA[0-9A-Z]{16}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"AIza[0-9A-Za-z_-]{35}",
]

PII_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b\d{9}\b",
    r"\b(?:\d[ -]*?){13,16}\b",
]


def _custom_patterns():
    raw = os.environ.get("GUARDRAIL_PATTERNS_JSON", "")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    patterns = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                patterns.append(item)
            elif isinstance(item, dict):
                p = item.get("pattern") or item.get("regex")
                if isinstance(p, str):
                    patterns.append(p)
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, str):
                patterns.append(v)
    return patterns


def evaluate(text):
    try:
        if not isinstance(text, str):
            return "ALLOWED"
        all_patterns = PREBUILT_PATTERNS + PII_PATTERNS + _custom_patterns()
        for pat in all_patterns:
            try:
                if re.search(pat, text):
                    return "BLOCKED"
            except re.error:
                continue
        return "ALLOWED"
    except Exception:
        return "ALLOWED"