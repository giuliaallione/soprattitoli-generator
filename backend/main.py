# ── ITA: Processa + split AI ───────────────────────────────────────────────────

@app.post("/api/process")
async def process(criteria: Criteria):
    tmp_path = Path(tempfile.gettempdir()) / "soprattitoli" / f"{criteria.session_id}.docx"
    if not tmp_path.exists():
        raise HTTPException(404, "Sessione non trovata.")
    try:
        # Il tuo parser esistente estrae il testo dal Word
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

    # Estraiamo le frasi grezze e i colori
    sentences_to_process = [r["ita"] for r in rows_from_parser if r.get("ita")]
    
    expanded = []
    
    try:
        # Chiamiamo la NUOVA funzione AI che ci restituisce la lista di dizionari {personaggio, testo}
        ai_results = rework_text(sentences_to_process)
        
        # Uniamo i risultati dell'AI con i colori estratti dal parser
        for row_parser, ai_data in zip(rows_from_parser, ai_results):
            # Assicuriamoci che ai_data sia un dizionario (per evitare errori se l'AI impazzisce)
            if isinstance(ai_data, dict):
                personaggio = ai_data.get("personaggio", row_parser.get("personaggio", ""))
                testo = ai_data.get("testo", "")
            else:
                # Fallback di sicurezza se Gemini restituisce per errore una stringa
                personaggio = row_parser.get("personaggio", "")
                testo = str(ai_data)
                
            expanded.append({
                "colore":      row_parser.get("colore", ""),
                "personaggio": personaggio,
                "ita":         testo,
                "note":        row_parser.get("note", "")
            })
            
    except Exception as e:
        # Fallback algoritmico se Gemini va in errore
        print(f"Errore Gemini durante process, uso fallback: {e}")
        for row in rows_from_parser:
            if row["ita"]:
                for j, line in enumerate(split_at_max_chars(row["ita"], criteria.max_chars)):
                    expanded.append({
                        "colore":      row["colore"],
                        "personaggio": row["personaggio"],
                        "ita":         line,
                        "note":        row["note"] if j == 0 else "",
                    })
            else:
                expanded.append(row)

    sessions[criteria.session_id] = expanded
    colors = propose_colors(expanded)
    
    return {
        "rows": expanded,
        "total": len(expanded),
        "characters": len({r["personaggio"] for r in expanded if r.get("personaggio")}),
        "proposed_colors": colors,
    }
