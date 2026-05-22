import { useState } from 'react'

const card = {
  background: 'var(--bg2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: '16px 20px',
  marginBottom: 12,
}

const NAME_STYLE_OPTIONS = [
  { value: 'caps',   label: 'TUTTO MAIUSCOLO' },
  { value: 'bold',   label: 'Grassetto' },
  { value: 'custom', label: 'Personalizzato…' },
]

const SEP_OPTIONS = [
  { value: ' – ',  label: ' – ' },
  { value: ' - ',  label: ' - ' },
  { value: ': ',   label: ':  ' },
  { value: ':',    label: ':'   },
  { value: ' — ',  label: ' — ' },
  { value: ' ',    label: 'Spazio' },
  { value: 'custom', label: 'Personalizzato…' },
]

function SelectWithCustom({ options, value, onChange, disabled, mono = false }) {
  const isCustom = !options.some(o => o.value === value && o.value !== 'custom')
    || value === 'custom'
  const [showInput, setShowInput] = useState(isCustom && value !== 'custom' && value !== '')

  const handleSelect = (e) => {
    const v = e.target.value
    if (v === 'custom') {
      setShowInput(true)
      onChange('')
    } else {
      setShowInput(false)
      onChange(v)
    }
  }

  const selectValue = showInput ? 'custom' : (options.find(o => o.value === value) ? value : 'custom')

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <select
        value={selectValue}
        onChange={handleSelect}
        disabled={disabled}
        style={{
          background: 'var(--bg3)', border: '1px solid var(--border)',
          color: 'var(--text)', borderRadius: 6, padding: '5px 10px',
          fontSize: 13, fontFamily: mono ? 'var(--mono)' : 'var(--font)',
          opacity: disabled ? 0.4 : 1, minWidth: 160,
        }}
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {showInput && (
        <input
          autoFocus
          placeholder="Scrivi il criterio…"
          value={value === 'custom' ? '' : value}
          onChange={e => onChange(e.target.value)}
          disabled={disabled}
          style={{
            background: 'var(--bg3)', border: '1px solid var(--accent)',
            color: 'var(--text)', borderRadius: 6, padding: '5px 10px',
            fontSize: 13, fontFamily: mono ? 'var(--mono)' : 'var(--font)',
            width: 160,
          }}
        />
      )}
    </div>
  )
}

export default function CriteriaModal({ filename, onConfirm, onBack, loading }) {
  // Stile nome: 'caps' | 'bold' | stringa custom
  const [nameStyle, setNameStyle] = useState('caps')
  // Separatore: stringa | '' (disabilitato)
  const [useSep, setUseSep]       = useState(true)
  const [sepChar, setSepChar]     = useState(' – ')
  // Didascalie
  const [descItalic, setDescItalic] = useState(true)
  const [descParens, setDescParens] = useState(true)

  const submit = () => {
    onConfirm({
      name_caps:   nameStyle === 'caps',
      name_bold:   nameStyle === 'bold',
      name_custom: !['caps', 'bold'].includes(nameStyle) ? nameStyle : '',
      name_sep:    useSep,
      sep_char:    sepChar,
      desc_italic: descItalic,
      desc_parens: descParens,
    })
  }

  const canSubmit = nameStyle && nameStyle !== 'custom' && (!useSep || sepChar)

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <button onClick={onBack} style={{
        background: 'none', color: 'var(--text2)', fontSize: 13, marginBottom: 24
      }}>← Torna indietro</button>

      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>Criteri di analisi</h2>
      <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 24, fontFamily: 'var(--mono)' }}>
        {filename}
      </p>

      {/* Nomi personaggi */}
      <div style={card}>
        <p style={{ fontWeight: 500, marginBottom: 4 }}>Stile dei nomi dei personaggi</p>
        <p style={{ color: 'var(--text2)', fontSize: 12, marginBottom: 12 }}>
          Come sono formattati i nomi nel copione?
        </p>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 6 }}>Formato</div>
          <SelectWithCustom
            options={NAME_STYLE_OPTIONS}
            value={nameStyle}
            onChange={setNameStyle}
          />
          {nameStyle && !['caps', 'bold'].includes(nameStyle) && nameStyle !== 'custom' && (
            <p style={{ fontSize: 11, color: 'var(--text2)', marginTop: 6 }}>
              Il testo inserito verrà cercato all'inizio di ogni riga per identificare il nome
            </p>
          )}
        </div>

        <div style={{ height: 1, background: 'var(--border)', margin: '14px 0' }} />

        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, cursor: 'pointer' }}>
            <input type="checkbox" checked={useSep} onChange={e => setUseSep(e.target.checked)}
              style={{ width: 15, height: 15, accentColor: 'var(--accent)' }} />
            <span style={{ fontSize: 13, fontWeight: 500 }}>Seguito da separatore</span>
          </label>
          <div style={{ marginLeft: 26 }}>
            <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 6 }}>
              Carattere che separa il nome dalla battuta
            </div>
            <SelectWithCustom
              options={SEP_OPTIONS}
              value={sepChar}
              onChange={setSepChar}
              disabled={!useSep}
              mono
            />
          </div>
        </div>
      </div>

      {/* Didascalie */}
      <div style={card}>
        <p style={{ fontWeight: 500, marginBottom: 12 }}>Didascalie / parti descrittive</p>

        <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, cursor: 'pointer' }}>
          <input type="checkbox" checked={descItalic} onChange={e => setDescItalic(e.target.checked)}
            style={{ width: 15, height: 15, accentColor: 'var(--accent)' }} />
          <span style={{ fontSize: 14 }}>Paragrafi interamente in <em>corsivo</em></span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
          <input type="checkbox" checked={descParens} onChange={e => setDescParens(e.target.checked)}
            style={{ width: 15, height: 15, accentColor: 'var(--accent)' }} />
          <span style={{ fontSize: 14 }}>Testo tra parentesi tonde <span style={{ fontFamily: 'var(--mono)' }}>( )</span></span>
        </label>
      </div>

      {!canSubmit && (
        <div style={{
          padding: '10px 14px', borderRadius: 8,
          background: '#2d1a0a', border: '1px solid #7a4010',
          color: '#ffaa60', fontSize: 13, marginBottom: 12
        }}>
          ⚠ Completa i criteri per identificare i nomi dei personaggi
        </div>
      )}

      <button
        onClick={submit}
        disabled={loading || !canSubmit}
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
