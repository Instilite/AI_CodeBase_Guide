'use client'

import { useState, useEffect } from 'react'

const badgeClass = {
  High: 'badge-high',
  Medium: 'badge-med',
  Low: 'badge-low',
}

export default function ImpactTab() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [analyzed, setAnalyzed] = useState(false)

  const analyze = async () => {
    const sessionId = localStorage.getItem('uploadSessionId')
    if (!sessionId) {
      setError('No repo uploaded. Please upload a repo first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/impact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong')
      }

      setFiles(data.files || [])
      setAnalyzed(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Auto-analyze when tab mounts if a session exists
  useEffect(() => {
    const sessionId = localStorage.getItem('uploadSessionId')
    if (sessionId && !analyzed) {
      analyze()
    }
  }, [])

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-dim)', fontSize: '12px', marginBottom: '16px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }}>
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          Analyzing file impact...
        </div>
        {[1, 2, 3, 4].map(i => (
          <div key={i} style={{
            background: 'var(--surface2)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '10px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ height: '12px', background: 'var(--border)', borderRadius: '4px', width: '35%', animation: 'pulse 1.5s ease-in-out infinite' }} />
              <div style={{ height: '12px', background: 'var(--border)', borderRadius: '4px', width: '15%', animation: 'pulse 1.5s ease-in-out infinite' }} />
            </div>
            <div style={{ height: '3px', background: 'var(--border)', borderRadius: '2px', marginBottom: '8px', animation: 'pulse 1.5s ease-in-out infinite' }} />
            <div style={{ height: '10px', background: 'var(--border)', borderRadius: '4px', width: '80%', animation: 'pulse 1.5s ease-in-out infinite' }} />
          </div>
        ))}
        <style>{`
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
          @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
        `}</style>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{
          padding: '12px 16px',
          background: 'rgba(245,80,80,0.1)',
          border: '1px solid rgba(245,80,80,0.3)',
          borderRadius: '8px',
          color: '#f55050',
          fontSize: '12px',
          marginBottom: '12px',
        }}>
          {error}
        </div>
        <button
          onClick={analyze}
          style={{
            background: 'var(--accent)',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            color: '#0e0e12',
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  if (!analyzed) {
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
        gap: '12px',
      }}>
        <div style={{ fontSize: '32px', opacity: 0.3 }}>◈</div>
        <div style={{ fontSize: '12px', lineHeight: 1.6, maxWidth: '220px' }}>
          Upload a repo to analyze file impact
        </div>
        <button
          onClick={analyze}
          style={{
            background: 'var(--accent)',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            color: '#0e0e12',
            fontFamily: 'inherit',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
          }}
        >
          Analyze
        </button>
      </div>
    )
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px 10px' }}>
        <div className="section-label" style={{ padding: 0 }}>Impact Analysis</div>
        <button
          onClick={analyze}
          style={{
            background: 'var(--surface2)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '4px 10px',
            color: 'var(--text-muted)',
            fontFamily: 'inherit',
            fontSize: '10px',
            cursor: 'pointer',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}
        >
          Re-analyze
        </button>
      </div>

      <div className="impact-grid">
        {files.map((file) => (
          <div key={file.filename} className="impact-card">
            <div className="impact-card-header">
              <span className="impact-card-title" style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '140px',
                title: file.filename,
              }}>
                {file.filename.split('/').pop()}
              </span>
              <span className={`impact-badge ${badgeClass[file.impactLabel] || 'badge-low'}`}>
                {file.impactLabel}
              </span>
            </div>
            <div className="impact-bar-wrap">
              <div className="impact-bar" style={{ width: `${Math.round((file.impact ?? 0) * 100)}%` }} />
            </div>
            <div className="impact-desc">{file.summary}</div>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
      `}</style>
    </>
  )
}
