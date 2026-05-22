export default function MenuScreen({ onChoose }) {
  return (
    <div style={{
      maxWidth: 480, margin: '80px auto', textAlign: 'center', padding: '0 24px'
    }}>
      <h1 style={{ fontSize: 28, fontWeight: 600, marginBottom: 8, letterSpacing: '-0.5px' }}>
        Soprattitoli Generator
      </h1>
      <p style={{ color: 'var(--text2)', marginBottom: 48, fontSize: 15 }}>
        Scegli il percorso di lavoro
      </p>

      <div style={{ display: 'flex', gap: 16 }}>
        {/* ITA */}
        <button
          onClick={() => onChoose('ita')}
          style={{
            flex: 1,
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: '32px 20px',
            cursor: 'pointer',
            transition: 'all 0.15s',
            textAlign: 'left',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'var(--accent)'
            e.currentTarget.style.background = 'rgba(79,124,255,0.06)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.background = 'var(--bg2)'
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 12 }}>📄</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
            ITA
          </div>
          <div style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.5 }}>
            Carica un copione Word e genera la tabella soprattitoli con colonne Colore, Personaggio, ITA, Note
          </div>
        </button>

        {/* ITA+ */}
        <button
          onClick={() => onChoose('itaplus')}
          style={{
            flex: 1,
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: '32px 20px',
            cursor: 'pointer',
            transition: 'all 0.15s',
            textAlign: 'left',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'var(--accent2)'
            e.currentTarget.style.background = 'rgba(124,92,255,0.06)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.background = 'var(--bg2)'
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 12 }}>✨</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
            ITA+
          </div>
          <div style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.5 }}>
            Carica un file Excel esistente e aggiungi la colonna ITA+ con le frasi riformulate dall'AI
          </div>
        </button>
      </div>
    </div>
  )
}
