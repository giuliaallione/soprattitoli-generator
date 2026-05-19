# Soprattitoli Generator – Guida al deploy

## Struttura del progetto

```
soprattitoli/
├── backend/
│   ├── main.py          ← Server web (FastAPI)
│   ├── parser.py        ← Logica di parsing del copione
│   ├── ai.py            ← Integrazione Gemini AI
│   └── requirements.txt ← Dipendenze Python
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/  ← Interfaccia utente
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── render.yaml          ← Configurazione deploy automatico
```

---

## Prerequisiti (da installare una volta sola)

- **Git**: https://git-scm.com/downloads
- **Node.js**: https://nodejs.org (versione 18 o superiore)
- **Python**: https://python.org (versione 3.11 o superiore)
- Un account **GitHub**: https://github.com (gratuito)
- Un account **Render**: https://render.com (gratuito)
- Un account **Google AI Studio**: https://aistudio.google.com (gratuito)

---

## Passo 1 – Ottieni la chiave API Gemini

1. Vai su https://aistudio.google.com
2. Clicca **"Get API key"** in alto a sinistra
3. Clicca **"Create API key"**
4. Copia la chiave che appare (inizia con "AIza...") e salvala in un posto sicuro
   ⚠️ Non condividere mai questa chiave con nessuno

---

## Passo 2 – Crea il repository su GitHub

1. Vai su https://github.com e accedi
2. Clicca il **+** in alto a destra → **New repository**
3. Nome: `soprattitoli-generator`
4. Lascia tutto il resto come sta, clicca **Create repository**
5. Segui le istruzioni che compaiono per caricare i file
   (sezione "…or upload an existing file" → trascina tutta la cartella `soprattitoli/`)

---

## Passo 3 – Deploy su Render

1. Vai su https://render.com e accedi (puoi usare il tuo account GitHub)
2. Clicca **New +** → **Blueprint**
3. Collega il tuo repository GitHub `soprattitoli-generator`
4. Render leggerà il file `render.yaml` e creerà automaticamente i due servizi:
   - `soprattitoli-backend` (il server Python)
   - `soprattitoli-frontend` (l'interfaccia web)
5. **Prima di confermare**, imposta la variabile d'ambiente:
   - Clicca su `soprattitoli-backend`
   - Trova **Environment Variables**
   - Aggiungi: chiave = `GEMINI_API_KEY`, valore = la chiave che hai copiato al Passo 1
6. Clicca **Apply** e aspetta 3-5 minuti

---

## Passo 4 – Collega il frontend al backend

Dopo il primo deploy, Render assegna un URL al backend (es. `https://soprattitoli-backend.onrender.com`).

1. Vai nel servizio `soprattitoli-frontend` su Render
2. **Environment Variables** → modifica `VITE_API_URL` con l'URL esatto del tuo backend
3. Clicca **Save Changes** → Render fa un nuovo build automaticamente

---

## Passo 5 – Accedi all'app

Dopo il build, il frontend ha il suo URL (es. `https://soprattitoli-frontend.onrender.com`).
Condividi questo link con il tuo team — non serve installare nulla.

---

## Note importanti

**Piano gratuito Render**: I servizi vanno in "sleep" dopo 15 minuti di inattività.
Il primo accesso dopo una pausa può richiedere 30-60 secondi.
Se volete evitarlo, passate al piano "Starter" (7$/mese per servizio).

**Costi Gemini**: Con il piano gratuito (1.500 richieste/giorno) non paghi nulla.
Se superate questo limite, Google vi avvisa via email prima di addebitare qualcosa.

**Sicurezza**: La chiave Gemini è sul server e non è mai visibile agli utenti.

---

## Aggiornare l'app in futuro

Ogni volta che modifichi i file e li carichi su GitHub, Render fa il deploy automaticamente.
Non devi fare nulla di extra.
