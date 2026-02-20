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

const ANALYSIS_CARDS = [
  {
    title: 'Purpose',
    body: 'FastAPI is a modern, high-performance web framework for building APIs with Python, based on standard Python type hints. It is designed for speed, ease of use, and automatic OpenAPI documentation generation.',
    evidence: ['E1', 'E3'],
  },
  {
    title: 'Entry Points',
    body: (
      <>
        The main application entry point is <code style={{ color: 'var(--accent2)' }}>fastapi/applications.py</code>{' '}
        which defines the FastAPI class. Users instantiate this class and register routes via decorators such as{' '}
        <code style={{ color: 'var(--accent2)' }}>@app.get()</code> and{' '}
        <code style={{ color: 'var(--accent2)' }}>@app.post()</code>.
      </>
    ),
    evidence: ['E2', 'E5'],
  },
  {
    title: 'Key Modules',
    body: (
      <>
        Core routing is handled in <code style={{ color: 'var(--accent2)' }}>fastapi/routing.py</code>. Dependency
        injection is managed through <code style={{ color: 'var(--accent2)' }}>fastapi/dependencies/utils.py</code>.
        Request validation integrates with Pydantic via{' '}
        <code style={{ color: 'var(--accent2)' }}>fastapi/_compat.py</code>.
      </>
    ),
    evidence: ['E4', 'E6'],
  },
  {
    title: 'Main Flow',
    body: (
      <>
        Requests flow through Starlette's ASGI interface → FastAPI routing → dependency resolution → endpoint execution
        → response serialization via <code style={{ color: 'var(--accent2)' }}>encoders.py</code> → JSON response
        returned to client.
      </>
    ),
    evidence: ['E1', 'E2', 'E4'],
  },
]

export default function AskTab() {
  const [activeQuestion, setActiveQuestion] = useState(QUICK_QUESTIONS[0])
  const [inputValue, setInputValue] = useState(QUICK_QUESTIONS[0])
  const textareaRef = useRef(null)

  const handleQuickSelect = (question) => {
    setActiveQuestion(question)
    setInputValue(question)
    textareaRef.current?.focus()
  }

  const handleInputChange = (e) => {
    setInputValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
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
          rows={1}
          placeholder="What does this project do?"
        />
        <button className="ask-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0e0e12" strokeWidth="2.5">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>

      <div className="confidence-bar-wrap">
        <span className="conf-label">Retrieval Confidence</span>
        <div className="conf-track">
          <div className="conf-fill" />
        </div>
        <span className="conf-val">0.61</span>
        <span className="conf-tag">Medium</span>
      </div>

      <div className="analysis-header">
        <span className="analysis-title">Analysis</span>
        <div className="analysis-right">
          <div className="overview-tag">Overview</div>
          <span className="claims-tag">4 claims</span>
        </div>
      </div>

      <div className="cards-area">
        {ANALYSIS_CARDS.map((card) => (
          <div key={card.title} className="card">
            <div className="card-header">
              <span className="card-title">{card.title}</span>
              <span className="project-map-tag">Project Map</span>
            </div>
            <div className="card-body">{card.body}</div>
            <div className="evidence-tags">
              {card.evidence.map((e) => (
                <span key={e} className="ev-tag">{e}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
