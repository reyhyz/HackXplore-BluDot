# backend/validator.py
from typing import Dict

def validate(ocr_result: Dict) -> list:
    blocks = []
    for chapter_id, fields in ocr_result.items():
        for field_name, value in fields.items():
            blocks.append({
                "parameter": f"{chapter_id} — {field_name}",
                "expected_value": "",
                "actual_value": value,
                "page_number": None,
                "line_number": None,
                "flags": {"unvalidated": "Validator not yet connected"}
                         if value in ("EMPTY", "UNCLEAR")
                         else {}
            })
    return blocks