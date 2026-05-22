"""
ai.py – Integrazione Google Gemini per:
  1. Rielaborazione testi ITA (rework_text)
  2. Suddivisione battute a 42 caratteri con senso compiuto (split_lines)
  3. Riformulazione ITA+ da Excel (rework_ita_plus)
"""

import os
import json
import urllib.request
import urllib.error

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

# ── Prompt per rielaborazione ITA ──────────────────────────────────────────────
REWORK_PROMPT = """Sei un esperto di adattamento di testi per soprattitoli teatrali.
Rielabora le battute rispettando queste regole:
1. Usa solo il PRESENTE SEMPLICE (no presente continuo).
2. Struttura S-V-O quando possibile.
3. Ogni riga massimo 42 caratteri (spazi inclusi).
4. Se troppo lunga, dividi in più elementi della lista.
5. Mantieni il senso originale.
6. Italiano chiaro e diretto.
7. Nessuna punteggiatura finale.

Rispondi SOLO con un array JSON di stringhe, senza altro testo.
Esempio: ["Prima riga", "Seconda riga se necessario"]"""

# ── Prompt per suddivisione a 42 caratteri ────────────────────────────────────
SPLIT_PROMPT = """Sei un assistente per la suddivisione di testi teatrali in soprattitoli.
Dividi ogni battuta in righe di senso compiuto di MASSIMO 42 caratteri (spazi inclusi).
Regole:
- Non spezzare le parole
- Ogni riga deve avere senso compiuto o almeno formare un'unità logica
- Non modificare il testo, solo dividi
- Nessuna punteggiatura finale aggiunta

Rispondi SOLO con un array JSON di stringhe (una per riga risultante).
Esempio input: "Sono andato al mercato e ho comprato delle mele"
Esempio output: ["Sono andato al mercato", "e ho comprato delle mele"]"""

# ── Prompt per ITA+ ───────────────────────────────────────────────────────────
ITA_PLUS_PROMPT = """Sei un esperto di adattamento di testi per soprattitoli teatrali.
Riformula le frasi seguendo questi criteri precisi:
1. Il presente continuo diventa presente semplice ("va" non "sta andando")
2. Ristabilisci la sequenza SOGGETTO-VERBO-OGGETTO
3. Massimo 37 caratteri per riga (spazi inclusi)
4. Se la frase è più lunga, dividila in più righe
5. Non aggiungere o togliere informazioni
6. Italiano chiaro, nessuna punteggiatura finale

Rispondi SOLO con un array JSON di stringhe.
Esempio: ["Soggetto verbo oggetto", "seconda riga se necessario"]"""


def _call_gemini(prompt: str, user_text: str) -> list[str]:
    """Chiama Gemini e restituisce lista di stringhe."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY non configurata.")

    payload = {
        "contents": [{"parts": [{"text": prompt + "\n\n" + user_text}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
    }

    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Errore Gemini ({e.code}): {e.read().decode()}")

    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
        result = json.loads(text)
        return [str(s) for s in result] if isinstance(result, list) else [str(result)]
    except Exception as e:
        raise RuntimeError(f"Risposta Gemini non valida: {e}")


def rework_text(sentences: list[str]) -> list[str]:
    """Rielabora le battute ITA selezionate (pulsante AI nella tabella)."""
    user_text = "Rielabora queste battute:\n" + "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(sentences)
    )
    return _call_gemini(REWORK_PROMPT, user_text)


def split_lines_ai(sentence: str, max_chars: int = 42) -> list[str]:
    """Suddivide una battuta in righe di senso compiuto con AI."""
    user_text = f"Dividi in righe da max {max_chars} caratteri:\n{sentence}"
    return _call_gemini(SPLIT_PROMPT, user_text)


def rework_ita_plus(sentences: list[str]) -> list[str]:
    """Riformula le frasi per la colonna ITA+ (percorso ITA+)."""
    user_text = "Riformula queste frasi:\n" + "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(sentences)
    )
    return _call_gemini(ITA_PLUS_PROMPT, user_text)
