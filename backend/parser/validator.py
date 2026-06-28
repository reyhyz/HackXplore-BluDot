"""
validator.py  (backend/parser/validator.py)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# ── Path setup FIRST ─────────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_UTILS_DIR   = _BACKEND_DIR / "utils"
_PARSER_DIR  = _BACKEND_DIR / "parser"

for _p in (_UTILS_DIR, _PARSER_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from compute_statistics import get_all_values, calculate_mean, calculate_stdev  # noqa: E402
from textToJSON import verify_parsed_data  # noqa: E402

_SKIP_KEYS     = {"Errors", "Unclear"}
_SKIP_PREFIXES = ("Soll_",)

# Matches "DD.MM.YYYY | initials" or "DD.MM.YYYY|initials"
_DATE_SIG_RE = re.compile(
    r"(\d{2}\.\d{2}\.\d{4})\s*\|\s*.+",
    re.IGNORECASE,
)


def _clean_value(value: str) -> str:
    """
    Strip the initials/name after the | delimiter in date-signature fields
    so the Excel export shows only the date.

    "10.06.2026 | ohe"  →  "10.06.2026"
    "10.06.2026|han"    →  "10.06.2026"
    Anything else is returned unchanged.
    """
    m = _DATE_SIG_RE.fullmatch(value.strip())
    if m:
        return m.group(1)
    return value


def _to_data_blocks(verified: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []

    for section_id, section in verified.items():
        if not isinstance(section, dict) or section_id == "Produktinfo":
            continue

        section_errors  = section.get("Errors",  {})
        section_unclear = section.get("Unclear", {})

        for field_name, value in section.items():
            if field_name in _SKIP_KEYS or field_name.startswith("Soll_"):
                continue
            if not isinstance(value, (str, int, float)):
                continue

            flags: dict[str, str] = {}
            if field_name in section_errors:
                flags["error"] = section_errors[field_name]
            if field_name in section_unclear:
                flags["unclear"] = section_unclear[field_name]

            blocks.append({
                "parameter":      f"{section_id} — {field_name}",
                "expected_value": str(section.get(f"Soll_{field_name}", "")),
                "actual_value":   _clean_value(str(value)),   # initials stripped here
                "page_number":    None,
                "line_number":    None,
                "flags":          flags,
            })

    return blocks


def validate(ocr_result: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    verified_doc = verify_parsed_data(ocr_result)
    ui_blocks    = _to_data_blocks(verified_doc)
    return verified_doc, ui_blocks