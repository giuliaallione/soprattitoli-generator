"""
parser.py – Logica di parsing del copione (portata dal codice originale Tkinter).
Nessuna dipendenza da UI: funziona sia standalone che nel contesto web.
"""

import re
from collections import defaultdict
import docx


# ── Costanti colori ────────────────────────────────────────────────────────────

COLOR_META = {
    'w': {'name': 'BIANCO',  'hex': '#FFFFFF'},
    'c': {'name': 'CIANO',   'hex': '#00FFFF'},
    'g': {'name': 'VERDE',   'hex': '#90EE90'},
    'm': {'name': 'MAGENTA', 'hex': '#FF00FF'},
}
COLOR_ORDER = ['w', 'c', 'g', 'm']


# ── Funzioni di parsing ────────────────────────────────────────────────────────

def is_para_italic(para):
    """True se tutti i run non vuoti del paragrafo sono in corsivo."""
    runs = [r for r in para.runs if r.text.strip()]
    return bool(runs) and all(r.italic for r in runs)


def split_sentences(text):
    """Divide il testo in frasi sui . ! ? seguiti da spazio o fine stringa."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_inline_parens(text):
    """Estrae il contenuto tra parentesi inline; restituisce (testo_pulito, note)."""
    notes = re.findall(r'\(([^)]+)\)', text)
    clean = re.sub(r'\s*\([^)]+\)', '', text).strip()
    return clean, '; '.join(notes)


def parse_document(path: str, criteria: dict) -> list[dict]:
    """
    Legge il .docx e restituisce lista di dict:
      {colore, personaggio, ita, note}
    """
    doc = docx.Document(path)
    rows = []
    current_char = None

    name_caps   = criteria.get('name_caps', True)
    name_sep    = criteria.get('name_sep', True)
    sep_char    = criteria.get('sep_char', ' – ')
    desc_italic = criteria.get('desc_italic', True)
    desc_parens = criteria.get('desc_parens', True)

    def add_row(char, ita, note=''):
        rows.append({'colore': '', 'personaggio': char or '', 'ita': ita, 'note': note})

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 1. Paragrafo interamente in corsivo → didascalia
        if desc_italic and is_para_italic(para):
            add_row(current_char, '', text)
            continue

        # 2. Paragrafo interamente tra parentesi → didascalia
        if desc_parens and text.startswith('(') and text.endswith(')'):
            add_row(current_char, '', text[1:-1].strip())
            continue

        character = None
        dialogue  = text

        # 3. Nome personaggio + separatore nella stessa riga
        if name_sep and sep_char in text:
            idx = text.index(sep_char)
            candidate = text[:idx].strip()
            rest = text[idx + len(sep_char):].strip()
            if candidate:
                character = candidate
                dialogue  = rest

        # 4. Riga standalone: nome in MAIUSCOLO con eventuale didascalia tra parentesi
        if character is None and name_caps:
            text_no_paren, inline_note = extract_inline_parens(text)
            text_no_paren = text_no_paren.strip()
            words = text_no_paren.split()
            is_caps = (bool(words)
                       and all(w == w.upper() for w in words)
                       and any(c.isalpha() for c in text_no_paren)
                       and len(words) <= 5)
            if is_caps:
                current_char = text_no_paren
                if inline_note:
                    add_row(current_char, '', inline_note)
                continue

        if character:
            current_char = character

        # 5. Dividi il dialogo in frasi
        sentences = split_sentences(dialogue)
        for sentence in sentences:
            if desc_parens:
                clean_s, inline_note = extract_inline_parens(sentence)
            else:
                clean_s, inline_note = sentence, ''
            if clean_s:
                add_row(current_char, clean_s, inline_note)

    return rows


def count_chars(rows: list[dict]) -> dict:
    """Conta i caratteri per personaggio (battute ITA, spazi inclusi)."""
    counts = defaultdict(int)
    for row in rows:
        if row.get('ita') and row.get('personaggio'):
            counts[row['personaggio']] += len(row['ita'])
    return dict(counts)


def propose_colors(rows: list[dict]) -> list[dict]:
    """
    Ritorna la proposta colori automatica:
    lista di {personaggio, count, color_key, color_name, color_hex}
    per i top-4 personaggi per numero di caratteri.
    """
    counts = count_chars(rows)
    if not counts:
        return []
    top4 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:4]
    result = []
    for i, (char, count) in enumerate(top4):
        key = COLOR_ORDER[i]
        result.append({
            'personaggio': char,
            'count': count,
            'color_key': key,
            'color_name': COLOR_META[key]['name'],
            'color_hex': COLOR_META[key]['hex'],
        })
    return result


def apply_colors(rows: list[dict], assignments: dict) -> list[dict]:
    """
    Applica i colori alle righe.
    assignments = {'NOME_PERSONAGGIO': 'w', 'ALTRO': 'c', ...}
    """
    for row in rows:
        char = row.get('personaggio', '')
        if char in assignments:
            row['colore'] = assignments[char]
    return rows
