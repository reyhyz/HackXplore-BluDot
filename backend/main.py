"""
main.py  (backend/main.py)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import io
import json
import os
import uuid
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dotenv import load_dotenv
from agent.ocrProcessor import extract_chapters_from_images
from agent.pdfConverter import convert_pdf_to_images
from parser.jsonToExcel import export_to_excel
from parser.validator import validate, _to_data_blocks

load_dotenv()
API_KEY      = os.getenv("GOOGLE_AI_API_KEY")
_BACKEND_DIR = Path(__file__).resolve().parent
_OUTPUTS_DIR = _BACKEND_DIR / "data" / "outputs"
_MOCK_PATH   = _BACKEND_DIR.parent / "data" / "outputs" / "mock_batches.json"

_store: dict[str, dict[str, Any]] = {}


# ── Pydantic models ───────────────────────────────────────────────────────────

class ErrorBlock(BaseModel):
    field:    str
    value:    str
    message:  str
    severity: str = "error"


class FileRecord(BaseModel):
    id:          str
    batchNumber: str
    sapMaterial: str
    processStep: str
    status:      str
    errors:      list[ErrorBlock]
    data_blocks: list[dict]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _produktinfo_to_meta(doc: dict) -> tuple[str, str, str]:
    info = doc.get("Produktinfo", {})
    return (
        info.get("Batch No.",          "—"),
        info.get("SAP-Materialnummer", "—"),
        info.get("Prozessstufe",       "—"),
    )


def _save_to_historical_store(
    verified_doc: dict,
    sap_material: str,
    process_step: str,
    batch_number: str,
) -> None:
    if not sap_material or not process_step:
        print("[SAVE] Skipping — missing sapMaterial or processStep")
        return

    target_dir = _OUTPUTS_DIR / sap_material / process_step
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = batch_number.replace("/", "-").replace("\\", "-") or str(uuid.uuid4())
    out_file  = target_dir / f"{safe_name}.json"
    out_file.write_text(
        json.dumps(verified_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SAVE] ✓ Written → {out_file}")


def _status_from_blocks(blocks: list[dict]) -> str:
    has_error   = any("error"   in b.get("flags", {}) for b in blocks)
    has_unclear = any("unclear" in b.get("flags", {}) for b in blocks)
    if has_error:
        return "error"
    if has_unclear:
        return "warn"
    return "ok"


def _errors_from_blocks(blocks: list[dict]) -> list[ErrorBlock]:
    errors = []
    for block in blocks:
        for flag_key, flag_msg in (block.get("flags") or {}).items():
            severity = "warn" if flag_key == "unclear" else "error"
            errors.append(ErrorBlock(
                field=block.get("parameter", "Unknown field"),
                value=str(block.get("actual_value") or "—"),
                message=flag_msg,
                severity=severity,
            ))
    return errors


def _load_mock_batch(batch_name: str, verified_doc: dict) -> dict | None:
    """
    Konvertiert einen Eintrag aus mock_batches.json in einen _store-Datensatz.
    Mappt die verschachtelten 'Errors' und 'Unclear' Felder auf das flache
    flags-System für das Frontend.
    """
    batch_number, sap_material, process_step = _produktinfo_to_meta(verified_doc)

    # Relevante Metadaten für das System anhängen
    verified_doc["sapMaterial"] = sap_material
    verified_doc["processStep"] = process_step

    # 1. Standardmäßige Konvertierung in Datenblöcke durchführen
    data_blocks = _to_data_blocks(verified_doc)
    
    # 2. Mock-Fehler ("Errors" & "Unclear") extrahieren und in Datenblöcke injizieren
    for section_key, section_data in verified_doc.items():
        if not isinstance(section_data, dict) or section_key == "Produktinfo":
            continue
            
        mock_errors = section_data.get("Errors", {})
        mock_unclear = section_data.get("Unclear", {})
        
        if mock_errors or mock_unclear:
            for block in data_blocks:
                # Prüfen, ob der Block zu diesem Kapitel und Parameter gehört
                # (Hier wird angenommen, dass _to_data_blocks ein Feld wie 'parameter' oder ein Kapitel-Matching nutzt)
                param_name = block.get("parameter")
                
                if block.get("flags") is None:
                    block["flags"] = {}
                
                # Wenn für diesen Parameter ein Fehler im Mock-JSON existiert:
                if param_name in mock_errors:
                    block["flags"]["error"] = mock_errors[param_name]
                    # Aktualisiere den tatsächlichen Wert, falls im Mock "EMPTY" o.ä. steht
                    if block.get("actual_value") == "EMPTY":
                        block["actual_value"] = section_data.get(param_name, "—")
                        
                # Wenn für diesen Parameter Unklarheiten im Mock-JSON existieren:
                if param_name in mock_unclear:
                    block["flags"]["unclear"] = mock_unclear[param_name]

    file_id = str(uuid.uuid4())

    return {
        "id":          file_id,
        "batchNumber": batch_number,
        "sapMaterial": sap_material,
        "processStep": process_step,
        "status":      _status_from_blocks(data_blocks),
        "errors":      [e.model_dump() for e in _errors_from_blocks(data_blocks)],
        "data_blocks": data_blocks,
    }


def _seed_mock_data() -> None:
    """Load mock_batches.json into _store at startup."""
    if not _MOCK_PATH.exists():
        print(f"[MOCK] No mock file found at {_MOCK_PATH} — skipping.")
        return

    try:
        raw = json.loads(_MOCK_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[MOCK] Failed to read mock file: {e}")
        return

    loaded = 0
    for batch_name, verified_doc in raw.items():
        if not isinstance(verified_doc, dict):
            continue
        try:
            record = _load_mock_batch(batch_name, verified_doc)
            if record:
                _store[record["id"]] = record
                loaded += 1
        except Exception as e:
            print(f"[MOCK] Skipping '{batch_name}': {e}")

    print(f"[MOCK] Loaded {loaded} mock batch(es) into dashboard.")


#── App ───────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_mock_data()
    yield  


app = FastAPI(title="Batch Review API", lifespan=lifespan)

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

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(await upload.read())
            tmp_path = tmp.name

        try:
            # 1. PDF → images
            pages = convert_pdf_to_images(tmp_path, target_dpi=300)
            print(f"[UPLOAD] Converted to {len(pages)} page(s)")

            # 2. Images → raw OCR dict
            ocr_result = extract_chapters_from_images(pages, api_key=API_KEY)
            print(f"[UPLOAD] OCR chapters: {list(ocr_result.keys())}")

            # 3. Read identity fields
            batch_number, sap_material, process_step = _produktinfo_to_meta(ocr_result)
            print(f"[UPLOAD] Produktinfo → batch={batch_number!r}  sap={sap_material!r}  step={process_step!r}")

            # 4. Hoist to doc root for statistical scoping
            ocr_result["sapMaterial"] = sap_material
            ocr_result["processStep"] = process_step

            # 5. Validate → (annotated doc, flat ui blocks)
            verified_doc, data_blocks = validate(ocr_result)
            print(f"[UPLOAD] data_blocks={len(data_blocks)}  flagged={sum(1 for b in data_blocks if b.get('flags'))}")

            # 6. Persist to historical store
            _save_to_historical_store(verified_doc, sap_material, process_step, batch_number)

        finally:
            Path(tmp_path).unlink(missing_ok=True)

        # 7. Build frontend record
        file_id = str(uuid.uuid4())
        errors  = _errors_from_blocks(data_blocks)
        status  = _status_from_blocks(data_blocks)
        print(f"[UPLOAD] status={status!r}  error_blocks={len(errors)}")

        record = {
            "id":          file_id,
            "batchNumber": batch_number,
            "sapMaterial": sap_material,
            "processStep": process_step,
            "status":      status,
            "errors":      [e.model_dump() for e in errors],
            "data_blocks": data_blocks,
        }
        _store[file_id] = record
        created.append(FileRecord(**record))

    return created


@app.delete("/files")
def delete_all_files():
    """Clears real uploads but preserves mock data."""
    # Re-seed so mock entries are always present after a remove-all
    _store.clear()
    _seed_mock_data()
    return {"deleted": True}


class ExportRequest(BaseModel):
    mode:     str
    file_ids: list[str]


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

    all_blocks: list[dict] = []
    for rec in records:
        all_blocks.append({
            "parameter":       f"── Batch {rec['batchNumber']}  |  SAP {rec['sapMaterial']}  |  {rec['processStep']} ──",
            "expected_value":  "",
            "actual_value":    "",
            "page_number":     "",
            "line_number":     "",
            "flags":           {},
            "_section_header": True,
        })
        all_blocks.extend(rec["data_blocks"])

    buf = io.BytesIO()
    export_to_excel(data_blocks=all_blocks, output_path=buf, sheet_name="Batch Review")
    buf.seek(0)

    filename = f"batch_review_{req.mode}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )