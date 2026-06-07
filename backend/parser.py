"""
parser.py – Logica di parsing del copione.
Supporta nomi in MAIUSCOLO, GRASSETTO, o criterio custom.
Divide le battute in base alla punteggiatura forte (punti, esclamativi) e le passa a Gemini.
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

# ── Utilità ────────────────────────────────────────────────────────────────────

def is_para_italic(para):
    runs = [r for r in para.runs if r.text.strip()]
    return bool(runs) and all(r.italic for r in runs)

def split_sentences(text):
    """Divide il testo in frasi logiche usando i punti, esclamativi e interrogativi."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def extract_inline_parens(text):
    notes = re.findall(r'\(([^)]+)\)', text)
    clean = re.sub(r'\s*\([^)]+\)', '', text).strip()
    return clean, '; '.join(notes)

def is_caps(text):
    words = text.split()
    return (bool(words)
            and all(w == w.upper() for w in words)
            and any(c.isalpha() for c in text)
            and len(words) <= 6)

def get_bold_prefix(para):
    """Estrae nome in grassetto + resto testo normale dalla stessa riga."""
    bold_text = []
    normal_text = []
    in_bold = True
    for run in para.runs:
        if not run.text:
            continue
        if in_bold and run.bold:
            bold_text.append(run.text)
        else:
            in_bold = False
            normal_text.append(run.text)
    name = ''.join(bold_text).strip()
    rest = ''.join(normal_text).strip()
    if name and rest:
        return name, rest
    return None, None

# ── Parser principale ──────────────────────────────────────────────────────────

def parse_document(path: str, criteria: dict) -> list[dict]:
    doc = docx.Document(path)
    rows = []
    current_char = None

    name_caps   = criteria.get('name_caps', True)
    name_bold   = criteria.get('name_bold', False)
    name_custom = criteria.get('name_custom', '')
    name_sep    = criteria.get('name_sep', True)
    sep_char    = criteria.get('sep_char', ' – ')
    desc_italic = criteria.get('desc_italic', True)
    desc_parens = criteria.get('desc_parens', True)

    def add_rows(char, ita, note=''):
        """Aggiunge la riga INTERA senza tagliarla meccanicamente a 42 caratteri."""
        rows.append({'colore': '', 'personaggio': char or '', 'ita': ita, 'note': note})

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # 1. Corsivo → didascalia
        if desc_italic and is_para_italic(para):
            add_rows(current_char, '', text)
            continue

        # 2. Parentesi intere → didascalia
        if desc_parens and text.startswith('(') and text.endswith(')'):
            add_rows(current_char, '', text[1:-1].strip())
            continue

        character = None
        dialogue  = text

        # 3. Nome in GRASSETTO + battuta nella stessa riga
        if name_bold:
            bold_name, bold_rest = get_bold_prefix(para)
            if bold_name:
                name_clean, name_note = extract_inline_parens(bold_name)
                name_clean = name_clean.strip()
                if name_clean:
                    character = name_clean
                    dialogue  = bold_rest if bold_rest else ''
                    if name_note and not dialogue:
                        add_rows(character, '', name_note)
                        current_char = character
                        continue

        # 4. Nome + separatore
        if character is None and name_sep and sep_char and sep_char in text:
            idx = text.index(sep_char)
            candidate = text[:idx].strip()
            rest = text[idx + len(sep_char):].strip()
            if candidate:
                character = candidate
                dialogue  = rest

        # 5. Maiuscolo standalone
        if character is None and name_caps:
            text_no_paren, inline_note = extract_inline_parens(text)
            text_no_paren = text_no_paren.strip()
            if is_caps(text_no_paren):
                current_char = text_no_paren
                if inline_note:
                    add_rows(current_char, '', inline_note)
                continue

        # 5b. Criterio personalizzato
        if character is None and name_custom and text.startswith(name_custom):
            rest = text[len(name_custom):].strip()
            if rest:
                character = name_custom.strip()
                dialogue = rest
            else:
                current_char = name_custom.strip()
                continue

        if character:
            current_char = character

        if not dialogue:
            continue

        # Ripristinata la divisione per frasi logiche! (Punti, esclamativi, ecc.)
        sentences = split_sentences(dialogue)
        for sentence in sentences:
            if desc_parens:
                clean_s, inline_note = extract_inline_parens(sentence)
            else:
                clean_s, inline_note = sentence, ''
                
            if clean_s:
                add_rows(current_char, clean_s, inline_note)

    return rows

def count_chars(rows: list[dict]) -> dict:
    counts = defaultdict(int)
    for row in rows:
        if row.get('ita') and row.get('personaggio'):
            counts[row['personaggio']] += len(row['ita'])
    return dict(counts)

def propose_colors(rows: list[dict]) -> list[dict]:
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
            'color_hex':  COLOR_META[key]['hex'],
        })
    return result

def apply_colors(rows: list[dict], assignments: dict) -> list[dict]:
    for row in rows:
        char = row.get('personaggio', '')
        if char in assignments:
            row['colore'] = assignments[char]
    return rows
