"""
main.py – Server FastAPI per Soprattitoli Generator.
Percorsi: ITA (copione Word) e ITA+ (Excel esistente).
"""

import os
import io
import uuid
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

from parser import parse_document, propose_colors, apply_colors, COLOR_META, split_at_max_chars
from ai import rework_text, split_lines_ai, rework_ita_plus

app = FastAPI(title="Soprattitoli Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class SplitRequest(BaseModel):
    sentence: str
    max_chars: int = 42
    use_ai: bool = False

class UpdateRow(BaseModel):
    session_id: str
    index: int
    field: str
    value: str

class ExportRequest(BaseModel):
    session_id: str

class ItaPlusProcess(BaseModel):
    session_id: str
    column_index: int = 2   # indice colonna ITA (0-based), default 3a colonna

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
    session_id = str(uuid.uuid4())
    tmp_dir = Path(tempfile.gettempdir()) / "soprattitoli"
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / f"{session_id}.docx").write_bytes(content)
    return {"session_id": session_id, "filename": file.filename}


# ── ITA: Processa ──────────────────────────────────────────────────────────────

@app.post("/api/process")
async def process(criteria: Criteria):
    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{criteria.session_id}.docx"
    if not tmp_path.exists():
        raise HTTPException(404, "Sessione non trovata. Ricarica il file.")
    try:
        rows = parse_document(str(tmp_path), {
            "name_caps":   criteria.name_caps,
            "name_bold":   criteria.name_bold,
            "name_custom": criteria.name_custom,
            "name_sep":    criteria.name_sep,
            "sep_char":    criteria.sep_char,
            "desc_italic": criteria.desc_italic,
            "desc_parens": criteria.desc_parens,
            "max_chars":   criteria.max_chars,
        })
    except Exception as e:
        raise HTTPException(500, f"Errore elaborazione: {e}")
    sessions[criteria.session_id] = rows
    colors = propose_colors(rows)
    return {
        "rows": rows,
        "total": len(rows),
        "characters": len({r["personaggio"] for r in rows if r["personaggio"]}),
        "proposed_colors": colors,
    }


# ── ITA: Colori ────────────────────────────────────────────────────────────────

@app.post("/api/colors")
async def set_colors(body: ColorAssignment):
    rows = sessions.get(body.session_id)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")
    updated = apply_colors(rows, body.assignments)
    sessions[body.session_id] = updated
    return {"rows": updated}


# ── ITA: Rielabora con AI ──────────────────────────────────────────────────────

@app.post("/api/rework")
async def rework(body: ReworkRequest):
    if not body.sentences:
        raise HTTPException(400, "Nessuna battuta.")
    try:
        return {"reworked": rework_text(body.sentences)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── ITA: Suddividi riga ────────────────────────────────────────────────────────

@app.post("/api/split")
async def split_line(body: SplitRequest):
    """Suddivide una battuta in righe da max_chars. Algoritmo o AI."""
    if body.use_ai:
        try:
            lines = split_lines_ai(body.sentence, body.max_chars)
        except Exception as e:
            raise HTTPException(500, str(e))
    else:
        lines = split_at_max_chars(body.sentence, body.max_chars)
    return {"lines": lines}


# ── ITA: Aggiorna riga ─────────────────────────────────────────────────────────

@app.post("/api/update-row")
async def update_row(body: UpdateRow):
    rows = sessions.get(body.session_id)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")
    if body.index < 0 or body.index >= len(rows):
        raise HTTPException(400, "Indice non valido.")
    if body.field not in ("ita", "note", "colore", "personaggio"):
        raise HTTPException(400, "Campo non valido.")
    rows[body.index][body.field] = body.value
    return {"ok": True}


# ── ITA: Esporta Excel ─────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_excel(body: ExportRequest):
    rows = sessions.get(body.session_id)
    if not rows:
        raise HTTPException(404, "Nessun dato.")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Soprattitoli"
    ws.append(["Colore", "Personaggio", "ITA", "Note"])
    hdr_fill = PatternFill(start_color="FF0D47A1", end_color="FF0D47A1", fill_type="solid")
    hdr_font = Font(bold=True, color="FFFFFFFF")
    for cell in ws[1]:
        cell.fill = hdr_fill
        cell.font = hdr_font
    align = Alignment(wrap_text=True, vertical="top")
    for i, row in enumerate(rows, start=2):
        ws.cell(i, 1, row.get("colore", ""))
        ws.cell(i, 2, row.get("personaggio", ""))
        ws.cell(i, 3, row.get("ita", ""))
        ws.cell(i, 4, row.get("note", ""))
        ck = row.get("colore", "")
        if ck in COLOR_META:
            hx = COLOR_META[ck]["hex"].lstrip("#")
            ws.cell(i, 1).fill = PatternFill(start_color=f"FF{hx}", end_color=f"FF{hx}", fill_type="solid")
        for col in range(1, 5):
            ws.cell(i, col).alignment = align
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 65
    ws.column_dimensions["D"].width = 32
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=soprattitoli.xlsx"}
    )


# ── ITA+: Upload Excel ─────────────────────────────────────────────────────────

@app.post("/api/itaplus/upload")
async def itaplus_upload(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Solo file .xlsx supportati.")
    content = await file.read()
    session_id = str(uuid.uuid4())
    tmp_dir = Path(tempfile.gettempdir()) / "soprattitoli"
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / f"{session_id}_itaplus.xlsx").write_bytes(content)

    # Leggi intestazioni per mostrare all'utente
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    return {
        "session_id": session_id,
        "filename": file.filename,
        "headers": headers,
        "rows": ws.max_row - 1
    }


# ── ITA+: Processa (riformula con Gemini) ─────────────────────────────────────

@app.post("/api/itaplus/process")
async def itaplus_process(body: ItaPlusProcess):
    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{body.session_id}_itaplus.xlsx"
    if not tmp_path.exists():
        raise HTTPException(404, "File non trovato.")

    wb = openpyxl.load_workbook(str(tmp_path))
    ws = wb.active
    col = body.column_index + 1  # 1-based

    # Raccogli tutte le frasi ITA
    sentences = []
    for r in range(2, ws.max_row + 1):
        val = ws.cell(r, col).value
        sentences.append(str(val) if val else "")

    # Riformula con Gemini (solo frasi non vuote)
    non_empty = [(i, s) for i, s in enumerate(sentences) if s.strip()]
    reworked_map = {}
    if non_empty:
        try:
            results = rework_ita_plus([s for _, s in non_empty])
            for idx, (orig_i, _) in enumerate(non_empty):
                reworked_map[orig_i] = results[idx] if idx < len(results) else ""
        except Exception as e:
            raise HTTPException(500, f"Errore Gemini: {e}")

    # Costruisci lista di righe con originale + proposta
    rows_out = []
    for i, orig in enumerate(sentences):
        rows_out.append({
            "index": i,
            "original": orig,
            "proposed": reworked_map.get(i, orig),
            "accepted": reworked_map.get(i, orig),  # editabile dall'utente
        })

    sessions[f"{body.session_id}_itaplus"] = rows_out
    sessions[f"{body.session_id}_itaplus_col"] = body.column_index

    return {"rows": rows_out, "total": len(rows_out)}


# ── ITA+: Aggiorna proposta ────────────────────────────────────────────────────

@app.post("/api/itaplus/update")
async def itaplus_update(body: ItaPlusUpdate):
    key = f"{body.session_id}_itaplus"
    rows = sessions.get(key)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")
    if body.row_index < 0 or body.row_index >= len(rows):
        raise HTTPException(400, "Indice non valido.")
    rows[body.row_index]["accepted"] = body.value
    return {"ok": True}


# ── ITA+: Salva nel file Excel ─────────────────────────────────────────────────

@app.post("/api/itaplus/save")
async def itaplus_save(body: ItaPlusSave):
    key = f"{body.session_id}_itaplus"
    rows = sessions.get(key)
    col_idx = sessions.get(f"{body.session_id}_itaplus_col", 2)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")

    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{body.session_id}_itaplus.xlsx"
    wb = openpyxl.load_workbook(str(tmp_path))
    ws = wb.active

    # Aggiungi intestazione colonna ITA+
    new_col = ws.max_column + 1
    ws.cell(1, new_col, "ITA+")
    ws.cell(1, new_col).font = Font(bold=True, color="FFFFFFFF")
    ws.cell(1, new_col).fill = PatternFill(start_color="FF0D47A1", end_color="FF0D47A1", fill_type="solid")

    for i, row in enumerate(rows):
        ws.cell(i + 2, new_col, row.get("accepted", ""))
        ws.cell(i + 2, new_col).alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions[openpyxl.utils.get_column_letter(new_col)].width = 55

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=soprattitoli_itaplus.xlsx"}
    )


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}
