import { useState, useCallback } from 'react'

const API = import.meta.env.VITE_API_URL || ''

function friendlyError(msg) {
  if (!msg) return 'Errore sconosciuto.'
  if (msg.includes('503') || msg.toLowerCase().includes('high demand') || msg.toLowerCase().includes('unavailable'))
    return 'I server AI sono momentaneamente molto occupati. Il sistema sta riprovando automaticamente — attendi qualche secondo e riprova.'
  if (msg.includes('429') || msg.toLowerCase().includes('quota'))
    return 'Limite di richieste raggiunto. Attendi qualche minuto e riprova.'
  if (msg.includes('404'))
    return 'Modello AI non disponibile. Contatta l\'amministratore.'
  if (msg.includes('GEMINI_API_KEY'))
    return 'Chiave API non configurata sul server.'
  return msg
}

export default function ItaPlusView({ onBack }) {
  const [step, setStep]           = useState('upload')
  const [sessionId, setSessionId] = useState(null)
  const [filename, setFilename]   = useState('')
  const [headers, setHeaders]     = useState([])
  const [colIndex, setColIndex]   = useState(0)
  const [rows, setRows]           = useState([])
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState('')
  const [dragging, setDragging]   = useState(false)

  const handleFile = useCallback(async (file) => {
    if (!file.name.match(/\.xlsx?$/)) { alert('Seleziona un file .xlsx'); return }
    setLoading(true); setError('')
    try {
      const fd = new FormData(); fd.append('file', file)
      const res = await fetch(`${API}/api/itaplus/upload`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setSessionId(data.session_id); setFilename(data.filename); setHeaders(data.headers)
      const itaIdx = data.headers.findIndex(h => h && h.toString().toUpperCase() === 'ITA')
      setColIndex(itaIdx >= 0 ? itaIdx : 0)
      setStep('column')
    } catch (e) { setError(friendlyError(e.message)) }
    finally { setLoading(false) }
  }, [])

  const onDrop = (e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }

  const handleProcess = async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API}/api/itaplus/process`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, column_index: colIndex })
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setRows(data.rows); setStep('review')
    } catch (e) { setError(friendlyError(e.message)) }
    finally { setLoading(false) }
  }

  const handleEdit = useCallback(async (rowIndex, value) => {
    setRows(prev => prev.map((r, i) => i === rowIndex ? { ...r, accepted: value } : r))
    try {
      await fetch(`${API}/api/itaplus/update`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, row_index: rowIndex, value })
      })
    } catch (e) { setError(friendlyError(e.message)) }
  }, [sessionId])

  const handleSave = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/itaplus/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
      if (!res.ok) throw new Error('Errore esportazione')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url
      a.download = 'soprattitoli_itaplus.xlsx'; a.click()
      URL.revokeObjectURL(url); setStep('done')
    } catch (e) { setError(friendlyError(e.message)) }
    finally { setLoading(false) }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <button onClick={onBack} style={{ background: 'none', color: 'var(--text2)', fontSize: 13 }}>← Menu</button>
        <div style={{ width: 1, height: 16, background: 'var(--border)' }} />
        <span style={{ fontSize: 15, fontWeight: 600 }}>ITA+</span>
        {filename && <span style={{ fontSize: 13, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>{filename}</span>}
      </div>

      {error && (
        <div style={{
          padding: '12px 16px', marginBottom: 16,
          background: '#1e1010', border: '1px solid #7a2020',
          borderRadius: 10, color: '#ffaaaa', fontSize: 14, lineHeight: 1.5
        }}>
          ⚠ {error}
          <button onClick={() => setError('')} style={{ float: 'right', background: 'none', color: '#ffaaaa', fontSize: 18, lineHeight: 1 }}>×</button>
        </div>
      )}

      {step === 'upload' && (
        <div
          onDrop={onDrop}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onClick={() => document.getElementById('xlsx-input').click()}
          style={{
            border: `2px dashed ${dragging ? 'var(--accent2)' : 'var(--border)'}`,
            borderRadius: 16, padding: '60px 40px',
            background: dragging ? 'rgba(124,92,255,0.06)' : 'var(--bg2)',
            textAlign: 'center', cursor: 'pointer',
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
          <p style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>
            {loading ? 'Caricamento…' : 'Trascina il file Excel qui'}
          </p>
          <p style={{ color: 'var(--text2)', fontSize: 13 }}>oppure clicca · solo .xlsx</p>
          <input id="xlsx-input" type="file" accept=".xlsx,.xls"
            style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
        </div>
      )}

      {step === 'column' && (
        <div style={{ maxWidth: 480 }}>
          <div style={{
            background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: 12, padding: '20px 24px', marginBottom: 16
          }}>
            <p style={{ fontWeight: 500, marginBottom: 8 }}>Quale colonna contiene le frasi da riformulare?</p>
            <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 16 }}>Di solito è la colonna "ITA"</p>
            <select value={colIndex} onChange={e => setColIndex(parseInt(e.target.value))} style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              color: 'var(--text)', borderRadius: 8, padding: '8px 12px',
              fontSize: 14, width: '100%'
            }}>
              {headers.map((h, i) => <option key={i} value={i}>{h || `Colonna ${i+1}`}</option>)}
            </select>
          </div>
          {loading && (
            <div style={{
              padding: '12px 16px', marginBottom: 16,
              background: '#0f1a2e', border: '1px solid var(--accent)',
              borderRadius: 10, color: 'var(--text2)', fontSize: 13
            }}>
              ✨ Riformulazione in corso… L'AI sta elaborando le frasi. Può richiedere 30-60 secondi. In caso di sovraccarico dei server, il sistema riprova automaticamente.
            </div>
          )}
          <button onClick={handleProcess} disabled={loading} style={{
            width: '100%',
            background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
            color: '#fff', borderRadius: 10, padding: '13px 0',
            fontSize: 15, fontWeight: 600,
          }}>
            {loading ? '⏳ Elaborazione in corso…' : '✨ Riformula con AI'}
          </button>
        </div>
      )}

      {step === 'review' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <p style={{ color: 'var(--text2)', fontSize: 13 }}>
              Clicca sulla colonna <strong style={{ color: 'var(--text)' }}>ITA+</strong> per modificare prima di salvare
            </p>
            <button onClick={handleSave} disabled={loading} style={{
              background: 'var(--green)', color: '#000',
              borderRadius: 8, padding: '8px 20px', fontSize: 14, fontWeight: 600,
            }}>
              {loading ? 'Salvataggio…' : '↓ Salva ed esporta Excel'}
            </button>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: 'var(--bg2)' }}>
                  <th style={th}>#</th>
                  <th style={th}>ITA (originale)</th>
                  <th style={{ ...th, color: 'var(--accent2)' }}>ITA+ (proposta AI — clicca per modificare)</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => <ReviewRow key={i} row={row} index={i} onEdit={handleEdit} />)}
              </tbody>
            </table>
          </div>
        </>
      )}

      {step === 'done' && (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ fontSize: 22, marginBottom: 8 }}>File scaricato!</h2>
          <p style={{ color: 'var(--text2)', marginBottom: 24 }}>
            Il file Excel con la colonna ITA+ è stato salvato nel tuo computer.
          </p>
          <button onClick={onBack} style={{
            background: 'var(--accent)', color: '#fff',
            borderRadius: 8, padding: '10px 24px', fontSize: 14, fontWeight: 600,
          }}>Torna al menu</button>
        </div>
      )}
    </div>
  )
}

function ReviewRow({ row, index, onEdit }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(row.accepted)
  const commit = () => { setEditing(false); onEdit(index, val) }
  return (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      <td style={{ ...td, width: 40, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>{index+1}</td>
      <td style={{ ...td, color: 'var(--text2)' }}>{row.original || '—'}</td>
      <td style={{ ...td, cursor: 'text' }} onClick={() => !editing && setEditing(true)}>
        {editing ? (
          <textarea autoFocus value={val}
            onChange={e => setVal(e.target.value)} onBlur={commit}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); commit() } }}
            style={{
              width: '100%', minHeight: 50, background: 'var(--bg3)',
              border: '1px solid var(--accent2)', borderRadius: 4,
              color: 'var(--text)', padding: '4px 6px', fontSize: 13,
              fontFamily: 'inherit', resize: 'vertical',
            }}
          />
        ) : (
          <span style={{ color: val ? '#a0f0c0' : 'var(--text2)' }}>{val || '—'}</span>
        )}
      </td>
    </tr>
  )
}

const th = { padding: '9px 12px', textAlign: 'left', fontSize: 12, fontWeight: 600,
  color: 'var(--text2)', borderBottom: '1px solid var(--border)',
  textTransform: 'uppercase', letterSpacing: '0.05em' }
const td = { padding: '7px 12px', verticalAlign: 'top' }
