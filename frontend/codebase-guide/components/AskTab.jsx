'use client'

import { useState, useRef } from 'react'
import { ApiError, ask } from '../lib/api'

const QUICK_QUESTIONS = [
  'What does this project do?',
  'How is the repo structured?',
  'What are the main entry points?',
  'Explain the main request / data flow',
  'What are the most important files?',
  'What dependencies are used?',
  'How is authentication handled?',
]

const toAskErrorMessage = (error) => {
  if (error instanceof ApiError) {
    if (error.error === 'indexing_in_progress') return 'Repo is still indexing. Wait for indexing to complete and try again.'
    if (error.error === 'repo_not_found') return 'Selected repo was not found. Refresh the repo list and select another repo.'
    if (error.error === 'validation_error') return 'Request validation failed. Check repo selection and question text.'
    return error.message
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'Unable to run Ask right now.'
}

export default function AskTab({
  selectedRepoId,
  disabledReason,
  onEvidenceUpdate,
  onFilesUpdate,
  onEvidenceSelect,
}) {
  const [activeQuestion, setActiveQuestion] = useState(null)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)
  const textareaRef = useRef(null)

  const handleQuickSelect = (question) => {
    if (loading) return
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

    if (!selectedRepoId || disabledReason) {
      setError(disabledReason || 'Select a repo before asking a question.')
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)
    onEvidenceUpdate([])
    onFilesUpdate(0)
    onEvidenceSelect?.(null)

    try {
      const data = await ask(selectedRepoId, question)
      setResponse(data)
      onEvidenceUpdate(data.chunks || [])
      onFilesUpdate(new Set((data.chunks || []).map((chunk) => chunk.file_path)).size)
    } catch (err) {
      setError(toAskErrorMessage(err))
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

  const hasResults = Boolean(response)

  const formatConfidenceLabel = (label) => {
    if (!label) return ''
    return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase()
  }

  const confidence = typeof response?.confidence_score === 'number' ? response.confidence_score : null
  const safeConfidence = confidence === null ? 0 : Math.max(0, Math.min(confidence, 1))
  const claims = Array.isArray(response?.claims) ? response.claims : []

  const controlsDisabled = loading || Boolean(disabledReason)

  return (
    <>
      <div className="section-label">Overview / Project Map</div>

      {disabledReason && (
        <div className="inline-notice inline-notice-muted">
          {disabledReason}
        </div>
      )}

      <div className="quick-buttons">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            className={`quick-btn ${activeQuestion === q ? 'active' : ''}`}
            onClick={() => handleQuickSelect(q)}
            disabled={controlsDisabled}
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
          disabled={controlsDisabled}
        />
        <button
          className="ask-btn"
          onClick={handleAsk}
          disabled={controlsDisabled || !inputValue.trim()}
          style={{ opacity: controlsDisabled || !inputValue.trim() ? 0.5 : 1 }}
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

      {error && (
        <div className="inline-notice inline-notice-error">
          {error}
        </div>
      )}

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

      {hasResults && !loading && (
        <>
          {response?.llm_fallback_used && (
            <div className="inline-notice inline-notice-warning">
              Degraded result: LLM fallback mode was used. Claims may be limited, but evidence remains valid.
            </div>
          )}



          <div className="analysis-header">
            <span className="analysis-title">Analysis</span>
            <div className="analysis-right">
              <div className="overview-tag">{response?.retrieval_mode === 'overview' ? 'Overview' : 'Standard'}</div>
              <span className="claims-tag">{claims.length} claims</span>
            </div>
          </div>

          <div className="cards-area">
            {claims.length === 0 && (
              <div className="card">
                <div className="card-body">
                  No structured claims were returned. Review the evidence panel for grounded chunks.
                </div>
              </div>
            )}

            {claims.map((item, i) => (
              <div key={i} className="card">
                <div className="card-header">
                  <span className="card-title">Finding {i + 1}</span>
                  <span className="project-map-tag">Project Map</span>
                </div>
                <div className="card-body">{item.claim}</div>
                {item.evidence && item.evidence.length > 0 && (
                  <div className="evidence-tags">
                    {item.evidence.map((eId, j) => (
                      <button
                        type="button"
                        key={`${eId}-${j}`}
                        className="ev-tag"
                        onClick={() => onEvidenceSelect?.(eId)}
                      >
                        {eId}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

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
