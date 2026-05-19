import { useState } from 'react'

const COLOR_META = {
  w: { name: 'BIANCO',  hex: '#e8e8e8', text: '#000' },
  c: { name: 'CIANO',   hex: '#00e5ff', text: '#000' },
  g: { name: 'VERDE',   hex: '#69f0ae', text: '#000' },
  m: { name: 'MAGENTA', hex: '#ff40ff', text: '#000' },
}

const overlay = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  zIndex: 200, padding: 24,
}

const modal = {
  background: 'var(--bg2)', border: '1px solid var(--border)',
  borderRadius: 16, width: '100%', maxWidth: 480, padding: 28,
}

export default function ColorModal({ proposed, onAccept, onSkip, onManual }) {
  const [mode, setMode] = useState('proposed')  // 'proposed' | 'manual'
  const [manualMap, setManualMap] = useState({})

  // Costruisce gli assignments dalla proposta
  const acceptProposed = () => {
    const assignments = {}
    proposed.forEach(p => { assignments[p.personaggio] = p.color_key })
    onAccept(assignments)
  }

  const acceptManual = () => {
    onManual(manualMap)
  }

  // Tutti i personaggi unici dalla proposta (per il manuale aggiungiamo altri)
  const allChars = proposed.map(p => ({ name: p.personaggio, count: p.count }))

  return (
    <div style={overlay} onClick={e => e.target === e.currentTarget && onSkip()}>
      <div style={modal}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Assegnazione colori</h3>
        <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 20 }}>
          I 4 personaggi con più battute (caratteri, spazi inclusi)
        </p>

        {/* Tab */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {['proposed', 'manual'].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding: '6px 14px', borderRadius: 8, fontSize: 13,
              background: mode === m ? 'var(--accent)' : 'var(--bg3)',
              border: `1px solid ${mode === m ? 'var(--accent)' : 'var(--border)'}`,
              color: mode === m ? '#fff' : 'var(--text)',
            }}>
              {m === 'proposed' ? '✨ Proposta automatica' : '✏️ Manuale'}
            </button>
          ))}
        </div>

        {mode === 'proposed' && (
          <>
            {proposed.length === 0 && (
              <p style={{ color: 'var(--text2)', fontSize: 14 }}>Nessun personaggio trovato.</p>
            )}
            {proposed.map((p, i) => {
              const cm = COLOR_META[p.color_key]
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '10px 14px', borderRadius: 8,
                  background: cm.hex + '22',
                  border: `1px solid ${cm.hex}55`,
                  marginBottom: 8,
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: cm.hex, flexShrink: 0,
                    border: '1px solid rgba(255,255,255,0.2)'
                  }} />
                  <div style={{ flex: 1 }}>
                    <span style={{ fontWeight: 500, fontSize: 14 }}>{p.personaggio}</span>
                    <span style={{ color: 'var(--text2)', fontSize: 12, marginLeft: 8 }}>
                      {p.count.toLocaleString()} car.
                    </span>
                  </div>
                  <span style={{
                    fontSize: 12, fontFamily: 'var(--mono)',
                    color: cm.hex, fontWeight: 500
                  }}>{cm.name}</span>
                </div>
              )
            })}
            <div style={{ display: 'flex', gap: 8, marginTop: 20 }}>
              <button onClick={acceptProposed} style={{
                flex: 1, background: 'var(--green)', color: '#000',
                borderRadius: 8, padding: '10px 0', fontWeight: 600, fontSize: 14,
              }}>✅ Accetta</button>
              <button onClick={onSkip} style={{
                flex: 1, background: 'var(--bg3)',
                border: '1px solid var(--border)', color: 'var(--text)',
                borderRadius: 8, padding: '10px 0', fontSize: 14,
              }}>Salta</button>
            </div>
          </>
        )}

        {mode === 'manual' && (
          <>
            <div style={{ marginBottom: 8, fontSize: 12, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>
              w = BIANCO · c = CIANO · g = VERDE · m = MAGENTA
            </div>
            <div style={{ maxHeight: 280, overflowY: 'auto', marginBottom: 16 }}>
              {allChars.map((ch, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '7px 0', borderBottom: '1px solid var(--border)'
                }}>
                  <span style={{ flex: 1, fontSize: 14 }}>{ch.name}</span>
                  <span style={{ fontSize: 12, color: 'var(--text2)', fontFamily: 'var(--mono)', minWidth: 60, textAlign: 'right' }}>
                    {ch.count?.toLocaleString()} car.
                  </span>
                  <select
                    value={manualMap[ch.name] || ''}
                    onChange={e => setManualMap(m => ({ ...m, [ch.name]: e.target.value }))}
                    style={{
                      background: 'var(--bg3)', border: '1px solid var(--border)',
                      color: 'var(--text)', borderRadius: 6, padding: '4px 8px',
                      fontSize: 13, fontFamily: 'var(--mono)', width: 80
                    }}
                  >
                    <option value="">—</option>
                    {Object.entries(COLOR_META).map(([k, v]) => (
                      <option key={k} value={k}>{v.name}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={acceptManual} style={{
                flex: 1, background: 'var(--green)', color: '#000',
                borderRadius: 8, padding: '10px 0', fontWeight: 600, fontSize: 14,
              }}>Inserisci</button>
              <button onClick={onSkip} style={{
                flex: 1, background: 'var(--bg3)',
                border: '1px solid var(--border)', color: 'var(--text)',
                borderRadius: 8, padding: '10px 0', fontSize: 14,
              }}>Chiudi</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
