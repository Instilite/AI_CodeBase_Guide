'use client'

import { useRef, useState } from 'react'

export default function TopBar({ theme, toggleTheme }) {
  const fileInputRef = useRef(null)
  const [uploadState, setUploadState] = useState('idle')
  const [uploadMessage, setUploadMessage] = useState('')

  const handleUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploadState('uploading')
    setUploadMessage(`Uploading ${files.length} file${files.length > 1 ? 's' : ''}...`)

    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || 'Upload failed')
      }

      setUploadState('success')
      setUploadMessage(`✓ ${result.fileCount} file${result.fileCount > 1 ? 's' : ''} uploaded`)

      // Store sessionId so Ask can reference these files later
      localStorage.setItem('uploadSessionId', result.sessionId)

      setTimeout(() => {
        setUploadState('idle')
        setUploadMessage('')
      }, 3000)

    } catch (error) {
      console.error('Upload error:', error)
      setUploadState('error')
      setUploadMessage(`✗ ${error.message}`)
      setTimeout(() => {
        setUploadState('idle')
        setUploadMessage('')
      }, 3000)
    }

    e.target.value = ''
  }

  const getUploadButtonStyle = () => {
    if (uploadState === 'success') return { borderColor: 'var(--green)', color: 'var(--green)' }
    if (uploadState === 'error')   return { borderColor: '#f55050', color: '#f55050' }
    if (uploadState === 'uploading') return { opacity: 0.6, cursor: 'wait' }
    return {}
  }

  return (
    <header className="topbar">
      <div className="logo-badge">CG</div>
      <span className="topbar-title" style={{ color: '#ffffff' }}>Codebase Guide</span>
      <div className="divider-v" />

      <div className="topbar-actions">
        <button
          className="btn-upload"
          onClick={() => uploadState === 'idle' && fileInputRef.current.click()}
          style={getUploadButtonStyle()}
        >
          {uploadState === 'uploading' ? (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          ) : (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          )}
          {uploadMessage || 'Upload Repo'}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".py,.js,.ts,.tsx,.jsx,.json,.md,.txt,.yaml,.yml,.toml,.cfg,.html,.css"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
        </button>

        <button className="btn-theme" onClick={toggleTheme} title="Toggle light/dark mode">
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </header>
  )
}

