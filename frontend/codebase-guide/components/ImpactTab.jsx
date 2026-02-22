'use client'

import { useState } from 'react'

const BACKEND_URL = 'http://localhost:8000'

const riskColors = {
  High:   { bg: 'rgba(245,80,80,0.1)',   border: 'rgba(245,80,80,0.3)',   color: '#f55050' },
  Medium: { bg: 'rgba(245,166,35,0.15)', border: 'rgba(245,166,35,0.3)',  color: 'var(--accent)' },
  Low:    { bg: 'rgba(61,214,140,0.1)',  border: 'rgba(61,214,140,0.3)',  color: 'var(--green)' },
}

export default function ImpactTab() {
  const [functionName, setFunctionName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleSearch = async () => {
    const name = functionName.trim()
    if (!name || loading) return

    const repoId = localStorage.getItem('repoId') || 'demo_repo'

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${BACKEND_URL}/impact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repoId, function_name: name }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong')
      }

      setResult(data)
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        setError('Cannot reach backend. Make sure the Python server is running (cd backend && uvicorn main:app --reload).')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch()
  }

  const riskStyle = result ? (riskColors[result.risk_level] || riskColors.Low) : null

  return (
    <>
      <div className="section-label" style={{ paddingTop: '16px' }}>Impact Analysis</div>

      {/* Search bar */}
      <div style={{ padding: '0 20px 16px', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={functionName}
          onChange={e => setFunctionName(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter a function name..."
          disabled={loading}
          style={{
            flex: 1,
            background: 'var(--surface2)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '10px 14px',
            fontFamily: 'inherit',
            fontSize: '13px',
            color: 'var(--text)',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSearch}
          disabled={loading || !functionName.trim()}
          style={{
            background: 'var(--accent)',
            border: 'none',
            borderRadius: '8px',
            width: '42px',
            height: '42px',
            cursor: loading || !functionName.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !functionName.trim() ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          {loading ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0e0e12" strokeWidth="2.5" style={{ animation: 'spin 1s linear infinite' }}>
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0e0e12" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          )}
        </button>
      </div>

      <div style={{ fontSize: '11px', color: 'var(--text-dim)', padding: '0 20px 16px', lineHeight: 1.5 }}>
        Enter a function name to see how widely it's used across the codebase and what it does.
      </div>

      {/* Error */}
      {error && (
        <div style={{
          margin: '0 20px 16px',
          padding: '12px 16px',
          background: 'rgba(245,80,80,0.1)',
          border: '1px solid rgba(245,80,80,0.3)',
          borderRadius: '8px',
          color: '#f55050',
          fontSize: '12px',
          lineHeight: 1.6,
        }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ padding: '0 20px' }}>
          {[1, 2, 3].map(i => (
            <div key={i} style={{
              background: 'var(--surface2)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '10px',
            }}>
              <div style={{ height: '12px', background: 'var(--border)', borderRadius: '4px', width: '40%', marginBottom: '10px', animation: 'pulse 1.5s ease-in-out infinite' }} />
              <div style={{ height: '10px', background: 'var(--border)', borderRadius: '4px', width: '80%', animation: 'pulse 1.5s ease-in-out infinite' }} />
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div style={{ padding: '0 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Risk level + summary card */}
          <div style={{
            background: 'var(--surface2)',
            border: `1px solid ${riskStyle.border}`,
            borderRadius: '8px',
            padding: '16px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: '14px', color: 'var(--text)' }}>
                {result.function_name}
              </span>
              <span style={{
                fontSize: '10px',
                padding: '3px 10px',
                borderRadius: '10px',
                background: riskStyle.bg,
                border: `1px solid ${riskStyle.border}`,
                color: riskStyle.color,
                fontWeight: 700,
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
              }}>
                {result.risk_level} Risk
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: '10px' }}>
              {result.what_it_does}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
              Referenced in <strong style={{ color: 'var(--accent)' }}>{result.file_count}</strong> file{result.file_count !== 1 ? 's' : ''}
            </div>
          </div>

          {/* Files referencing this function */}
          {result.files_referencing && result.files_referencing.length > 0 && (
            <div style={{
              background: 'var(--surface2)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '16px',
            }}>
              <div style={{ fontSize: '10px', letterSpacing: '1.2px', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>
                Files Referencing
              </div>
              {result.files_referencing.map((file, i) => (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 0',
                  borderBottom: i < result.files_referencing.length - 1 ? '1px solid var(--border)' : 'none',
                  fontSize: '12px',
                  color: 'var(--accent2)',
                }}>
                  <span style={{ color: 'var(--text-dim)', fontSize: '10px', flexShrink: 0 }}>#{i + 1}</span>
                  {file}
                </div>
              ))}
            </div>
          )}

          {/* Evidence chunks */}
          {result.chunks && result.chunks.length > 0 && (
            <div style={{
              background: 'var(--surface2)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '16px',
            }}>
              <div style={{ fontSize: '10px', letterSpacing: '1.2px', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>
                Evidence
              </div>
              {result.chunks.map((chunk, i) => (
                <div key={i} style={{ marginBottom: i < result.chunks.length - 1 ? '12px' : 0 }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      background: 'var(--accent-dim)',
                      color: 'var(--accent)',
                      border: '1px solid rgba(245,166,35,0.3)',
                      borderRadius: '4px',
                      padding: '2px 7px',
                    }}>
                      {chunk.evidence_id}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--accent2)' }}>{chunk.file_path}</span>
                    <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>L{chunk.start_line}–{chunk.end_line}</span>
                  </div>
                  <div style={{
                    background: 'var(--code-bg)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    lineHeight: 1.7,
                  }}>
                    {chunk.text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
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
            Type a function name above to see its impact across the codebase.
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
      `}</style>
    </>
  )
}
