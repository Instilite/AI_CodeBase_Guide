'use client'

import { useRef } from 'react'

export default function TopBar({ theme, toggleTheme }) {
  const fileInputRef = useRef(null)

  const handleUpload = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      // Replace with real upload logic later
      alert(`${files.length} file${files.length > 1 ? 's' : ''} selected`)
    }
  }

  return (
    <header className="topbar">
      <div className="logo-badge">CG</div>
      <span className="topbar-title">Codebase Guide</span>
      <div className="divider-v" />

      <div className="repo-selector">
        <div className="repo-dot" />
        <span>fastapi / fastapi</span>
        <span style={{ color: 'var(--text-dim)' }}>▾</span>
      </div>

      <div className="meta-pills">
        <span className="meta-pill">1,247 chunks</span>
        <span className="meta-pill">83 files</span>
        <span className="meta-pill">text-embedding-3-small</span>
      </div>

      <div className="topbar-actions">
        <button className="btn-upload" onClick={() => fileInputRef.current.click()}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload Repo
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".py,.js,.ts,.tsx,.jsx,.json,.md,.txt,.yaml,.yml,.toml,.cfg"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
        </button>

        <button className="btn-new">New Index</button>

        <button className="btn-theme" onClick={toggleTheme} title="Toggle light/dark mode">
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
      </div>
    </header>
  )
}
