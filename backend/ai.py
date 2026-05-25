"""
ai.py – Integrazione Google Gemini con gemini-1.5-flash su API v1.
"""

import os
import json
import urllib.request
import urllib.error

# API v1 (stabile) + gemini-1.5-flash
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent"
)

REGOLE_BASE = """REGOLE DI FORMATTAZIONE (obbligatorie):
1. Ogni riga ha MASSIMO 42 caratteri, spazi compresi.
2. I numeri da zero a dieci si scrivono in lettere. I numeri maggiori di dieci in cifre arabe. Qualsiasi numero a inizio frase va scritto in lettere.
3. I due punti si usano SOLO per i discorsi diretti, seguiti da uno spazio singolo.
4. Il punto e virgola NON è consentito. Sostituiscilo con una virgola o spezza la frase.
5. I tre puntini di sospensione si usano SOLO per frasi volutamente incomplete.
6. Cambia il presente progressivo in presente semplice: "Sto piangendo" → "Piango".
7. Preferisci l'ordine soggetto-verbo-complemento.
8. NON saltare né censurare alcuna frase.
9. La divisione tra le righe deve rispettare la grammatica italiana.
10. Nessuna punteggiatura finale aggiunta."""

SPLIT_SMART_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Ricevi un elenco numerato di battute. Per ciascuna:
- Se già entro 42 caratteri, restituiscila invariata
- Se più lunga, dividila in righe di senso compiuto di max 42 caratteri

{REGOLE_BASE}

Rispondi ESCLUSIVAMENTE con un oggetto JSON:
{{"results": [["riga1"], ["riga1", "riga2"], ...]}}
Ogni elemento corrisponde alla battuta con lo stesso indice.
Nessun testo aggiuntivo, nessun backtick."""

REWORK_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Rielabora le battute elencate applicando queste regole.

{REGOLE_BASE}

Rispondi ESCLUSIVAMENTE con un array JSON di stringhe.
Esempio: ["Prima riga", "Seconda riga se necessario"]
Nessun testo aggiuntivo, nessun backtick."""

ITA_PLUS_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Riformula le frasi per la colonna ITA+ applicando queste regole.
Puoi riscrivere liberamente mantenendo il significato.

{REGOLE_BASE}
- Massimo 37 caratteri per riga in questo percorso.

Rispondi ESCLUSIVAMENTE con un array JSON di stringhe.
Nessun testo aggiuntivo, nessun backtick."""


def _call_gemini(payload: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY non configurata.")
    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Errore Gemini ({e.code}): {e.read().decode()}")


def _extract_text(body: dict) -> str:
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
        return text
    except Exception as e:
        raise RuntimeError(f"Risposta Gemini non valida: {e}\n{body}")


def split_sentences_smart(sentences: list[str], max_chars: int = 42) -> list[list[str]]:
    indexed = [(i, s) for i, s in enumerate(sentences) if s and s.strip()]
    if not indexed:
        return [[] for _ in sentences]

    user_text = "Elabora queste battute:\n\n" + "\n".join(
        f"{i}. {s}" for i, s in indexed
    )
    payload = {
        "contents": [{"parts": [{"text": SPLIT_SMART_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
    }
    body = _call_gemini(payload)
    raw = _extract_text(body)

    try:
        parsed = json.loads(raw)
        results_list = parsed.get("results", [])
    except Exception:
        try:
            results_list = json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"Risposta split non valida: {e}\n{raw}")

    result_map = {}
    for pos, (orig_i, orig_s) in enumerate(indexed):
        if pos < len(results_list):
            val = results_list[pos]
            result_map[orig_i] = [str(r) for r in val if str(r).strip()] if isinstance(val, list) else [str(val)]
        else:
            result_map[orig_i] = [orig_s]

    return [result_map.get(i, [s] if s else []) for i, s in enumerate(sentences)]


def rework_text(sentences: list[str]) -> list[str]:
    user_text = "Rielabora:\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    payload = {
        "contents": [{"parts": [{"text": REWORK_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
    }
    body = _call_gemini(payload)
    result = json.loads(_extract_text(body))
    return [str(s) for s in result] if isinstance(result, list) else [str(result)]


def rework_ita_plus(sentences: list[str]) -> list[str]:
    user_text = "Riformula:\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    payload = {
        "contents": [{"parts": [{"text": ITA_PLUS_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
    }
    body = _call_gemini(payload)
    result = json.loads(_extract_text(body))
    return [str(s) for s in result] if isinstance(result, list) else [str(result)]
