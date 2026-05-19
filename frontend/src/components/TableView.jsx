import { useState, useCallback } from 'react'

const COLOR_HEX = { w: '#e8e8e8', c: '#00e5ff', g: '#69f0ae', m: '#ff40ff' }
const COLOR_BG  = { w: '#e8e8e822', c: '#00e5ff22', g: '#69f0ae22', m: '#ff40ff22' }

export default function TableView({ rows, onUpdateRow, onRework }) {
  const [editing, setEditing]     = useState(null)   // { index, field }
  const [editVal, setEditVal]     = useState('')
  const [selected, setSelected]   = useState(new Set())
  const [reworking, setReworking] = useState(false)
  const [reworkResult, setReworkResult] = useState(null)  // { indices, texts }
  const [filter, setFilter]       = useState('')

  const filteredRows = filter
    ? rows.map((r, i) => ({ ...r, _i: i })).filter(r =>
        r.personaggio.toLowerCase().includes(filter.toLowerCase()) ||
        r.ita.toLowerCase().includes(filter.toLowerCase())
      )
    : rows.map((r, i) => ({ ...r, _i: i }))

  // ── Editing inline ──────────────────────────────────────────────────────────
  const startEdit = (index, field, current) => {
    setEditing({ index, field })
    setEditVal(current)
  }

  const commitEdit = () => {
    if (!editing) return
    onUpdateRow(editing.index, editing.field, editVal)
    setEditing(null)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); commitEdit() }
    if (e.key === 'Escape') setEditing(null)
  }

  // ── Selezione righe per AI ──────────────────────────────────────────────────
  const toggleSelect = (i) => {
    setSelected(s => {
      const n = new Set(s)
      n.has(i) ? n.delete(i) : n.add(i)
      return n
    })
  }

  const handleRework = async () => {
    const indices = [...selected].sort((a, b) => a - b)
    const sentences = indices.map(i => rows[i].ita).filter(Boolean)
    if (!sentences.length) return
    setReworking(true)
    try {
      const result = await onRework(sentences)
      setReworkResult({ indices, texts: result })
    } catch (e) {
      alert('Errore AI: ' + e.message)
    } finally {
      setReworking(false)
    }
  }

  const acceptRework = (idx, text) => {
    onUpdateRow(idx, 'ita', text)
    setReworkResult(prev => {
      const newIndices = prev.indices.filter(i => i !== idx)
      const pos = prev.indices.indexOf(idx)
      const newTexts = prev.texts.filter((_, i) => i !== pos)
      return newIndices.length ? { indices: newIndices, texts: newTexts } : null
    })
    setSelected(s => { const n = new Set(s); n.delete(idx); return n })
  }

  const dismissRework = () => { setReworkResult(null) }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px)' }}>

      {/* Toolbar tabella */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 16px',
        background: 'var(--bg2)', borderBottom: '1px solid var(--border)',
      }}>
        <input
          placeholder="Filtra per personaggio o testo…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{
            background: 'var(--bg3)', border: '1px solid var(--border)',
            color: 'var(--text)', borderRadius: 8, padding: '6px 12px',
            fontSize: 13, width: 280,
          }}
        />
        {selected.size > 0 && (
          <>
            <span style={{ color: 'var(--text2)', fontSize: 13 }}>
              {selected.size} {selected.size === 1 ? 'riga selezionata' : 'righe selezionate'}
            </span>
            <button
              onClick={handleRework}
              disabled={reworking}
              style={{
                background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
                color: '#fff', borderRadius: 8, padding: '6px 16px',
                fontSize: 13, fontWeight: 600,
              }}
            >
              {reworking ? '⏳ Rielaborazione…' : '✨ Rielabora con AI'}
            </button>
            <button
              onClick={() => setSelected(new Set())}
              style={{
                background: 'none', border: '1px solid var(--border)',
                color: 'var(--text2)', borderRadius: 8, padding: '6px 12px', fontSize: 13,
              }}
            >
              Deseleziona
            </button>
          </>
        )}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: 12, color: 'var(--text2)' }}>
          Clicca una cella per modificarla · Seleziona righe per la rielaborazione AI
        </span>
      </div>

      {/* Pannello risultati AI */}
      {reworkResult && (
        <div style={{
          background: '#1a1f35', borderBottom: '1px solid #4f7cff44',
          padding: '12px 16px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <span style={{ fontSize: 14, fontWeight: 500 }}>✨ Proposte AI</span>
            <span style={{ fontSize: 12, color: 'var(--text2)' }}>
              Clicca "Accetta" per applicare, oppure ignora
            </span>
            <button onClick={dismissRework} style={{
              marginLeft: 'auto', background: 'none',
              color: 'var(--text2)', fontSize: 18,
            }}>×</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {reworkResult.indices.map((rowIdx, pos) => (
              <div key={rowIdx} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '8px 12px', background: 'var(--bg3)',
                borderRadius: 8, border: '1px solid var(--border)'
              }}>
                <div style={{ flex: 1, fontSize: 13 }}>
                  <div style={{ color: 'var(--text2)', fontSize: 11, marginBottom: 3, fontFamily: 'var(--mono)' }}>
                    Riga {rowIdx + 1} · {rows[rowIdx]?.personaggio}
                  </div>
                  <div style={{ color: 'var(--text2)', textDecoration: 'line-through', marginBottom: 4 }}>
                    {rows[rowIdx]?.ita}
                  </div>
                  <div style={{ color: '#7cf0a0' }}>
                    {reworkResult.texts[pos]}
                  </div>
                </div>
                <button
                  onClick={() => acceptRework(rowIdx, reworkResult.texts[pos])}
                  style={{
                    background: 'var(--green)', color: '#000',
                    borderRadius: 6, padding: '4px 12px', fontSize: 12, fontWeight: 600,
                    flexShrink: 0, marginTop: 4,
                  }}
                >Accetta</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabella */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--bg2)', position: 'sticky', top: 0, zIndex: 10 }}>
              <th style={th}>☐</th>
              <th style={{ ...th, width: 60 }}>Colore</th>
              <th style={{ ...th, width: 160 }}>Personaggio</th>
              <th style={{ ...th }}>ITA</th>
              <th style={{ ...th, width: 200 }}>Note</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => {
              const i = row._i
              const isSelected = selected.has(i)
              const colorKey = row.colore
              const rowBg = isSelected
                ? 'rgba(79,124,255,0.12)'
                : colorKey ? COLOR_BG[colorKey] : 'transparent'
              const isNote = !row.ita && row.note

              return (
                <tr key={i} style={{
                  background: rowBg,
                  borderBottom: '1px solid var(--border)',
                  opacity: isNote ? 0.6 : 1,
                }}>
                  {/* Checkbox selezione */}
                  <td style={{ ...td, width: 36, textAlign: 'center' }}>
                    {!isNote && (
                      <input type="checkbox" checked={isSelected}
                        onChange={() => toggleSelect(i)}
                        style={{ accentColor: 'var(--accent)', cursor: 'pointer' }} />
                    )}
                  </td>

                  {/* Colore */}
                  <td style={{ ...td, width: 60, textAlign: 'center' }}>
                    {colorKey && (
                      <span style={{
                        display: 'inline-block', width: 20, height: 20,
                        borderRadius: 4, background: COLOR_HEX[colorKey],
                        border: '1px solid rgba(255,255,255,0.2)',
                        verticalAlign: 'middle'
                      }} title={colorKey} />
                    )}
                  </td>

                  {/* Personaggio */}
                  <EditCell
                    value={row.personaggio}
                    isEditing={editing?.index === i && editing?.field === 'personaggio'}
                    editVal={editVal}
                    onStart={() => startEdit(i, 'personaggio', row.personaggio)}
                    onEdit={setEditVal}
                    onCommit={commitEdit}
                    onKey={handleKey}
                    style={{ width: 160, fontWeight: isNote ? 400 : 500 }}
                  />

                  {/* ITA */}
                  <EditCell
                    value={row.ita}
                    isEditing={editing?.index === i && editing?.field === 'ita'}
                    editVal={editVal}
                    onStart={() => startEdit(i, 'ita', row.ita)}
                    onEdit={setEditVal}
                    onCommit={commitEdit}
                    onKey={handleKey}
                    style={{ fontFamily: row.ita ? 'inherit' : 'var(--mono)', color: row.ita ? 'var(--text)' : 'var(--text2)' }}
                    multiline
                  />

                  {/* Note */}
                  <EditCell
                    value={row.note}
                    isEditing={editing?.index === i && editing?.field === 'note'}
                    editVal={editVal}
                    onStart={() => startEdit(i, 'note', row.note)}
                    onEdit={setEditVal}
                    onCommit={commitEdit}
                    onKey={handleKey}
                    style={{ width: 200, color: 'var(--text2)', fontStyle: row.note ? 'italic' : 'normal' }}
                  />
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Componente cella editabile ─────────────────────────────────────────────────
function EditCell({ value, isEditing, editVal, onStart, onEdit, onCommit, onKey, style, multiline }) {
  return (
    <td style={{ ...td, ...style }} onClick={!isEditing ? onStart : undefined}>
      {isEditing ? (
        multiline ? (
          <textarea
            autoFocus
            value={editVal}
            onChange={e => onEdit(e.target.value)}
            onBlur={onCommit}
            onKeyDown={onKey}
            style={{
              width: '100%', minHeight: 60, background: 'var(--bg3)',
              border: '1px solid var(--accent)', borderRadius: 4,
              color: 'var(--text)', padding: '4px 6px', fontSize: 13,
              fontFamily: 'inherit', resize: 'vertical',
            }}
          />
        ) : (
          <input
            autoFocus
            value={editVal}
            onChange={e => onEdit(e.target.value)}
            onBlur={onCommit}
            onKeyDown={onKey}
            style={{
              width: '100%', background: 'var(--bg3)',
              border: '1px solid var(--accent)', borderRadius: 4,
              color: 'var(--text)', padding: '4px 6px', fontSize: 13,
            }}
          />
        )
      ) : (
        <span style={{ cursor: 'text', display: 'block', minHeight: 20, padding: '2px 0' }}>
          {value || <span style={{ color: 'var(--text2)', fontStyle: 'italic', opacity: 0.5 }}>—</span>}
        </span>
      )}
    </td>
  )
}

const th = {
  padding: '9px 12px',
  textAlign: 'left',
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--text2)',
  borderBottom: '1px solid var(--border)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  userSelect: 'none',
}

const td = {
  padding: '7px 12px',
  verticalAlign: 'top',
  maxWidth: 400,
}
