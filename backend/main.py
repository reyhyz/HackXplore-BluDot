# backend/main.py
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="HackXplore BluDot API",
    version="0.1.0",
    description="FastAPI backend for the Review Dashboard frontend.",
)

# ── CORS Configuration ────────────────────────────────────────────────────

origins = [
    "http://localhost:5173",  # Default local Vite port
    "http://127.0.0.1:5173", # Change to domain for actual deployment
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────

class FileError(BaseModel):
    field: str
    value: str
    message: str

class ReviewFile(BaseModel):
    processStep: str
    sapMaterial: str
    batchNumber: str = Field(..., pattern=r"^\d{7}$")
    status: str  # "error", "ok", or "warn"
    errors: list[FileError] = []

# ── Mock Data ─────────────────────────────────────────────────────────────

_mock_files = [
    ReviewFile(
        processStep="001",
        sapMaterial="MAT-123456",
        batchNumber="1234567",
        status="ok",
        errors=[]
    ),
    ReviewFile(
        processStep="002",
        sapMaterial="MAT-789012",
        batchNumber="2345678",
        status="error",
        errors=[
            FileError(field="Material", value="INVALID", message="Material code format invalid"),
            FileError(field="Batch", value="—", message="Batch number cannot be determined"),
        ]
    ),
    ReviewFile(
        processStep="003",
        sapMaterial="MAT-345678",
        batchNumber="3456789",
        status="warn",
        errors=[
            FileError(field="Handwriting", value="—", message="Unrecognized handwriting detected in field"),
        ]
    ),
]

# ── Health Check ──────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "HackXplore BluDot API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ── Files Endpoints ───────────────────────────────────────────────────────

@app.get("/api/files", response_model=list[ReviewFile])
def get_files():
    """Fetch all processed files."""
    return _mock_files

@app.get("/api/files/{file_id}", response_model=ReviewFile)
def get_file(file_id: str):
    """Fetch a specific file by ID."""
    for file in _mock_files:
        if file.processStep == file_id:
            return file
    raise HTTPException(status_code=404, detail="File not found")

@app.delete("/api/files/{file_id}")
def delete_file(file_id: str):
    """Delete a specific file."""
    global _mock_files
    _mock_files = [f for f in _mock_files if f.processStep != file_id]
    return {"message": f"File {file_id} deleted"}

@app.delete("/api/files")
def delete_all_files():
    """Delete all files."""
    global _mock_files
    _mock_files = []
    return {"message": "All files deleted"}

# ── Upload Endpoint ───────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Upload one or more PDF files for processing.
    Returns a list of newly created ReviewFile objects.
    """
    uploaded = []
    for file in files:
        # TODO: Process the PDF file here
        new_file = ReviewFile(
            processStep=f"UPL-{len(_mock_files) + 1:03d}",
            sapMaterial="MAT-NEW",
            batchNumber=f"{1000000 + len(_mock_files):07d}",
            status="ok",
            errors=[]
        )
        _mock_files.append(new_file)
        uploaded.append(new_file)
    return uploaded

# ── Export Endpoint ───────────────────────────────────────────────────────

@app.get("/api/export")
def export_files(mode: str, ids: Optional[list[str]] = None):
    """
    Export files as Excel. 
    Modes: 'all', 'no_error', 'selected'
    """
    if mode == "all":
        to_export = _mock_files
    elif mode == "no_error":
        to_export = [f for f in _mock_files if f.status == "ok"]
    elif mode == "selected":
        to_export = [f for f in _mock_files if f.processStep in (ids or [])]
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # TODO: Generate actual Excel file
    # For now, return a simple JSON response
    return {"exported_files": len(to_export), "files": to_export}