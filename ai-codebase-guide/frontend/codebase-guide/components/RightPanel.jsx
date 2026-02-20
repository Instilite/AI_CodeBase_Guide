const EVIDENCE = [
  {
    num: 'E1',
    filePath: 'fastapi/',
    fileHighlight: 'applications.py',
    lines: 'L1–60',
    pct: '77%',
    pctClass: 'pct-high',
    barGradient: 'linear-gradient(90deg,#3dd68c,#3dd68c88)',
    code: `<span class="kw">class</span> <span class="fn">FastAPI</span>(Starlette):<br>&nbsp;&nbsp;<span class="str">"""Main FastAPI application class."""</span><br>&nbsp;&nbsp;<span class="kw">def</span> <span class="fn">__init__</span>(<br>&nbsp;&nbsp;&nbsp;&nbsp;self: AppType,<br>&nbsp;&nbsp;&nbsp;&nbsp;*`,
  },
  {
    num: 'E2',
    filePath: 'fastapi/',
    fileHighlight: 'routing.py',
    lines: 'L84–184',
    pct: '74%',
    pctClass: 'pct-high',
    barGradient: 'linear-gradient(90deg,#3dd68c88,#f5a62388)',
    code: `<span class="kw">def</span> <span class="fn">get_dependant</span>(<br>&nbsp;&nbsp;*, path: str, call: Callable[..., Any]<br>) → Dependant:`,
  },
  {
    num: 'E3',
    filePath: '',
    fileHighlight: 'README.md',
    lines: 'L1–55',
    pct: '70%',
    pctClass: 'pct-high',
    barGradient: 'linear-gradient(90deg,#f5a62388,#f5a62344)',
    code: `<span class="cm"># FastAPI</span><br><br>FastAPI framework, high performance, easy to learn,<br>fast to code, ready for production.`,
  },
  {
    num: 'E4',
    filePath: 'fastapi/',
    fileHighlight: 'dependencies/utils.py',
    lines: 'L1–80',
    pct: '67%',
    pctClass: 'pct-med',
    barGradient: 'linear-gradient(90deg,#f5a62344,#7c6af755)',
    code: `<span class="kw">async def</span> <span class="fn">solve_dependencies</span>(<br>&nbsp;&nbsp;*, request: Request, dependant: Dependant`,
  },
  {
    num: 'E5',
    filePath: 'fastapi/',
    fileHighlight: '_compat.py',
    lines: 'L1–60',
    pct: '63%',
    pctClass: 'pct-med',
    barGradient: 'linear-gradient(90deg,#7c6af755,#7c6af733)',
    code: `<span class="cm"># Pydantic v1 / v2 compatibility shims</span><br><span class="kw">try</span>:`,
  },
  {
    num: 'E6',
    filePath: 'fastapi/',
    fileHighlight: 'encoders.py',
    lines: 'L1–70',
    pct: '60%',
    pctClass: 'pct-low',
    barGradient: 'linear-gradient(90deg,#7c6af733,#7c6af722)',
    code: `<span class="kw">def</span> <span class="fn">jsonable_encoder</span>(<br>&nbsp;&nbsp;obj: Any,<br>&nbsp;&nbsp;include: Optional[IncEx] = None,<br>&nbsp;&nbsp;exclude: Optional[IncEx] = None,`,
  },
  {
    num: 'E7',
    filePath: 'fastapi/',
    fileHighlight: 'exception_handlers.py',
    lines: 'L1–45',
    pct: '58%',
    pctClass: 'pct-low',
    barGradient: 'linear-gradient(90deg,#f5505022,#f5505011)',
    code: `<span class="kw">async def</span> <span class="fn">request_validation_exception_handler</span>(<br>&nbsp;&nbsp;request: Request, exc: RequestValidationError,<br>) → JSONResponse:`,
  },
]

export default function RightPanel() {
  return (
    <div className="right-panel">
      <div className="evidence-header">
        <span className="evidence-label">Evidence</span>
        <span className="chunks-tag">7 chunks</span>
      </div>

      <div className="evidence-list">
        {EVIDENCE.map((ev) => (
          <div key={ev.num} className="ev-card">
            <div className="ev-top-bar" style={{ background: ev.barGradient }} />
            <div className="ev-meta">
              <span className="ev-num">{ev.num}</span>
              <span className="ev-file">
                {ev.filePath}<span>{ev.fileHighlight}</span>
              </span>
              <span className="ev-lines">{ev.lines}</span>
              <span className={`ev-pct ${ev.pctClass}`}>{ev.pct}</span>
            </div>
            <div className="ev-code" dangerouslySetInnerHTML={{ __html: ev.code }} />
          </div>
        ))}
      </div>
    </div>
  )
}
