"""
textToJSON.py  (backend/parser/textToJSON.py)
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_UTILS_DIR = Path(__file__).resolve().parent.parent / "utils"
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

from utils.compute_statistics import get_all_values, calculate_mean, calculate_stdev  # noqa: E402

_SKIP_KEYS     = {"Errors", "Unclear"}
_SKIP_PREFIXES = ("Soll_",)

_DATE_TIME_FMTS = [
    "%d.%m.%Y|%H:%M",
    "%d.%m.%Y | %H:%M",
    "%d.%m.%Y|%H:%M:%S",
    "%d.%m.%Y",
]

_SIG_FRAGMENTS = ("bearbeitet", "geprüft", "gepruft")


def _is_empty(value: str) -> bool:
    return str(value).strip().upper() in ("EMPTY", "")


def _is_sig_field(key: str) -> bool:
    k = key.lower()
    return any(frag in k for frag in _SIG_FRAGMENTS)


def _parse_dt(raw: str) -> datetime | None:
    for fmt in _DATE_TIME_FMTS:
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def _extract_date_from_sig(raw: str) -> datetime | None:
    """Extract just the date part from a 'DD.MM.YYYY | initials' field."""
    date_part = raw.split("|")[0].strip()
    return _parse_dt(date_part)


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _extract_numeric(value: str) -> float | None:
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", value)
    return float(m.group().replace(",", ".")) if m else None


# ── Check 1 – Time-range integrity ────────────────────────────────────────────

def _check_time_range(section: dict, errors: dict) -> None:
    start_fields: dict[str, datetime] = {}
    end_fields:   dict[str, datetime] = {}

    for key, raw in section.items():
        if not isinstance(raw, str):
            continue
        k_lower = key.lower()
        dt = _parse_dt(raw)
        if dt is None:
            continue
        if "start" in k_lower:
            start_fields[key] = dt
        elif k_lower.startswith("erlaubte") or "end" in k_lower:
            end_fields[key] = dt

    for s_key, s_dt in start_fields.items():
        for e_key, e_dt in end_fields.items():
            if s_dt > e_dt:
                errors[s_key] = (
                    f"Start time ({s_dt:%d.%m.%Y %H:%M}) is after "
                    f"the allowed end time in '{e_key}' ({e_dt:%d.%m.%Y %H:%M})"
                )


# ── Check 2a – Bearbeitet → Geprüft ordering ─────────────────────────────────
# Within each section (and within each table row for composite keys),
# the Geprüft date must not be before the Bearbeitet date.
# Handles both simple keys and composite table keys like
# "Oven A - Bearbeitet (Datum/Kürzel)" / "Oven A - Geprüft (Datum/Kürzel)".

def _check_bearbeitet_geprueft_order(section: dict, errors: dict) -> None:
    # Group keys by their row prefix so composite table rows are compared
    # against each other, not across different rows.
    # Simple keys (no " - " prefix) are grouped under the empty string "".
    #
    # Example grouping:
    #   ""         → {"Bearbeitet: (Datum/Kürzel)": "...", "Geprüft (Datum/Kürzel)": "..."}
    #   "Oven A"   → {"Bearbeitet (Datum/Kürzel)": "...", "Geprüft (Datum/Kürzel)": "..."}
    #   "Batter Pump" → {...}

    groups: dict[str, dict[str, str]] = {}

    for key, raw in section.items():
        if not isinstance(raw, str) or not _is_sig_field(key):
            continue

        if " - " in key:
            prefix, suffix = key.split(" - ", 1)
        else:
            prefix, suffix = "", key

        groups.setdefault(prefix, {})[suffix] = raw

    for prefix, fields in groups.items():
        bearbeitet_dt: datetime | None = None
        bearbeitet_key: str | None     = None
        geprueft_dt:   datetime | None = None
        geprueft_key:  str | None      = None

        for suffix, raw in fields.items():
            s_lower = suffix.lower()
            dt = _extract_date_from_sig(raw)
            if dt is None:
                continue
            if "bearbeitet" in s_lower:
                bearbeitet_dt  = dt
                bearbeitet_key = f"{prefix} - {suffix}" if prefix else suffix
            elif "geprüft" in s_lower or "gepruft" in s_lower:
                geprueft_dt  = dt
                geprueft_key = f"{prefix} - {suffix}" if prefix else suffix

        if bearbeitet_dt and geprueft_dt and geprueft_dt < bearbeitet_dt:
            label = f"({prefix}) " if prefix else ""
            errors[geprueft_key] = (
                f"{label}Geprüft date ({geprueft_dt:%d.%m.%Y}) is before "
                f"Bearbeitet date ({bearbeitet_dt:%d.%m.%Y}) in '{bearbeitet_key}' — "
                f"verification cannot precede processing"
            )


# ── Check 2b – Signature / EMPTY completeness ────────────────────────────────

def _check_signatures_and_empty(section: dict, errors: dict) -> None:
    for key, raw in section.items():
        if key in _SKIP_KEYS or any(key.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if not isinstance(raw, str):
            continue

        if _is_sig_field(key):
            if _is_empty(raw):
                errors[key] = "Field is empty — date and signature required"
            elif "|" not in raw:
                errors[key] = "Missing '|' delimiter — signature could not be separated from date"
            elif not raw.split("|", 1)[1].strip():
                errors[key] = "Missing signature (empty after '|')"
        else:
            if _is_empty(raw):
                errors[key] = "Field is empty — value required"


# ── Check 3 – Soll / Ist agreement ───────────────────────────────────────────

def _check_soll_ist(section: dict, errors: dict, unclear: dict) -> None:
    for key, soll_raw in section.items():
        if not key.startswith("Soll_"):
            continue
        actual_key = key[len("Soll_"):]
        actual_raw = section.get(actual_key)

        if actual_raw is None:
            unclear[actual_key] = (
                f"Soll value '{soll_raw}' is specified but "
                f"no matching field '{actual_key}' was found"
            )
            continue

        soll_norm   = _normalise(str(soll_raw))
        actual_norm = _normalise(str(actual_raw))

        range_match = re.search(
            r"([-+]?\d+(?:[.,]\d+)?)\s*[-–to]+\s*([-+]?\d+(?:[.,]\d+)?)",
            soll_norm,
        )
        if range_match:
            low  = float(range_match.group(1).replace(",", "."))
            high = float(range_match.group(2).replace(",", "."))
            num  = _extract_numeric(actual_norm)
            if num is not None:
                if not (low <= num <= high):
                    errors[actual_key] = (
                        f"Value {num} is outside the allowed range "
                        f"[{low}, {high}] (Soll: '{soll_raw}')"
                    )
            else:
                unclear[actual_key] = (
                    f"Cannot compare '{actual_raw}' against numeric range '{soll_raw}'"
                )
            continue

        op_match = re.match(r"([≤≥<>]=?)\s*([-+]?\d+(?:[.,]\d+)?)", soll_norm)
        if op_match:
            op        = op_match.group(1)
            threshold = float(op_match.group(2).replace(",", "."))
            num       = _extract_numeric(actual_norm)
            if num is not None:
                ok = {
                    "≤": num <= threshold, "≥": num >= threshold,
                    "<": num <  threshold, ">": num >  threshold,
                    "<=": num <= threshold, ">=": num >= threshold,
                }.get(op, True)
                if not ok:
                    errors[actual_key] = (
                        f"Value {num} does not satisfy '{op} {threshold}' "
                        f"(Soll: '{soll_raw}')"
                    )
            else:
                unclear[actual_key] = (
                    f"Cannot compare '{actual_raw}' against operator condition '{soll_raw}'"
                )
            continue

        if soll_norm in actual_norm or actual_norm in soll_norm:
            continue

        unclear[actual_key] = (
            f"Agent is unsure whether '{actual_raw}' satisfies Soll value '{soll_raw}'"
        )


# ── Check 4 – Statistical anomaly ────────────────────────────────────────────

def _check_statistical_anomalies(
    section_id:   str,
    section:      dict,
    errors:       dict,
    sap_material: str,
    process_step: str,
) -> None:
    for key, value in section.items():
        if key in _SKIP_KEYS or any(key.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if not isinstance(value, (str, int, float)):
            continue

        history = get_all_values(section_id, key, sap_material, process_step)
        if len(history) < 3:
            continue

        try:
            num_val = float(str(value).replace(",", "."))
            mean    = calculate_mean(history)
            stdev   = calculate_stdev(history)

            if stdev > 0 and abs(num_val - mean) > (3 * stdev):
                errors[key] = (
                    f"Statistical outlier: {value!r} drifts beyond historical bounds "
                    f"(mean={mean:.2f}, stdev={stdev:.2f})"
                )
        except (ValueError, TypeError):
            pass


# ── Public API ────────────────────────────────────────────────────────────────

def verify_parsed_data(data: dict[str, Any]) -> dict[str, Any]:
    sap_material: str = data.get("sapMaterial", "")
    process_step: str = data.get("processStep", "")

    if not sap_material or not process_step:
        print(
            "Warning: 'sapMaterial' and/or 'processStep' missing — "
            "statistical anomaly check will be skipped."
        )

    for section_id, section in data.items():
        if not isinstance(section, dict):
            continue

        errors:  dict[str, str] = {}
        unclear: dict[str, str] = {}

        _check_time_range(section, errors)
        _check_bearbeitet_geprueft_order(section, errors)  # ← new check
        _check_signatures_and_empty(section, errors)
        _check_soll_ist(section, errors, unclear)

        if sap_material and process_step:
            _check_statistical_anomalies(section_id, section, errors, sap_material, process_step)

        if errors:
            section["Errors"] = errors
        if unclear:
            section["Unclear"] = unclear

    return data


if __name__ == "__main__":
    input_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("root/data/processing/sample.JSON")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_stem(input_path.stem + "_verified")

    raw      = json.loads(input_path.read_text(encoding="utf-8"))
    verified = verify_parsed_data(raw)

    output_path.write_text(json.dumps(verified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓  Verified data written to {output_path}")