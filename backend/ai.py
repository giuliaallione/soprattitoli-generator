"""
ai.py – Integrazione Google Gemini.
"""

import os
import json
import urllib.request
import urllib.error

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash-latest:generateContent"
)

# ── Regole comuni ──────────────────────────────────────────────────────────────
REGOLE_BASE = """REGOLE DI FORMATTAZIONE (obbligatorie, rispettale tutte):
1. Ogni riga ha MASSIMO 42 caratteri, spazi compresi.
2. I numeri da zero a dieci si scrivono in lettere (zero, uno, due… dieci). I numeri maggiori di dieci si scrivono in cifre arabe (11, 12, 13…). Qualsiasi numero a inizio frase va scritto in lettere, indipendentemente dal valore.
3. I due punti si usano SOLO per i discorsi diretti e sono seguiti da uno spazio singolo. In tutti gli altri contesti non si usano.
4. Il punto e virgola NON è consentito. Sostituiscilo con una virgola o spezza la frase.
5. I tre puntini di sospensione (…) si usano SOLO per frasi volutamente lasciate incomplete. Non usarli per pause generiche o effetti stilistici.
6. Cambia il presente progressivo in presente semplice: "Sto piangendo" → "Piango", "Sta andando" → "Va", "Stanno parlando" → "Parlano".
7. È preferibile l'ordine soggetto-verbo-complemento. Limita l'uso di particelle e forme verbali complesse.
8. NON saltare né censurare alcuna frase. Non aggiungere informazioni non presenti nel testo originale.
9. La divisione tra le righe deve rispettare la grammatica italiana: non spezzare gruppi nominali (es. "il vecchio / castello" è sbagliato), gruppi verbali o locuzioni preposizionali.
10. Non aggiungere punteggiatura finale alla fine dell'ultima riga se non era presente nell'originale."""

# ── Prompt suddivisione ────────────────────────────────────────────────────────
SPLIT_SMART_PROMPT = f"""Sei un esperto di adattamento di testi per soprattitoli teatrali italiani.
Ricevi un elenco numerato di battute teatrali. Per ciascuna:
- Se la battuta è già entro 42 caratteri, restituiscila invariata come elemento singolo
- Se è più lunga, dividila in più righe rispettando le regole sotto
- Non modificare il contenuto, solo adatta la formattazione

{REGOLE_BASE}

FORMATO RISPOSTA OBBLIGATORIO:
Rispondi ESCLUSIVAMENTE con un oggetto JSON nel seguente formato, senza nessun altro testo:
{{"results": [["riga1"], ["riga1", "riga2"], ["riga unica"], ...]}}
Ogni elemento dell'array "results" corrisponde alla battuta con lo stesso indice numerico del testo in input.
Zero backtick, zero markdown, zero spiegazioni."""

# ── Prompt rielaborazione manuale ──────────────────────────────────────────────
REWORK_PROMPT = f"""Sei un esperto di adattamento di testi per soprattitoli teatrali italiani.
Rielabora le battute elencate applicando le regole qui sotto.
Puoi riformulare il testo per adattarlo alle regole, mantenendo il significato originale.

{REGOLE_BASE}

FORMATO RISPOSTA OBBLIGATORIO:
Rispondi ESCLUSIVAMENTE con un array JSON di stringhe, una per riga risultante.
Esempio: ["Prima riga elaborata", "Seconda riga se necessario"]
Zero backtick, zero markdown, zero spiegazioni."""

# ── Prompt ITA+ ────────────────────────────────────────────────────────────────
ITA_PLUS_PROMPT = f"""Sei un esperto di adattamento di testi per soprattitoli teatrali italiani.
Riformula le frasi elencate per la colonna ITA+ applicando le regole qui sotto.
Puoi riscrivere liberamente mantenendo il significato originale.

{REGOLE_BASE}

FORMATO RISPOSTA OBBLIGATORIO:
Rispondi ESCLUSIVAMENTE con un array JSON di stringhe.
Esempio: ["Prima riga riformulata", "Seconda riga se necessario"]
Zero backtick, zero markdown, zero spiegazioni."""


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
    """Suddivide tutte le battute in una chiamata sola a Gemini."""
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
            if isinstance(val, list):
                result_map[orig_i] = [str(r) for r in val if str(r).strip()]
            else:
                result_map[orig_i] = [str(val)] if str(val).strip() else [orig_s]
        else:
            result_map[orig_i] = [orig_s]

    return [result_map.get(i, [s] if s else []) for i, s in enumerate(sentences)]


def rework_text(sentences: list[str]) -> list[str]:
    """Rielaborazione manuale delle battute selezionate."""
    user_text = "Rielabora queste battute:\n\n" + "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(sentences)
    )
    payload = {
        "contents": [{"parts": [{"text": REWORK_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
    }
    body = _call_gemini(payload)
    result = json.loads(_extract_text(body))
    return [str(s) for s in result] if isinstance(result, list) else [str(result)]


def rework_ita_plus(sentences: list[str]) -> list[str]:
    """Riformulazione per colonna ITA+."""
    user_text = "Riformula queste frasi:\n\n" + "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(sentences)
    )
    payload = {
        "contents": [{"parts": [{"text": ITA_PLUS_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
    }
    body = _call_gemini(payload)
    result = json.loads(_extract_text(body))
    return [str(s) for s in result] if isinstance(result, list) else [str(result)]
