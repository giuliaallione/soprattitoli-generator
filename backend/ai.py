"""
ai.py – Integrazione Google Gemini 2.5 Flash.
Retry automatico con exponential backoff per errori 503/429.
Elaborazione a Chunk (scaglioni) per evitare limiti di token.
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

# Regole rigorose di base
REGOLE_ITA = """REGOLE DI FORMATTAZIONE (obbligatorie):
1. Massimo due righe per sottotitolo.
2. Massimo 42 caratteri (spazi compresi) per riga. Questo limite è TASSATIVO e non ammette eccezioni.
3. Ogni sottotitolo deve contenere un'unità linguistica di senso compiuto, senza penalizzare nessi logici e fluidità.
4. La divisione tra le righe deve avvenire tra principale e subordinata o in corrispondenza di una congiunzione.
5. DIVIETI DI DIVISIONE ASSOLUTI: La divisione tra le righe NON deve MAI avvenire tra articolo e sostantivo, preposizione e sostantivo, aggettivo e sostantivo, soggetto e verbo, ausiliare e verbo, qualifica e nome proprio.
6. I numeri da zero a dieci vanno scritti in lettere. I numeri maggiori di dieci in numeri arabi. Qualsiasi numero a inizio frase va scritto in lettere.
7. Il simbolo "-" si utilizza a inizio delle due righe per distinguere due parlanti nello stesso sottotitolo, seguito da uno spazio singolo; ogni riga può contenere un parlante solo.
8. I due punti si utilizzano unicamente per i discorsi diretti e sono seguiti da uno spazio singolo.
9. Le virgolette (ad esempio per i discorsi diretti) sono sempre basse (« »).
10. Il trattino alto si usa per aprire un virgolettato dentro a frasi già tra virgolette.
11. L'uso del punto e virgola NON è consentito.
12. NON saltare né censurare frasi."""

# Prompt specifico per la colonna ITA
REWORK_PROMPT = f"""Sei un linguista esperto di soprattitoli teatrali italiani.
Ricevi un elenco numerato di battute. Devi formattarle applicando QUESTE REGOLE, rispettando rigorosamente questo ordine di importanza:

PRIORITÀ ASSOLUTA 1 (Limiti di Riga e Grammatica):
- LIMITE TASSATIVO: NON superare MAI i 42 caratteri per riga (spazi inclusi). Non ci sono eccezioni.
- DIVIETI DI DIVISIONE: Rispetta scrupolosamente i divieti (es. "un / angelo" o "è / annegato" sono errori inaccettabili). La divisione a capo deve rispettare i nessi logici naturali.
- Se rispettare un nesso logico ti porta a superare i 42 caratteri, devi ANTICIPARE il taglio a un punto logico precedente pur di restare entro il limite senza fare errori.

PRIORITÀ ASSOLUTA 2 (Limite di 2 Righe e Overflow):
- MASSIMO DUE RIGHE per sottotitolo. Questo limite è invalicabile. NON CREARE MAI UNA TERZA RIGA.
- Se la battuta originale è molto lunga, compila la prima e la seconda riga in modo logico (massimo 42 caratteri l'una).
- Tutto il testo in eccedenza (quello che costituirebbe una terza riga) DEVE scivolare in un NUOVO sottotitolo separato.
- Usa ESCLUSIVAMENTE la stringa " || " (doppia barra verticale) per segnalare la divisione tra il primo sottotitolo e quello successivo generato dall'eccedenza.
- Usa il carattere '\\n' per andare a capo all'interno dello stesso sottotitolo.
- Esempio corretto: "Prima riga riempita in modo logico\\nSeconda riga riempita in modo logico || Testo in eccedenza che forma il nuovo\\nsottotitolo successivo"

Rispondi ESCLUSIVAMENTE con un oggetto JSON dove le chiavi sono gli indici originali forniti nel testo e i valori sono le battute formattate.
MANTENI GLI INDICI ESATTI CHE TI VENGONO FORNITI.
"""

# Prompt per il percorso ITA+
ITA_PLUS_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Riformula le frasi per la colonna ITA+ applicando queste regole.
Puoi riscrivere liberamente mantenendo il significato.

{REGOLE_ITA}
- ATTENZIONE: In questo percorso il limite massimo è di 37 caratteri per riga, spazi inclusi. TASSATIVO e senza eccezioni.

Rispondi con un array JSON di stringhe.
Esempio: ["Prima riga riformulata", "Seconda riga se necessario"]"""


def _gen_config(max_tokens: int = 8192, temp: float = 0.1) -> dict:
    return {
        "temperature": temp,
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
    }


def _call_gemini(payload: dict, max_retries: int = 5) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY non configurata.")

    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")

    last_error = None
    for attempt in range(max_retries):
        if attempt > 0:
            wait = 2 ** attempt
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
            if e.code in (503, 429):
                continue
            raise RuntimeError(last_error)

    raise RuntimeError(f"Gemini non disponibile dopo {max_retries} tentativi. {last_error}")


def _extract_text(body: dict) -> str:
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        raise RuntimeError(f"Risposta Gemini non valida: {e}\n{body}")


def rework_text(indexed_sentences: list[tuple[int, str]]) -> dict[int, str]:
    if not indexed_sentences:
        return {}

    chunk_size = 60
    result_map = {}

    for i in range(0, len(indexed_sentences), chunk_size):
        chunk = indexed_sentences[i:i+chunk_size]
        user_text = "\n".join(f"{idx}. {s}" for idx, s in chunk)
        payload = {
            "contents": [{"parts": [{"text": REWORK_PROMPT + "\n\n" + user_text}]}],
            "generationConfig": _gen_config(),
        }
        
        try:
            body = _call_gemini(payload)
            raw_text = _extract_text(body)
            parsed = json.loads(raw_text, strict=False)
            for k, v in parsed.items():
                result_map[int(k)] = str(v)
        except Exception as e:
            print(f"Errore chunk da indice {chunk[0][0]}: {e}")
            for idx, s in chunk:
                result_map[idx] = s

    return result_map


def rework_ita_plus(sentences: list[str]) -> list[str]:
    user_text = "Riformula:\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
    payload = {
        "contents": [{"parts": [{"text": ITA_PLUS_PROMPT + "\n\n" + user_text}]}],
        "generationConfig": _gen_config(),
    }
    body = _call_gemini(payload)
    raw_text = _extract_text(body)
    try:
        result = json.loads(raw_text, strict=False)
        return [str(s) for s in result] if isinstance(result, list) else [str(result)]
    except Exception as e:
        raise RuntimeError(f"Errore di parsing del JSON in ITA+: {e}\nTesto grezzo:\n{raw_text}")
