'use client'

import { useMemo, useRef } from 'react'

export default function TopBar({
  theme,
  toggleTheme,
  backendStatus,
  repos,
  selectedRepoId,
  onSelectRepo,
  onUpload,
  uploadState,
  currentJob,
  reposLoading,
  onDeleteRepo,
  onRefreshRepos,
}) {
  const fileInputRef = useRef(null)

  const healthLabel = useMemo(() => {
    if (backendStatus === 'online') return 'Backend Online'
    if (backendStatus === 'offline') return 'Backend Offline'
    return 'Checking Backend'
  }, [backendStatus])

  const uploadLabel = useMemo(() => {
    if (uploadState.status === 'uploading') return 'Uploading...'
    if (uploadState.status === 'indexing') return 'Indexing...'
    return 'Upload Repo'
  }, [uploadState.status])

  const chunkProgress = currentJob?.status === 'indexing'
    ? `${currentJob.chunk_count || 0} chunks`
    : null

  const uploadDisabled = uploadState.status === 'uploading' || uploadState.status === 'indexing'
  const canDelete = Boolean(selectedRepoId) && !uploadDisabled
  const repoSelectorDisabled = backendStatus !== 'online' || reposLoading || repos.length === 0

  const handleUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    await onUpload(files[0])
    e.target.value = ''
  }

  const handleDelete = async () => {
    if (!selectedRepoId || !canDelete) return
    const confirmed = window.confirm(`Delete repo "${selectedRepoId}"?`)
    if (!confirmed) return
    await onDeleteRepo(selectedRepoId)
  }

  const handleRefreshClick = async () => {
    await onRefreshRepos({ preferredRepoId: selectedRepoId })
  }

  const getUploadButtonStyle = () => {
    if (uploadState.status === 'success') return { borderColor: 'var(--green)', color: 'var(--green)' }
    if (uploadState.status === 'error') return { borderColor: '#f55050', color: '#f55050' }
    if (uploadDisabled) return { opacity: 0.7, cursor: 'wait' }
    return {}
  }

  const healthClass =
    backendStatus === 'online' ? 'health-pill health-pill-online'
      : backendStatus === 'offline' ? 'health-pill health-pill-offline'
        : 'health-pill'

  const showSpinner = uploadState.status === 'uploading' || uploadState.status === 'indexing'
  const statusMessage = uploadState.message || (reposLoading ? 'Refreshing repos...' : '')

  return (
    <header className="topbar">
      <div className="logo-badge">CG</div>
      <span className="topbar-title">Codebase Guide</span>
      <div className="divider-v" />

      <div className={healthClass}>
        <span className="repo-dot" />
        <span>{healthLabel}</span>
      </div>

      <button
        className="btn-inline"
        onClick={handleRefreshClick}
        disabled={reposLoading}
      >
        Refresh
      </button>

      <select
        className="repo-select"
        value={selectedRepoId}
        onChange={(e) => onSelectRepo(e.target.value)}
        disabled={repoSelectorDisabled}
      >
        {repos.length === 0 && <option value="">No repos indexed</option>}
        {repos.map((repo) => (
          <option key={repo.repo_id} value={repo.repo_id}>
            {repo.repo_id} ({repo.chunk_count} chunks)
          </option>
        ))}
      </select>

      <div className="topbar-actions">
        <button
          className="btn-upload"
          onClick={() => !uploadDisabled && fileInputRef.current?.click()}
          style={getUploadButtonStyle()}
          disabled={uploadDisabled}
        >
          {showSpinner ? (
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
          {uploadLabel}
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
        </button>

        <button
          className="btn-delete"
          onClick={handleDelete}
          disabled={!canDelete}
          title={canDelete ? 'Delete selected repo' : 'Select a repo to delete'}
        >
          Delete Repo
        </button>

        <button className="btn-theme" onClick={toggleTheme} title="Toggle light/dark mode">
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
      </div>

      {statusMessage && (
        <div className="topbar-status">
          <span>{statusMessage}</span>
          {chunkProgress && <span className="status-chunk">{chunkProgress}</span>}
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </header>
  )
}
