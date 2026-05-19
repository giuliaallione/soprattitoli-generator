export default function TopBar({ step, filename, stats, onColorClick, onExport, onReset, loading }) {
  return (
    <header style={{
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border)',
      padding: '0 24px',
      height: 56,
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Logo */}
      <button onClick={onReset} style={{
        background: 'none',
        color: 'var(--text)',
        fontFamily: 'var(--mono)',
        fontSize: 15,
        fontWeight: 500,
        letterSpacing: '-0.5px',
        padding: '4px 0',
        whiteSpace: 'nowrap',
      }}>
        ◈ Soprattitoli
      </button>

      {/* Separatore */}
      {step === 'table' && (
        <>
          <div style={{ width: 1, height: 20, background: 'var(--border)' }} />
          <span style={{ color: 'var(--text2)', fontSize: 13, fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 280 }}>
            {filename}
          </span>
          <span style={{ color: 'var(--text2)', fontSize: 12 }}>
            {stats.total} righe · {stats.characters} personaggi
          </span>
        </>
      )}

      <div style={{ flex: 1 }} />

      {/* Azioni visibili solo quando c'è la tabella */}
      {step === 'table' && (
        <>
          <button onClick={onColorClick} style={{
            background: 'var(--bg3)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
            borderRadius: 8,
            padding: '6px 14px',
            fontSize: 13,
          }}>
            🎨 Colori
          </button>
          <button onClick={onExport} disabled={loading} style={{
            background: 'var(--accent)',
            color: '#fff',
            borderRadius: 8,
            padding: '6px 16px',
            fontSize: 13,
            fontWeight: 500,
          }}>
            {loading ? 'Esportazione…' : '↓ Esporta Excel'}
          </button>
        </>
      )}
    </header>
  )
}
