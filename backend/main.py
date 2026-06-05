"""
main.py – FastAPI. Dopo il parsing chiama Gemini per formattazione e chunking.
"""

import os, io, uuid, tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

from parser import (parse_document, propose_colors, apply_colors,
                    COLOR_META, split_at_max_chars)
from ai import rework_text, split_sentences_smart, rework_ita_plus

app = FastAPI(title="Soprattitoli Generator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

sessions: dict[str, list[dict]] = {}

# ── Modelli ────────────────────────────────────────────────────────────────────

class Criteria(BaseModel):
    session_id: str
    name_caps:   bool = True
    name_bold:   bool = False
    name_custom: str  = ""
    name_sep:    bool = True
    sep_char:    str  = " – "
    desc_italic: bool = True
    desc_parens: bool = True
    max_chars:   int  = 42

class ColorAssignment(BaseModel):
    session_id: str
    assignments: dict[str, str]

class ReworkRequest(BaseModel):
    sentences: list[str]

class UpdateRow(BaseModel):
    session_id: str
    index: int
    field: str
    value: str

class ExportRequest(BaseModel):
    session_id: str

class ItaPlusProcess(BaseModel):
    session_id: str
    column_index: int = 2

class ItaPlusUpdate(BaseModel):
    session_id: str
    row_index: int
    value: str

class ItaPlusSave(BaseModel):
    session_id: str


# ── ITA: Upload ────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, "Solo file .docx supportati.")
    content = await file.read()
    sid = str(uuid.uuid4())
    tmp = Path(tempfile.gettempdir()) / "soprattitoli"
    tmp.mkdir(exist_ok=True)
    (tmp / f"{sid}.docx").write_bytes(content)
    return {"session_id": sid, "filename": file.filename}


# ── ITA: Processa + Formattazione AI a Chunk ───────────────────────────────────

@app.post("/api/process")
async def process(criteria: Criteria):
    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{criteria.session_id}.docx"
    if not tmp_path.exists():
        raise HTTPException(404, "Sessione non trovata.")
    try:
        rows_from_parser = parse_document(str(tmp_path), {
            "name_caps":   criteria.name_caps,
            "name_bold":   criteria.name_bold,
            "name_custom": criteria.name_custom,
            "name_sep":    criteria.name_sep,
            "sep_char":    criteria.sep_char,
            "desc_italic": criteria.desc_italic,
            "desc_parens": criteria.desc_parens,
        })
    except Exception as e:
        raise HTTPException(500, f"Errore parsing: {e}")

    sentences_to_process = [r["ita"] for r in rows_from_parser if r.get("ita")]
    expanded = []
    
    try:
        # L'AI ci restituisce una lista di testi formattati con gli "a capo" (\n)
        ai_results = rework_
