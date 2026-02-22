'use client'

// Backend returns chunks with: evidence_id, file_path, start_line, end_line, text, similarity
function getSimClass(similarity) {
  if (similarity >= 0.65) return 'pct-high'
  if (similarity >= 0.45) return 'pct-med'
  return 'pct-low'
}

function getBarGradient(index) {
  const gradients = [
    'linear-gradient(90deg,#3dd68c,#3dd68c88)',
    'linear-gradient(90deg,#3dd68c88,#f5a62388)',
    'linear-gradient(90deg,#f5a62388,#f5a62344)',
    'linear-gradient(90deg,#f5a62344,#7c6af755)',
    'linear-gradient(90deg,#7c6af755,#7c6af733)',
    'linear-gradient(90deg,#7c6af733,#7c6af722)',
    'linear-gradient(90deg,#f5505022,#f5505011)',
  ]
  return gradients[index % gradients.length]
}

function EmptyState() {
  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--text-dim)',
      padding: '40px',
      textAlign: 'center',
      gap: '10px',
    }}>
      <div style={{ fontSize: '32px', opacity: 0.3 }}>◈</div>
      <div style={{ fontSize: '12px', lineHeight: 1.6, maxWidth: '220px' }}>
        Evidence from your codebase will appear here after you ask a question.
      </div>
    </div>
  )
}

export default function RightPanel({ evidence = [], totalFiles }) {
  return (
    <div className="right-panel">
      <div className="evidence-header">
        <span className="evidence-label">Evidence</span>
        <span className="chunks-tag">
          {evidence.length > 0 ? `${evidence.length} chunks` : '—'}
        </span>
      </div>

      {evidence.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="evidence-list">
          {evidence.map((chunk, i) => {
            const similarity = chunk.similarity ?? 0
            const simPct = Math.round(similarity * 100)
            const simClass = getSimClass(similarity)
            const gradient = getBarGradient(i)

            // Split file_path into folder + filename
            const parts = (chunk.file_path || '').split('/')
            const filename = parts.pop()
            const filePath = parts.length > 0 ? parts.join('/') + '/' : ''

            return (
              <div key={chunk.evidence_id || i} className="ev-card">
                <div className="ev-top-bar" style={{ background: gradient }} />
                <div className="ev-meta">
                  <span className="ev-num">{chunk.evidence_id || `E${i + 1}`}</span>
                  <span className="ev-file">
                    {filePath}<span>{filename}</span>
                  </span>
                  {chunk.start_line && (
                    <span className="ev-lines">L{chunk.start_line}–{chunk.end_line}</span>
                  )}
                  <span className={`ev-pct ${simClass}`}>{simPct}%</span>
                </div>
                {chunk.text && (
                  <div className="ev-code" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {chunk.text}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
