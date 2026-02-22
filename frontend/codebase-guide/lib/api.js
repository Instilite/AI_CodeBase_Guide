const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

const DEFAULT_NETWORK_MESSAGE =
  'Cannot reach backend at http://localhost:8000. Start the backend server and retry.'

const isObject = (value) => typeof value === 'object' && value !== null && !Array.isArray(value)
const asString = (value, fallback = '') => (typeof value === 'string' ? value : fallback)
const asNumber = (value, fallback = 0) => (typeof value === 'number' && Number.isFinite(value) ? value : fallback)
const asBoolean = (value, fallback = false) => (typeof value === 'boolean' ? value : fallback)
const asArray = (value) => (Array.isArray(value) ? value : [])

export class ApiError extends Error {
  constructor({ status, error, message, repo_id = null, details = null }) {
    super(message || 'Request failed.')
    this.name = 'ApiError'
    this.status = typeof status === 'number' ? status : 0
    this.error = asString(error, 'internal_error')
    this.repo_id = typeof repo_id === 'string' ? repo_id : null
    this.details = isObject(details) ? details : null
  }
}

const parseJsonSafe = async (response) => {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

const toApiError = (response, payload) => {
  if (isObject(payload)) {
    return new ApiError({
      status: response.status,
      error: asString(payload.error, 'internal_error'),
      message: asString(payload.message, `Request failed with status ${response.status}.`),
      repo_id: payload.repo_id,
      details: payload.details,
    })
  }

  return new ApiError({
    status: response.status,
    error: 'internal_error',
    message: `Request failed with status ${response.status}.`,
  })
}

const request = async (path, options = {}) => {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new ApiError({
      status: 0,
      error: 'network_error',
      message: DEFAULT_NETWORK_MESSAGE,
    })
  }

  const payload = await parseJsonSafe(response)

  if (!response.ok) {
    throw toApiError(response, payload)
  }

  return payload
}

const normalizeChunk = (chunk, index) => {
  if (!isObject(chunk)) {
    return {
      evidence_id: `E${index + 1}`,
      file_path: '',
      start_line: 0,
      end_line: 0,
      text: '',
      similarity: null,
      source: 'vector',
    }
  }

  const source = chunk.source === 'grep' ? 'grep' : 'vector'
  const rawSimilarity = chunk.similarity
  const similarity = typeof rawSimilarity === 'number' && Number.isFinite(rawSimilarity) ? rawSimilarity : null

  return {
    evidence_id: asString(chunk.evidence_id, `E${index + 1}`),
    file_path: asString(chunk.file_path),
    start_line: asNumber(chunk.start_line),
    end_line: asNumber(chunk.end_line),
    text: asString(chunk.text),
    similarity,
    source,
  }
}

const normalizeClaims = (claims) =>
  asArray(claims).map((claim) => ({
    claim: isObject(claim) ? asString(claim.claim) : '',
    evidence: isObject(claim) ? asArray(claim.evidence).map((id) => asString(id)).filter(Boolean) : [],
  }))

const normalizeRepos = (payload) => {
  if (!Array.isArray(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /repos response.',
    })
  }

  return payload
    .filter((repo) => isObject(repo))
    .map((repo) => ({
      repo_id: asString(repo.repo_id),
      name: asString(repo.name),
      chunk_count: asNumber(repo.chunk_count),
      indexed_at: asString(repo.indexed_at),
    }))
    .filter((repo) => repo.repo_id.length > 0)
}

const normalizeAskResponse = (payload) => {
  if (!isObject(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /ask response.',
    })
  }

  const confidenceScore = asNumber(payload.confidence_score)
  const confidenceLabel = ['High', 'Medium', 'Low'].includes(payload.confidence_label)
    ? payload.confidence_label
    : confidenceScore >= 0.55
      ? 'High'
      : confidenceScore >= 0.35
        ? 'Medium'
        : 'Low'

  return {
    repo_id: asString(payload.repo_id),
    retrieval_mode: payload.retrieval_mode === 'overview' ? 'overview' : 'standard',
    confidence_score: confidenceScore,
    confidence_label: confidenceLabel,
    claims: normalizeClaims(payload.claims),
    chunks: asArray(payload.chunks).map((chunk, index) => normalizeChunk(chunk, index)),
    llm_fallback_used: asBoolean(payload.llm_fallback_used),
  }
}

const normalizeImpactResponse = (payload) => {
  if (!isObject(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /impact response.',
    })
  }

  const riskLevel = ['Low', 'Medium', 'High'].includes(payload.risk_level) ? payload.risk_level : 'Low'
  const message = typeof payload.message === 'string' && payload.message.length > 0 ? payload.message : null

  return {
    repo_id: asString(payload.repo_id),
    function_name: asString(payload.function_name),
    risk_level: riskLevel,
    file_count: asNumber(payload.file_count),
    files_referencing: asArray(payload.files_referencing).map((file) => asString(file)).filter(Boolean),
    what_it_does: asString(payload.what_it_does),
    message,
    chunks: asArray(payload.chunks).map((chunk, index) => normalizeChunk(chunk, index)),
    llm_fallback_used: asBoolean(payload.llm_fallback_used),
  }
}

export const apiBase = API_BASE

export const health = async () => {
  const payload = await request('/health')
  if (!isObject(payload) || payload.status !== 'ok') {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /health response.',
    })
  }
  return { status: 'ok' }
}

export const listRepos = async () => {
  const payload = await request('/repos')
  return normalizeRepos(payload)
}

export const uploadZip = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const payload = await request('/upload', {
    method: 'POST',
    body: formData,
  })

  if (!isObject(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /upload response.',
    })
  }

  return {
    job_id: asString(payload.job_id),
    repo_id: asString(payload.repo_id),
    status: payload.status === 'indexing' ? 'indexing' : 'indexing',
  }
}

export const jobStatus = async (jobId) => {
  const payload = await request(`/status/${encodeURIComponent(jobId)}`)
  if (!isObject(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed /status response.',
    })
  }

  const status = ['indexing', 'complete', 'failed'].includes(payload.status) ? payload.status : 'failed'

  return {
    job_id: asString(payload.job_id),
    repo_id: asString(payload.repo_id),
    status,
    chunk_count: asNumber(payload.chunk_count),
    error: typeof payload.error === 'string' && payload.error.length > 0 ? payload.error : null,
  }
}

export const ask = async (repoId, question) => {
  const payload = await request('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_id: repoId,
      question,
      mode: 'auto',
    }),
  })

  return normalizeAskResponse(payload)
}

export const impact = async (repoId, functionName) => {
  const payload = await request('/impact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_id: repoId,
      function_name: functionName,
    }),
  })

  return normalizeImpactResponse(payload)
}

export const deleteRepo = async (repoId) => {
  const payload = await request(`/repos/${encodeURIComponent(repoId)}`, {
    method: 'DELETE',
  })

  if (!isObject(payload)) {
    throw new ApiError({
      status: 500,
      error: 'internal_error',
      message: 'Malformed delete response.',
    })
  }

  return {
    deleted: asBoolean(payload.deleted),
    repo_id: asString(payload.repo_id),
  }
}
