'use client'

function getRelevanceClass(relevance) {
  if (relevance >= 0.75) return 'pct-high'
  if (relevance >= 0.5) return 'pct-med'
  return 'pct-low'
}

function getBarGradient(relevance, index) {
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

function EmptyState({ totalFiles }) {
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
        {totalFiles
          ? `${totalFiles} files indexed. Ask a question to see relevant evidence.`
          : 'Evidence from your codebase will appear here after you ask a question.'}
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
          {evidence.length > 0 ? `${evidence.length} chunks` : totalFiles ? `${totalFiles} files` : '—'}
        </span>
      </div>

      {evidence.length === 0 ? (
        <EmptyState totalFiles={totalFiles} />
      ) : (
        <div className="evidence-list">
          {evidence.map((ev, i) => {
            const relevancePct = Math.round((ev.relevance ?? 0) * 100)
            const relClass = getRelevanceClass(ev.relevance ?? 0)
            const gradient = getBarGradient(ev.relevance, i)

            // Split filename into path + highlighted filename
            const parts = ev.filename ? ev.filename.split('/') : ['']
            const filename = parts.pop()
            const filePath = parts.length > 0 ? parts.join('/') + '/' : ''

            return (
              <div key={i} className="ev-card">
                <div className="ev-top-bar" style={{ background: gradient }} />
                <div className="ev-meta">
                  <span className="ev-num">E{i + 1}</span>
                  <span className="ev-file">
                    {filePath}<span>{filename}</span>
                  </span>
                  {ev.startLine && (
                    <span className="ev-lines">L{ev.startLine}–{ev.endLine}</span>
                  )}
                  <span className={`ev-pct ${relClass}`}>{relevancePct}%</span>
                </div>
                {ev.snippet && (
                  <div className="ev-code" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {ev.snippet}
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
