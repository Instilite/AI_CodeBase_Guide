'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import TopBar from '../components/TopBar'
import LeftPanel from '../components/LeftPanel'
import { ApiError, deleteRepo, health, jobStatus, listRepos, uploadZip } from '../lib/api'

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const toErrorMessage = (error, fallback) => {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export default function Page() {
  const [theme, setTheme] = useState('dark')
  const [backendStatus, setBackendStatus] = useState('checking')
  const [repos, setRepos] = useState([])
  const [selectedRepoId, setSelectedRepoId] = useState('')
  const [reposLoading, setReposLoading] = useState(false)
  const [repoError, setRepoError] = useState('')
  const [uploadState, setUploadState] = useState({ status: 'idle', message: '' })
  const [currentJob, setCurrentJob] = useState(null)
  const [globalIndexing, setGlobalIndexing] = useState(false)
  const unmountedRef = useRef(false)

  useEffect(() => {
    return () => {
      unmountedRef.current = true
    }
  }, [])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const applyRepos = useCallback((nextRepos, preferredRepoId = '') => {
    if (unmountedRef.current) return

    setRepos(nextRepos)
    setSelectedRepoId((previous) => {
      if (preferredRepoId && nextRepos.some((repo) => repo.repo_id === preferredRepoId)) {
        return preferredRepoId
      }
      if (previous && nextRepos.some((repo) => repo.repo_id === previous)) {
        return previous
      }
      return nextRepos[0]?.repo_id || ''
    })
  }, [])

  const refreshRepos = useCallback(
    async ({ preferredRepoId = '', retryOnIndexing = true, maxAttempts = 24 } = {}) => {
      let attempt = 0
      let delayMs = 750

      while (!unmountedRef.current) {
        try {
          const repoList = await listRepos()
          setGlobalIndexing(false)
          applyRepos(repoList, preferredRepoId)
          return repoList
        } catch (error) {
          const isRetryableIndexing =
            retryOnIndexing &&
            error instanceof ApiError &&
            error.status === 409 &&
            error.error === 'indexing_in_progress'

          if (!isRetryableIndexing) {
            throw error
          }

          setGlobalIndexing(true)
          attempt += 1
          if (attempt >= maxAttempts) {
            throw new ApiError({
              status: 409,
              error: 'indexing_in_progress',
              message: 'Indexing is still in progress. Please wait and retry.',
            })
          }

          await sleep(delayMs)
          delayMs = Math.min(1500, Math.round(delayMs * 1.25))
        }
      }

      return []
    },
    [applyRepos],
  )

  const checkBackendAndLoadRepos = useCallback(
    async ({ preferredRepoId = '' } = {}) => {
      if (unmountedRef.current) return

      setReposLoading(true)
      setRepoError('')
      setBackendStatus('checking')

      try {
        await health()
        if (unmountedRef.current) return

        setBackendStatus('online')
        await refreshRepos({ preferredRepoId, retryOnIndexing: true })
      } catch (error) {
        if (unmountedRef.current) return

        const isNetworkError = error instanceof ApiError && error.error === 'network_error'
        if (isNetworkError) {
          setBackendStatus('offline')
          applyRepos([], '')
        } else {
          setBackendStatus('online')
        }
        setRepoError(toErrorMessage(error, 'Failed to load repositories.'))
      } finally {
        if (!unmountedRef.current) {
          setReposLoading(false)
        }
      }
    },
    [applyRepos, refreshRepos],
  )

  useEffect(() => {
    checkBackendAndLoadRepos()
  }, [checkBackendAndLoadRepos])

  const pollJobUntilDone = useCallback(async (jobId) => {
    let delayMs = 750

    while (!unmountedRef.current) {
      const status = await jobStatus(jobId)
      setCurrentJob(status)

      if (status.status === 'complete' || status.status === 'failed') {
        return status
      }

      await sleep(delayMs)
      delayMs = Math.min(1500, Math.round(delayMs * 1.2))
    }

    return null
  }, [])

  const handleUpload = useCallback(
    async (file) => {
      if (!file || unmountedRef.current) return

      setRepoError('')
      setUploadState({ status: 'uploading', message: `Uploading ${file.name}...` })

      try {
        const upload = await uploadZip(file)
        if (unmountedRef.current) return

        setCurrentJob({
          job_id: upload.job_id,
          repo_id: upload.repo_id,
          status: 'indexing',
          chunk_count: 0,
          error: null,
        })
        setSelectedRepoId(upload.repo_id)
        setUploadState({ status: 'indexing', message: `Indexing ${upload.repo_id}...` })

        const finalStatus = await pollJobUntilDone(upload.job_id)
        if (!finalStatus || unmountedRef.current) return

        if (finalStatus.status === 'complete') {
          setUploadState({
            status: 'success',
            message: `Indexing complete: ${finalStatus.repo_id} (${finalStatus.chunk_count} chunks).`,
          })

          setReposLoading(true)
          try {
            await refreshRepos({ preferredRepoId: finalStatus.repo_id, retryOnIndexing: true, maxAttempts: 30 })
          } finally {
            if (!unmountedRef.current) {
              setReposLoading(false)
            }
          }

          setTimeout(() => {
            if (!unmountedRef.current) {
              setUploadState((current) => (current.status === 'success' ? { status: 'idle', message: '' } : current))
            }
          }, 3500)
        } else {
          setUploadState({
            status: 'error',
            message: finalStatus.error ? `Indexing failed: ${finalStatus.error}` : 'Indexing failed.',
          })
        }
      } catch (error) {
        if (unmountedRef.current) return
        setUploadState({
          status: 'error',
          message: toErrorMessage(error, 'Upload failed.'),
        })
      }
    },
    [pollJobUntilDone, refreshRepos],
  )

  const handleDeleteRepo = useCallback(
    async (repoId) => {
      if (!repoId || unmountedRef.current) return

      try {
        await deleteRepo(repoId)
        if (unmountedRef.current) return

        if (currentJob?.repo_id === repoId) {
          setCurrentJob(null)
          setUploadState({ status: 'idle', message: '' })
        }

        setReposLoading(true)
        try {
          await refreshRepos({ retryOnIndexing: true })
        } finally {
          if (!unmountedRef.current) {
            setReposLoading(false)
          }
        }
      } catch (error) {
        if (unmountedRef.current) return
        setRepoError(toErrorMessage(error, 'Failed to delete repository.'))
      }
    },
    [currentJob, refreshRepos],
  )

  const indexingActive = currentJob?.status === 'indexing' || globalIndexing

  const disabledReason = useMemo(() => {
    if (backendStatus !== 'online') {
      return 'Backend offline. Start FastAPI at http://localhost:8000.'
    }

    if (indexingActive) {
      if (currentJob?.repo_id) {
        return `Indexing in progress for ${currentJob.repo_id}. Ask and Impact are disabled until indexing completes.`
      }
      return 'Indexing in progress. Ask and Impact are disabled until indexing completes.'
    }

    if (!selectedRepoId) {
      return 'Upload a repo ZIP or select an indexed repo to continue.'
    }

    return ''
  }, [backendStatus, currentJob?.repo_id, indexingActive, selectedRepoId])

  return (
    <div className="app" data-theme={theme}>
      <TopBar
        theme={theme}
        toggleTheme={toggleTheme}
        backendStatus={backendStatus}
        repos={repos}
        selectedRepoId={selectedRepoId}
        onSelectRepo={setSelectedRepoId}
        onUpload={handleUpload}
        uploadState={uploadState}
        currentJob={currentJob}
        reposLoading={reposLoading}
        onDeleteRepo={handleDeleteRepo}
        onRefreshRepos={checkBackendAndLoadRepos}
      />
      {repoError && (
        <div className="global-notice global-notice-error">{repoError}</div>
      )}
      <div className="main-layout">
        <LeftPanel
          selectedRepoId={selectedRepoId}
          disabledReason={disabledReason}
        />
      </div>
    </div>
  )
}
