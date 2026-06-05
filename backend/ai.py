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

# Prompt specifico per la colonna ITA (strutturato per Excel e Chunking)
REWORK_PROMPT = f"""Sei un esperto di soprattitoli teatrali italiani.
Ricevi un elenco numerato di battute. Devi formattarle applicando QUESTE REGOLE:

{REGOLE_ITA}

Rispondi ESCLUSIVAMENTE con un oggetto JSON dove le chiavi sono gli indici originali e i valori sono le battute formattate.
Se devi dividere in due righe, usa il carattere speciale '\\n' per andare a capo all'interno della stessa stringa.

Esempio di output:
{{
  "0": "Prima riga del sottotitolo\\nSeconda riga del sottotitolo",
  "1": "Sottotitolo corto su una riga sola",
  "2": "Altra battuta lunga\\nche va a capo qui"
}}"""

# Prompt per lo split base (se lo usi ancora per altri percorsi)
SPLIT_SMART_PROMPT = f"""Sei un esperto di soprattitoli teat
