import { useCallback, useState } from 'react'
import type { ReactNode } from 'react'
import type { Level } from '../api'
import { LEVEL, PatientContext, levelOf, pct } from '../lib/state'

// ---------------------------------------------------------------- current patient
export function PatientProvider({ children }: { children: ReactNode }) {
  const [currentId, setId] = useState<string>(() => {
    try { return localStorage.getItem('sleeptwin.patient') || 'A' } catch { return 'A' }
  })
  const setCurrentId = useCallback((id: string) => {
    setId(id)
    try { localStorage.setItem('sleeptwin.patient', id) } catch { /* storage may be blocked (private mode) */ }
  }, [])
  return <PatientContext.Provider value={{ currentId, setCurrentId }}>{children}</PatientContext.Provider>
}

export function Loading({ label = 'Loading the twin…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-24 text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-accent-600" />
      {label}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const notFound = /404|422|unknown patient|invalid input/i.test(message)
  return (
    <div className="card card-pad mx-auto mt-10 max-w-lg text-center">
      <div className="text-lg font-semibold text-slate-900">{notFound ? 'Patient not found' : 'Could not reach the twin'}</div>
      <p className="mt-2 text-sm text-slate-600">
        {notFound ? 'There is no virtual patient with that ID. Pick one from the Patients list.' :
          <>Is the API running? Start it with <code className="rounded-sm bg-slate-100 px-1">uvicorn api.main:app --port 8000</code>.</>}
      </p>
      <p className="mt-1 text-xs text-slate-400">{message}</p>
      {onRetry && !notFound && <button className="btn-primary mt-4" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="py-16 text-center text-sm text-slate-500">{children}</div>
}

// ---------------------------------------------------------------- risk visuals
export function RiskBadge({ level, size = 'sm' }: { level: Level; size?: 'sm' | 'lg' }) {
  const l = LEVEL[level]
  return (
    <span className={`chip ring-1 ${l.bg} ${l.text} ${l.ring} ${size === 'lg' ? 'px-3 py-1 text-sm' : ''}`}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: l.hex }} />
      {l.label}
    </span>
  )
}

/** Semicircle gauge with a large number in the middle. */
export function Gauge({ value, label, size = 220, sub }: { value: number; label: string; size?: number; sub?: string }) {
  const lv = levelOf(value)
  const r = size / 2 - 14
  const cx = size / 2
  const cy = size / 2
  const arc = (from: number, to: number) => {
    const a0 = Math.PI * (1 - from)
    const a1 = Math.PI * (1 - to)
    const x0 = cx + r * Math.cos(a0)
    const y0 = cy - r * Math.sin(a0)
    const x1 = cx + r * Math.cos(a1)
    const y1 = cy - r * Math.sin(a1)
    return `M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`
  }
  const v = Math.max(0.001, Math.min(0.999, value))
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 12} viewBox={`0 0 ${size} ${size / 2 + 12}`} role="img"
        aria-label={`${label}: ${pct(value)}`}>
        <path d={arc(0, 0.4)} stroke="#d1fae5" strokeWidth={14} fill="none" />
        <path d={arc(0.4, 0.75)} stroke="#fef3c7" strokeWidth={14} fill="none" />
        <path d={arc(0.75, 1)} stroke="#fee2e2" strokeWidth={14} fill="none" />
        <path d={arc(0, v)} stroke={LEVEL[lv].hex} strokeWidth={14} fill="none" strokeLinecap="round" />
        <text x={cx} y={cy - 6} textAnchor="middle" fontSize={size / 5.2} fontWeight={800} fill="#0f172a">
          {Math.round(value * 100)}%
        </text>
      </svg>
      <div className="-mt-1 text-sm font-semibold text-slate-700">{label}</div>
      {sub && <div className="text-xs text-slate-500">{sub}</div>}
    </div>
  )
}

export function SimulatedBadge() {
  return (
    <span className="chip bg-violet-50 text-violet-700 ring-1 ring-violet-200" title="All patients and signals are simulated (synthetic). No real patient data.">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" /></svg>
      Simulated data
    </span>
  )
}

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`flex items-start gap-2 rounded-xl bg-slate-50 text-slate-600 ring-1 ring-slate-200 ${compact ? 'px-3 py-2 text-xs' : 'px-4 py-3 text-sm'}`}>
      <svg className="mt-0.5 shrink-0" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
      <span><b>Model-based projection for clinical decision support. Research prototype.</b> Not a diagnosis; the clinician stays in charge. All data shown is simulated.</span>
    </div>
  )
}

export function Card({ title, children, right, className = '' }: { title?: ReactNode; children: ReactNode; right?: ReactNode; className?: string }) {
  return (
    <section className={`card card-pad ${className}`}>
      {(title || right) && (
        <div className="mb-3 flex items-center justify-between gap-3">
          {title && <h2 className="label">{title}</h2>}
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

export function PageTitle({ title, sub, right }: { title: ReactNode; sub?: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {sub && <p className="mt-1 text-sm text-slate-500">{sub}</p>}
      </div>
      {right}
    </div>
  )
}
