'use client'

import { useState, useRef } from 'react'

const QUICK_QUESTIONS = [
  'What does this project do?',
  'How is the repo structured?',
  'What are the main entry points?',
  'Explain the main request / data flow',
  'What are the most important files?',
  'What dependencies are used?',
  'How is authentication handled?',
]

const BACKEND_URL = 'http://localhost:8000'

export default function AskTab({ onEvidenceUpdate, onFilesUpdate }) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [claims, setClaims] = useState([])
  const [confidence, setConfidence] = useState(null)
  const [confidenceLabel, setConfidenceLabel] = useState(null)
  const textareaRef = useRef(null)

  const handleQuickSelect = (question) => {
    setActiveQuestion(question)
    setInputValue(question)
    textareaRef.current?.focus()
  }

  const handleInputChange = (e) => {
    setInputValue(e.target.value)
    setActiveQuestion(null)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleAsk = async () => {
    const question = inputValue.trim()
    if (!question || loading) return

    const repoId = localStorage.getItem('repoId') || 'demo_repo'

    setLoading(true)
    setError(null)
    setClaims([])
    setConfidence(null)
    setConfidenceLabel(null)
    onEvidenceUpdate([])

    try {
      const response = await fetch(`${BACKEND_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repoId, question }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong')
      }

      // Backend returns claims as [{ claim: "...", evidence: ["E1"] }]
      // and chunks as the evidence items
      setClaims(data.claims || [])
      setConfidence(data.confidence_score ?? null)
      setConfidenceLabel(data.confidence_label ?? null)
      onEvidenceUpdate(data.chunks || [])
      onFilesUpdate(data.chunks?.length ?? 0)

    } catch (err) {
      // Distinguish between backend being down vs actual errors
      if (err.message === 'Failed to fetch') {
        setError('Cannot reach backend. Make sure the Python server is running on port 8000 (cd backend && uvicorn main:app --reload).')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const hasResults = claims.length > 0

  const formatConfidenceLabel = (label) => {
    if (!label) return ''
    return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase()
  }

  return (
    <>
      <div className="section-label">Overview / Project Map</div>

      <div className="quick-buttons">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            className={`quick-btn ${activeQuestion === q ? 'active' : ''}`}
            onClick={() => handleQuickSelect(q)}
          >
            {q}
          </button>
        ))}
      </div>

      <div className="search-area">
        <textarea
          ref={textareaRef}
          className="search-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask anything about your codebase..."
          disabled={loading}
        />
        <button
          className="ask-btn"
          onClick={handleAsk}
          disabled={loading || !inputValue.trim()}
          style={{ opacity: loading || !inputValue.trim() ? 0.5 : 1 }}
        >
          {loading ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0e0e12" strokeWidth="2.5" style={{ animation: 'spin 1s linear infinite' }}>
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0e0e12" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          )}
        </button>
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

      {/* Loading skeleton */}
      {loading && (
        <div style={{ padding: '0 20px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', color: 'var(--text-dim)', fontSize: '12px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }}>
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            Analyzing code...
          </div>
          {[1, 2, 3].map(i => (
            <div key={i} style={{
              background: 'var(--surface2)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '10px',
            }}>
              <div style={{ height: '12px', background: 'var(--border)', borderRadius: '4px', width: '40%', marginBottom: '10px', animation: 'pulse 1.5s ease-in-out infinite' }} />
              <div style={{ height: '10px', background: 'var(--border)', borderRadius: '4px', width: '90%', marginBottom: '6px', animation: 'pulse 1.5s ease-in-out infinite' }} />
              <div style={{ height: '10px', background: 'var(--border)', borderRadius: '4px', width: '75%', animation: 'pulse 1.5s ease-in-out infinite' }} />
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {hasResults && !loading && (
        <>
          {confidence !== null && (
            <div className="confidence-bar-wrap">
              <span className="conf-label">Retrieval Confidence</span>
              <div className="conf-track">
                <div className="conf-fill" style={{ width: `${confidence * 100}%` }} />
              </div>
              <span className="conf-val">{confidence.toFixed(2)}</span>
              <span className="conf-tag">{formatConfidenceLabel(confidenceLabel)}</span>
            </div>
          )}

          <div className="analysis-header">
            <span className="analysis-title">Analysis</span>
            <div className="analysis-right">
              <div className="overview-tag">Overview</div>
              <span className="claims-tag">{claims.length} claims</span>
            </div>
          </div>

          <div className="cards-area">
            {claims.map((item, i) => (
              <div key={i} className="card">
                <div className="card-header">
                  <span className="card-title">Finding {i + 1}</span>
                  <span className="project-map-tag">Project Map</span>
                </div>
                {/* Backend returns { claim: "...", evidence: ["E1", "E2"] } */}
                <div className="card-body">{item.claim}</div>
                {item.evidence && item.evidence.length > 0 && (
                  <div className="evidence-tags">
                    {item.evidence.map((eId, j) => (
                      <span key={j} className="ev-tag">{eId}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Empty state */}
      {!hasResults && !loading && !error && (
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-dim)',
          padding: '40px 20px',
          textAlign: 'center',
          gap: '10px',
        }}>
          <div style={{ fontSize: '32px', opacity: 0.3 }}>⌨</div>
          <div style={{ fontSize: '12px', lineHeight: 1.6, maxWidth: '240px' }}>
            Ask anything about your codebase. Results will appear here.
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
