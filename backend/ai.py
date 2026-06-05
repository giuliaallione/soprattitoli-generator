"""
ai.py – Integrazione Google Gemini 2.5 Flash.
Retry automatico con exponential backoff per errori 503/429.
"""

import os
import json
import time
import urllib.request
import urllib.error

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

# Nuove regole rigorose per il percorso ITA
REGOLE_ITA = """REGOLE DI FORMATTAZIONE (obbligatorie):
1. Massimo due righe per sottotitolo.
2. Massimo 40 caratteri, spazi compresi, per riga.
3. Ogni sottotitolo deve contenere un'unità linguistica di senso compiuto, senza penalizzare nessi logici e fluidità.
4. La divisione tra le righe deve avvenire tra principale e subordinata o in corrispondenza di una congiunzione.
5. DIVIETI DI DIVISIONE: La divisione tra le righe NON deve MAI avvenire tra articolo e sostantivo, preposizione e sostantivo, aggettivo e sostantivo, soggetto e verbo, ausiliare e verbo, qualifica e nome proprio.
6. I numeri da zero a dieci vanno scritti in lettere. I numeri maggiori di dieci in numeri arabi. Qualsiasi numero a inizio frase va scritto in lettere.
7. Il simbolo "-" si utilizza a inizio delle due righe per distinguere due parlanti nello stesso sottotitolo, seguito da uno spazio singolo; ogni riga può contenere un parlante solo.
8. I due punti si utilizzano unicamente per i discorsi diretti e sono seguiti da uno spazio singolo.
9. Le virgolette (ad esempio per i discorsi diretti) sono sempre basse (« »).
10. Il trattino alto si usa per aprire un virgolettato dentro a frasi già tra virgolette.
11. L'uso del punto e virgola NON è consentito.
12. NON saltare né censurare frasi."""

# Prompt specifico per la colonna ITA (strutturato per Excel)
REWORK_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Ricevi un testo narrativo o teatrale. Devi strutturare i dati per un file Excel a due colonne.

{REGOLE_ITA}

Estrai il personaggio e il testo e rispondi ESCLUSIVAMENTE con un array JSON di oggetti.
Ogni oggetto deve avere due chiavi:
- "personaggio": il nome del personaggio in MAIUSCOLO.
- "testo": la battuta che rispetta rigorosamente le regole di 40 caratteri. Se divisa in due righe, usa il carattere speciale '\\n' per andare a capo.

Esempio di output JSON atteso:
[
  {{
    "personaggio": "NOME PERSONAGGIO",
    "testo": "Prima riga del sottotitolo\\nSeconda riga del sottotitolo"
  }}
]"""

# Prompt per lo split base (se lo usi ancora per altri percorsi)
SPLIT_SMART_PROMPT = f"""Sei un esperto di soprattitoli teatrali.
Dividi o formatta le seguenti battute rispettando queste regole.

{REGOLE_ITA}

Rispondi con un array JSON di stringhe, ad esempio: ["riga unica", "riga 1\\nriga 2"]"""


def _gen_config(max_tokens: int = 4096, temp: float = 0.2) -> dict:
    return {
        "temperature": temp,
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
    }


def _call_gemini(payload: dict, max_retries: int = 5) -> dict:
    """Chiama Gemini con retry automatico ed exponential backoff."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY non configurata.")

    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")

    last_error = None
    for attempt in range(max_retries):
        if attempt > 0:
            wait = 2 ** attempt  # 2, 4, 8, 16 secondi
            time.sleep(wait)

        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            last_error = f"Errore Gemini ({e.code}): {error_body}"
            # Retry solo su 503 (server sovraccarico) e 429 (quota)
            if e.code in (503, 429):
                continue
            # Su altri errori (404, 400...) fallisci subito
            raise RuntimeError(last_error)

    raise RuntimeError(f"Gemini non disponibile dopo {max_retries} tentativi. {last_error}")


def _extract_text(body: dict) -> str:
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        raise RuntimeError(f"Risposta Gemini non valida: {e}\n{body}")


def rework_text(sentences: list[str]) -> list[dict]:
    """
    Elabora le frasi per il percorso ITA e restituisce una lista di dizionari 
    con le chiavi 'personaggio' e 'testo', pronti per l'export in Excel.
    """
    user_text = "Elabora questo testo:\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    payload = {
        "contents": [{"parts": [{"text": REWORK_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": _gen_config(temp=0.1),
    }
    
    body = _call_gemini(payload)
    raw_text = _extract_text(body)
    
    try:
        # strict=False gestisce in sicurezza gli "a capo" nascosti che facevano esplodere il parser
        result = json.loads(raw_text, strict=False)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Errore di parsing del JSON di Gemini: {e}\nTesto grezzo:\n{raw_text}")


def split_sentences_smart(sentences: list[str]) -> list[str]:
    # (Mantenuto compatibile qualora venisse usato in altre rotte)
    user_text = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences) if s and s.strip())
    payload = {
        "contents": [{"parts": [{"text": SPLIT_SMART_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": _gen_config(max_tokens=8192, temp=0.1),
    }
    body = _call_gemini(payload)
    raw = _extract_text(body)

    try:
        parsed = json.loads(raw, strict=False)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except Exception as e:
        raise RuntimeError(f"Risposta split non valida: {e}\n{raw}")

# ── AGGIUNGI IN FONDO AL FILE ai.py ──

ITA_PLUS_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Riformula le frasi per la colonna ITA+ applicando queste regole.
Puoi riscrivere liberamente mantenendo il significato.

{REGOLE_ITA}
- Massimo 37 caratteri per riga in questo percorso.

Rispondi con un array JSON di stringhe.
Esempio: ["Prima riga riformulata", "Seconda riga se necessario"]"""

def rework_ita_plus(sentences: list[str]) -> list[str]:
    user_text = "Riformula:\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    payload = {
        "contents": [{"parts": [{"text": ITA_PLUS_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": _gen_config(),
    }
    body = _call_gemini(payload)
    raw_text = _extract_text(body)
    try:
        # Il strict=False ti salva dagli "a capo" indesiderati
        result = json.loads(raw_text, strict=False)
        return [str(s) for s in result] if isinstance(result, list) else [str(result)]
    except Exception as e:
        raise RuntimeError(f"Errore di parsing del JSON in ITA+: {e}\nTesto grezzo:\n{raw_text}")
