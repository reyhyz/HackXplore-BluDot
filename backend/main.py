"""
main.py
---------
FastAPI backend that connects:
  1. PDF upload  →  OCRProcessor (Gemini)
  2. OCR result  →  Validator (your team's module, plugged in below)
  3. Validated data lives in memory (keyed by file_id)
  4. GET /files   →  ReviewDashboard polls this
  5. POST /export →  jsonToExcel, returns the .xlsx as a download

Run:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import io
import os
import uuid
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── Your own modules ──────────────────────────────────────────────────────────
from dotenv import load_dotenv
from agent import extract_chapters_from_images   # your OCR file
from agent import convert_pdf_to_images
from parser import export_to_excel

# Plug your team's validator in here.
# It must accept the raw OCR dict and return a list of data_block dicts.
# Swap this import once validation is ready.
from parser import validate  

load_dotenv()
API_KEY = os.getenv("GOOGLE_AI_API_KEY")

# ── In-memory store ───────────────────────────────────────────────────────────
# Structure: { file_id: FileRecord }
_store: dict[str, dict[str, Any]] = {}


# ── Pydantic response models (must match frontend ReviewFile type) ─────────────
class ErrorBlock(BaseModel):
    field:   str
    value:   str
    message: str


class FileRecord(BaseModel):
    id:          str
    batchNumber: str
    sapMaterial: str
    processStep: str
    status:      str          # "ok" | "error" | "warn"
    errors:      list[ErrorBlock]
    data_blocks: list[dict]   # full validated blocks kept for export


# ── Helpers ───────────────────────────────────────────────────────────────────

def _status_from_blocks(blocks: list[dict]) -> str:
    """Derive dashboard status from the validated data blocks."""
    has_error = any(b.get("flags") for b in blocks)
    if not has_error:
        return "ok"
    # Distinguish hard errors from soft warnings by a flag key convention.
    # Your validator can set flag keys starting with "warn_" for warnings.
    all_warn = all(
        all(k.startswith("warn_") for k in b["flags"])
        for b in blocks if b.get("flags")
    )
    return "warn" if all_warn else "error"


def _errors_from_blocks(blocks: list[dict]) -> list[ErrorBlock]:
    """Flatten flags from all data blocks into the ErrorBlock list the frontend expects."""
    errors = []
    for block in blocks:
        for flag_key, flag_msg in (block.get("flags") or {}).items():
            errors.append(ErrorBlock(
                field=block.get("parameter", "Unknown field"),
                value=str(block.get("actual_value") or "—"),
                message=f"[{flag_key}] {flag_msg}",
            ))
    return errors


def _produktinfo_to_meta(ocr_result: dict) -> tuple[str, str, str]:
    """
    Pull Batch Number, SAP Material, and Process Step from the
    'Produktinfo' chapter that OCRProcessor always extracts from page 1.
    Falls back to placeholders if keys aren't found.
    """
    info = ocr_result.get("Produktinfo", {})
    sap  = info.get("SAP-Materialnummer", "—")
    step = info.get("Prozessstufe", "—")
    # Batch number is typically part of the filename or a dedicated chapter field.
    # Adjust the key name to match what your OCR actually returns.
    batch = info.get("Chargennummer", info.get("Batch", "—"))
    return batch, sap, step


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Batch Review API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/files", response_model=list[FileRecord])
def get_files():
    return [FileRecord(**r) for r in _store.values()]


@app.post("/upload", response_model=list[FileRecord])
async def upload_pdfs(files: list[UploadFile] = File(...)):
    created = []

    for upload in files:
        if upload.content_type != "application/pdf":
            raise HTTPException(400, f"{upload.filename} is not a PDF.")

        # Save upload to a temp file so pdfConverter can open it
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(await upload.read())
            tmp_path = tmp.name

        try:
            # 1. PDF → images
            pages = convert_pdf_to_images(tmp_path, target_dpi=300)

            # 2. Images → raw OCR dict  (your existing OCRProcessor)
            ocr_result = extract_chapters_from_images(pages, api_key=API_KEY)

            # 3. Raw OCR → validated data_blocks  (your team's module)
            data_blocks = validate(ocr_result)

        finally:
            Path(tmp_path).unlink(missing_ok=True)

        # 4. Build the record the frontend needs
        batch, sap, step = _produktinfo_to_meta(ocr_result)
        file_id = str(uuid.uuid4())

        record = {
            "id":          file_id,
            "batchNumber": batch,
            "sapMaterial": sap,
            "processStep": step,
            "status":      _status_from_blocks(data_blocks),
            "errors":      [e.model_dump() for e in _errors_from_blocks(data_blocks)],
            "data_blocks": data_blocks,
        }
        _store[file_id] = record
        created.append(FileRecord(**record))

    return created


@app.delete("/files")
def delete_all_files():
    _store.clear()
    return {"deleted": True}


class ExportRequest(BaseModel):
    mode:     str          # "all" | "no_error" | "selected"
    file_ids: list[str]    # used only when mode == "selected"


@app.post("/export")
def export_files(req: ExportRequest):
    if req.mode == "all":
        records = list(_store.values())
    elif req.mode == "no_error":
        records = [r for r in _store.values() if r["status"] == "ok"]
    elif req.mode == "selected":
        records = [_store[fid] for fid in req.file_ids if fid in _store]
    else:
        raise HTTPException(400, f"Unknown export mode: {req.mode}")

    if not records:
        raise HTTPException(404, "No matching files to export.")

    # Flatten all data blocks from every selected file into one sheet.
    # Each file gets a section break row so the reviewer can tell them apart.
    all_blocks: list[dict] = []
    for rec in records:
        # Section header pseudo-block (no flags, styled as meta by the exporter)
        all_blocks.append({
            "parameter":      f"── Batch {rec['batchNumber']} ({rec['sapMaterial']}) ──",
            "expected_value": "",
            "actual_value":   "",
            "page_number":    "",
            "line_number":    "",
            "flags":          {},
            "_section_header": True,   # jsonToExcel can detect this for grey styling
        })
        all_blocks.extend(rec["data_blocks"])

    # Write to an in-memory buffer so we can stream it back
    buf = io.BytesIO()
    export_to_excel(
        data_blocks=all_blocks,
        output_path=buf,          # jsonToExcel accepts a file-like object too (see note)
        sheet_name="Batch Review",
    )
    buf.seek(0)

    filename = f"batch_review_{req.mode}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )