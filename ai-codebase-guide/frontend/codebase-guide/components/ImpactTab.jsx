const IMPACT_FILES = [
  { name: 'routing.py', level: 'High', pct: 92, desc: 'Central routing logic. Changes here affect all API endpoints and method resolution.' },
  { name: 'applications.py', level: 'High', pct: 88, desc: 'Core FastAPI class definition. Modifications impact application initialization.' },
  { name: 'dependencies/utils.py', level: 'Medium', pct: 67, desc: 'Dependency injection resolution. Affects all routes using Depends().' },
  { name: '_compat.py', level: 'Medium', pct: 55, desc: 'Pydantic v1/v2 shims. Changes may break validation across the codebase.' },
  { name: 'encoders.py', level: 'Low', pct: 38, desc: 'JSON serialization. Isolated module, changes are contained to response output.' },
  { name: 'exception_handlers.py', level: 'Low', pct: 30, desc: 'Default exception handlers. Only affects error response format.' },
]

const badgeClass = {
  High: 'badge-high',
  Medium: 'badge-med',
  Low: 'badge-low',
}

export default function ImpactTab() {
  return (
    <>
      <div className="section-label" style={{ paddingTop: '16px' }}>Impact Analysis</div>
      <div className="impact-grid">
        {IMPACT_FILES.map((file) => (
          <div key={file.name} className="impact-card">
            <div className="impact-card-header">
              <span className="impact-card-title">{file.name}</span>
              <span className={`impact-badge ${badgeClass[file.level]}`}>{file.level}</span>
            </div>
            <div className="impact-bar-wrap">
              <div className="impact-bar" style={{ width: `${file.pct}%` }} />
            </div>
            <div className="impact-desc">{file.desc}</div>
          </div>
        ))}
      </div>
    </>
  )
}
