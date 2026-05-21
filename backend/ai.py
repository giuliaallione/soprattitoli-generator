"""
ai.py – Integrazione con Google Gemini per la rielaborazione dei testi ITA.
La chiave API viene letta dalla variabile d'ambiente GEMINI_API_KEY.
"""

import os
import json
import urllib.request
import urllib.error

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash-latest"
)

SYSTEM_PROMPT = """Sei un esperto di adattamento di testi per soprattitoli teatrali.
Il tuo compito è rielaborare le battute rispettando queste regole precise:

1. Usa solo il PRESENTE SEMPLICE (no presente continuo: "va" non "sta andando").
2. Struttura la frase come SOGGETTO – VERBO – OGGETTO (S-V-O) quando possibile.
3. Ogni riga deve avere MASSIMO 37 caratteri (spazi inclusi).
4. Se la frase è troppo lunga, dividila in due righe separate (due elementi della lista).
5. Mantieni il senso originale senza aggiungere o togliere informazioni.
6. Usa un italiano chiaro e diretto, senza letterarietà eccessiva.
7. Non usare punteggiatura finale (no punto, no virgola alla fine).

Rispondi SOLO con un array JSON di stringhe, senza nessun altro testo.
Esempio di risposta corretta: ["Prima riga rielaborata", "Seconda riga se necessario"]
"""


def rework_text(sentences: list[str]) -> list[str]:
    """
    Invia le battute a Gemini e ritorna le versioni rielaborate.
    sentences: lista di stringhe (battute originali dalla colonna ITA)
    Ritorna: lista di stringhe rielaborate
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY non configurata nel server.")

    # Prepara il testo da mandare
    user_text = "Rielabora queste battute:\n" + "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(sentences)
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + user_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }

    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Errore Gemini API ({e.code}): {error_body}")

    # Estrai il testo dalla risposta
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Rimuovi eventuali backtick di codice se Gemini li aggiunge
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
        result = json.loads(text)
        if isinstance(result, list):
            return [str(s) for s in result]
        return [str(result)]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Risposta Gemini non valida: {e}\nRisposta raw: {body}")
