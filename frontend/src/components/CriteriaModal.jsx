import { useState } from 'react'

const card = {
  background: 'var(--bg2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: '16px 20px',
  marginBottom: 12,
}

export default function CriteriaModal({ filename, onConfirm, onBack, loading }) {
  const [nameCaps, setNameCaps] = useState(true)
  const [nameSep, setNameSep] = useState(true)
  const [sepChar, setSepChar] = useState(' – ')
  const [descItalic, setDescItalic] = useState(true)
  const [descParens, setDescParens] = useState(true)

  const submit = () => {
    onConfirm({
      name_caps: nameCaps,
      name_sep: nameSep,
      sep_char: sepChar,
      desc_italic: descItalic,
      desc_parens: descParens,
    })
  }

  return (
    <div style={{ maxWidth: 480, margin: '0 auto' }}>
      <button onClick={onBack} style={{
        background: 'none', color: 'var(--text2)', fontSize: 13, marginBottom: 24
      }}>← Torna indietro</button>

      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>Criteri di analisi</h2>
      <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 24, fontFamily: 'var(--mono)' }}>
        {filename}
      </p>

      {/* Nomi personaggi */}
      <div style={card}>
        <p style={{ fontWeight: 500, marginBottom: 12 }}>Nomi dei personaggi</p>

        <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, cursor: 'pointer' }}>
          <input type="checkbox" checked={nameCaps} onChange={e => setNameCaps(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: 'var(--accent)' }} />
          <span style={{ fontSize: 14 }}>Tutto in MAIUSCOLO</span>
        </label>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <input type="checkbox" checked={nameSep} onChange={e => setNameSep(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: 'var(--accent)', flexShrink: 0 }} />
          <span style={{ fontSize: 14 }}>Seguito da separatore:</span>
          <select
            value={sepChar}
            onChange={e => setSepChar(e.target.value)}
            style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              color: 'var(--text)', borderRadius: 6, padding: '4px 8px',
              fontSize: 14, fontFamily: 'var(--mono)',
            }}
          >
            {[' – ', ' - ', ': ', ':', ' — '].map(s => (
              <option key={s} value={s}>{s.trim() || '(vuoto)'}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Didascalie */}
      <div style={card}>
        <p style={{ fontWeight: 500, marginBottom: 12 }}>Didascalie / parti descrittive</p>

        <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, cursor: 'pointer' }}>
          <input type="checkbox" checked={descItalic} onChange={e => setDescItalic(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: 'var(--accent)' }} />
          <span style={{ fontSize: 14 }}>Paragrafi interamente in corsivo</span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
          <input type="checkbox" checked={descParens} onChange={e => setDescParens(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: 'var(--accent)' }} />
          <span style={{ fontSize: 14 }}>Testo tra parentesi tonde ( )</span>
        </label>
      </div>

      <button
        onClick={submit}
        disabled={loading}
        style={{
          width: '100%',
          background: 'var(--accent)',
          color: '#fff',
          borderRadius: 10,
          padding: '13px 0',
          fontSize: 15,
          fontWeight: 600,
          marginTop: 8,
        }}
      >
        {loading ? 'Elaborazione in corso…' : '▶ Avvia elaborazione'}
      </button>
    </div>
  )
}
