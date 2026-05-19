import { useState, useCallback, useRef } from 'react'
import UploadStep from './components/UploadStep.jsx'
import CriteriaModal from './components/CriteriaModal.jsx'
import ColorModal from './components/ColorModal.jsx'
import TableView from './components/TableView.jsx'
import TopBar from './components/TopBar.jsx'

// URL base del backend — in produzione Render lo imposta automaticamente
const API = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [step, setStep] = useState('upload')  // 'upload' | 'criteria' | 'table'
  const [sessionId, setSessionId] = useState(null)
  const [filename, setFilename] = useState('')
  const [rows, setRows] = useState([])
  const [proposedColors, setProposedColors] = useState([])
  const [showColorModal, setShowColorModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stats, setStats] = useState({ total: 0, characters: 0 })

  // ── Upload ──────────────────────────────────────────────────────────────────
  const handleUpload = useCallback(async (file) => {
    setLoading(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail || 'Errore upload')
      const data = await res.json()
      setSessionId(data.session_id)
      setFilename(data.filename)
      setStep('criteria')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Processa con criteri ────────────────────────────────────────────────────
  const handleProcess = useCallback(async (criteria) => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/api/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, ...criteria })
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Errore elaborazione')
      const data = await res.json()
      setRows(data.rows)
      setStats({ total: data.total, characters: data.characters })
      setProposedColors(data.proposed_colors)
      setStep('table')
      setShowColorModal(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  // ── Assegna colori ──────────────────────────────────────────────────────────
  const handleColors = useCallback(async (assignments) => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/colors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, assignments })
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setRows(data.rows)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setShowColorModal(false)
    }
  }, [sessionId])

  // ── Aggiorna riga ───────────────────────────────────────────────────────────
  const handleUpdateRow = useCallback(async (index, field, value) => {
    // Aggiorna subito la UI (ottimistico)
    setRows(prev => prev.map((r, i) => i === index ? { ...r, [field]: value } : r))
    // Poi sincronizza col server
    try {
      await fetch(`${API}/api/update-row`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, index, field, value })
      })
    } catch (e) {
      setError('Errore salvataggio modifica: ' + e.message)
    }
  }, [sessionId])

  // ── Rielabora con AI ────────────────────────────────────────────────────────
  const handleRework = useCallback(async (sentences) => {
    const res = await fetch(`${API}/api/rework`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sentences })
    })
    if (!res.ok) throw new Error((await res.json()).detail || 'Errore AI')
    const data = await res.json()
    return data.reworked
  }, [])

  // ── Esporta Excel ───────────────────────────────────────────────────────────
  const handleExport = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
      if (!res.ok) throw new Error('Errore esportazione')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'soprattitoli.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  // ── Reset ───────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setStep('upload')
    setSessionId(null)
    setFilename('')
    setRows([])
    setProposedColors([])
    setError('')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopBar
        step={step}
        filename={filename}
        stats={stats}
        onColorClick={() => setShowColorModal(true)}
        onExport={handleExport}
        onReset={handleReset}
        loading={loading}
      />

      {error && (
        <div style={{
          margin: '12px 24px 0',
          padding: '10px 16px',
          background: '#2d1a1a',
          border: '1px solid #7a2020',
          borderRadius: 8,
          color: '#ff8080',
          fontSize: 14
        }}>
          ⚠ {error}
          <button onClick={() => setError('')} style={{
            float: 'right', background: 'none', color: '#ff8080', fontSize: 16
          }}>×</button>
        </div>
      )}

      <main style={{ flex: 1, padding: step === 'table' ? 0 : '40px 24px' }}>
        {step === 'upload' && (
          <UploadStep onUpload={handleUpload} loading={loading} />
        )}
        {step === 'criteria' && (
          <CriteriaModal
            filename={filename}
            onConfirm={handleProcess}
            onBack={() => setStep('upload')}
            loading={loading}
          />
        )}
        {step === 'table' && (
          <TableView
            rows={rows}
            onUpdateRow={handleUpdateRow}
            onRework={handleRework}
          />
        )}
      </main>

      {showColorModal && (
        <ColorModal
          proposed={proposedColors}
          onAccept={handleColors}
          onSkip={() => setShowColorModal(false)}
          onManual={handleColors}
        />
      )}
    </div>
  )
}
