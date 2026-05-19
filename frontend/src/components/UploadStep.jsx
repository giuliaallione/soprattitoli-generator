import { useCallback, useState } from 'react'

export default function UploadStep({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false)

  const handleFile = (file) => {
    if (!file) return
    if (!file.name.endsWith('.docx')) {
      alert('Seleziona un file .docx (Word)')
      return
    }
    onUpload(file)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  return (
    <div style={{ maxWidth: 520, margin: '60px auto', textAlign: 'center' }}>
      <h1 style={{ fontSize: 28, fontWeight: 600, marginBottom: 8, letterSpacing: '-0.5px' }}>
        Soprattitoli Generator
      </h1>
      <p style={{ color: 'var(--text2)', marginBottom: 40, fontSize: 15 }}>
        Carica un copione Word per generare la tabella soprattitoli
      </p>

      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 16,
          padding: '60px 40px',
          background: dragging ? 'rgba(79,124,255,0.06)' : 'var(--bg2)',
          transition: 'all 0.2s',
          cursor: 'pointer',
        }}
        onClick={() => document.getElementById('file-input').click()}
      >
        <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
        <p style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>
          {loading ? 'Caricamento…' : 'Trascina il file qui'}
        </p>
        <p style={{ color: 'var(--text2)', fontSize: 13 }}>
          oppure clicca per selezionare · solo .docx
        </p>
        <input
          id="file-input"
          type="file"
          accept=".docx"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>
    </div>
  )
}
