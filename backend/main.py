"""
main.py – Server FastAPI per Soprattitoli Generator (web version).
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

from parser import parse_document, propose_colors, apply_colors, COLOR_META
from ai import rework_text

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Soprattitoli Generator API")

# Permette al frontend (React) di comunicare col backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage temporaneo in memoria (va bene per 3 utenti)
# sessions = { session_id: [lista righe] }
sessions: dict[str, list[dict]] = {}


# ── Modelli dati ───────────────────────────────────────────────────────────────

class Criteria(BaseModel):
    session_id: str
    name_caps: bool = True
    name_sep: bool = True
    sep_char: str = " – "
    desc_italic: bool = True
    desc_parens: bool = True

class ColorAssignment(BaseModel):
    session_id: str
    assignments: dict[str, str]  # {'NOME': 'w', 'ALTRO': 'c'}

class ReworkRequest(BaseModel):
    sentences: list[str]

class ExportRequest(BaseModel):
    session_id: str


# ── Route: upload file ─────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Riceve il file .docx, lo salva temporaneamente,
    ritorna un session_id da usare nelle chiamate successive.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(400, "Solo file .docx sono supportati.")

    content = await file.read()
    session_id = str(uuid.uuid4())

    # Salva il file in una cartella temporanea
    tmp_dir = Path(tempfile.gettempdir()) / "soprattitoli"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"{session_id}.docx"
    tmp_path.write_bytes(content)

    return {"session_id": session_id, "filename": file.filename}


# ── Route: processa con criteri ────────────────────────────────────────────────

@app.post("/api/process")
async def process(criteria: Criteria):
    """
    Legge il .docx con i criteri indicati,
    ritorna le righe parsed e la proposta colori.
    """
    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{criteria.session_id}.docx"
    if not tmp_path.exists():
        raise HTTPException(404, "Sessione non trovata. Ricarica il file.")

    try:
        rows = parse_document(
            str(tmp_path),
            {
                "name_caps":   criteria.name_caps,
                "name_sep":    criteria.name_sep,
                "sep_char":    criteria.sep_char,
                "desc_italic": criteria.desc_italic,
                "desc_parens": criteria.desc_parens,
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Errore di elaborazione: {e}")

    sessions[criteria.session_id] = rows
    colors = propose_colors(rows)

    return {
        "rows": rows,
        "total": len(rows),
        "characters": len({r["personaggio"] for r in rows if r["personaggio"]}),
        "proposed_colors": colors,
    }


# ── Route: assegna colori ──────────────────────────────────────────────────────

@app.post("/api/colors")
async def set_colors(body: ColorAssignment):
    """Applica i colori alle righe della sessione."""
    rows = sessions.get(body.session_id)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")

    updated = apply_colors(rows, body.assignments)
    sessions[body.session_id] = updated
    return {"rows": updated}


# ── Route: rielaborazione AI ───────────────────────────────────────────────────

@app.post("/api/rework")
async def rework(body: ReworkRequest):
    """
    Invia le battute a Gemini e ritorna le versioni rielaborate.
    Non modifica la sessione — è il frontend a decidere se accettare.
    """
    if not body.sentences:
        raise HTTPException(400, "Nessuna battuta da rielaborare.")
    try:
        result = rework_text(body.sentences)
        return {"reworked": result}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Route: aggiorna riga singola ───────────────────────────────────────────────

class UpdateRow(BaseModel):
    session_id: str
    index: int
    field: str   # 'ita', 'note', 'colore', 'personaggio'
    value: str

@app.post("/api/update-row")
async def update_row(body: UpdateRow):
    """Aggiorna un singolo campo di una singola riga."""
    rows = sessions.get(body.session_id)
    if rows is None:
        raise HTTPException(404, "Sessione non trovata.")
    if body.index < 0 or body.index >= len(rows):
        raise HTTPException(400, "Indice riga non valido.")
    if body.field not in ("ita", "note", "colore", "personaggio"):
        raise HTTPException(400, "Campo non valido.")

    rows[body.index][body.field] = body.value
    return {"ok": True}


# ── Route: esporta Excel ───────────────────────────────────────────────────────

@app.post("/api/export")
async def export_excel(body: ExportRequest):
    """Genera e scarica il file .xlsx con la tabella completa."""
    rows = sessions.get(body.session_id)
    if not rows:
        raise HTTPException(404, "Nessun dato da esportare.")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Soprattitoli"

    headers = ["Colore", "Personaggio", "ITA", "Note"]
    ws.append(headers)

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

        # Colora la cella Colore con il colore assegnato
        color_key = row.get("colore", "")
        if color_key in COLOR_META:
            hex_color = COLOR_META[color_key]["hex"].lstrip("#")
            ws.cell(i, 1).fill = PatternFill(
                start_color=f"FF{hex_color}",
                end_color=f"FF{hex_color}",
                fill_type="solid"
            )

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


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}
