import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import type { PatientDetail, WhatIfInput, WhatIfResult } from '../api'
import { Card, Disclaimer, ErrorState, Gauge, Loading, PageTitle, RiskBadge } from '../components/ui'
import { LEVEL, pct, useAsync, useCurrentPatient } from '../lib/state'
import { ReasonList } from './OverviewPage'

const q = (x: number | null | undefined, step = 0.25) => Math.round((x ?? 0) / step) * step

export default function WhatIfPage() {
  const { id = 'A' } = useParams()
  const { setCurrentId } = useCurrentPatient()
  useEffect(() => setCurrentId(id), [id, setCurrentId])
  const p = useAsync(() => api.patient(id), [id])
  if (p.loading) return <Loading />
  if (p.error || !p.data) return <ErrorState message={p.error || 'no data'} onRetry={p.reload} />
  return <WhatIf key={id} patient={p.data} />
}

function WhatIf({ patient }: { patient: PatientDetail }) {
  const id = patient.id
  const [initial, setInitial] = useState<WhatIfInput | null>(null)
  const [inp, setInp] = useState<WhatIfInput | null>(null)
  const [res, setRes] = useState<WhatIfResult | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [resolvedKey, setResolvedKey] = useState<string | null>(null)
  const seq = useRef(0)
  const [params] = useSearchParams()

  // first call: discover the actual last night so sliders start at "what really happened"
  useEffect(() => {
    api.whatIf(id, { sleep_hours: 7.5, bedtime_shift_h: 0, cpap: false, nights: 1 })
      .then((r) => {
        const start = {
          sleep_hours: Math.min(10, Math.max(3, q(r.current_night.sleep_hours ?? r.current_night.usual_sleep_hours ?? 7))),
          bedtime_shift_h: Math.min(4, Math.max(-2, q(r.current_night.bedtime_shift_h ?? 0))),
          cpap: false, nights: 1,
        }
        setInitial(start)
        // optional demo presets, e.g. /patients/A/what-if?sleep=7.5&shift=0&cpap=1&nights=2
        const num = (k: string) => (params.get(k) != null && !Number.isNaN(Number(params.get(k))) ? Number(params.get(k)) : undefined)
        setInp({
          sleep_hours: Math.min(10, Math.max(3, num('sleep') ?? start.sleep_hours)),
          bedtime_shift_h: Math.min(4, Math.max(-2, num('shift') ?? start.bedtime_shift_h)),
          cpap: params.get('cpap') === '1' || start.cpap,
          nights: Math.min(4, Math.max(1, Math.round(num('nights') ?? 1))),
        })
      })
      .catch((e: Error) => setErr(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    if (!inp) return
    const my = ++seq.current
    const key = JSON.stringify(inp)
    const h = setTimeout(() => {
      api.whatIf(id, inp)
        .then((r) => { if (my === seq.current) { setRes(r); setErr(null) } })
        .catch((e: Error) => my === seq.current && setErr(e.message))
        .finally(() => { if (my === seq.current) setResolvedKey(key) })
    }, 180)
    return () => clearTimeout(h)
  }, [id, inp])

  const busy = inp != null && JSON.stringify(inp) !== resolvedKey

  if (err && !res) return <ErrorState message={err} />
  if (!inp || !initial) return <Loading label="Loading the patient's last night…" />

  const set = (patch: Partial<WhatIfInput>) => setInp({ ...inp, ...patch })
  const usual = res?.current_night.usual_sleep_hours
  const hasApneaSignal = (res?.current_night.odi ?? 0) >= 10

  return (
    <div className="space-y-5">
      <PageTitle
        title={<>What-If <span className="text-slate-400">· {patient.profile.demographics.name}</span></>}
        sub="Test a change before applying it. The twin re-calculates insulin sensitivity, re-runs tomorrow's glucose curve and re-scores the risk models."
        right={<Link to={`/patients/${id}`} className="btn-ghost">← Overview</Link>}
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* controls */}
        <Card title="Scenario for tonight">
          <div className="space-y-6">
            <Slider label="Sleep duration" value={inp.sleep_hours} min={3} max={10} step={0.25}
              fmt={(v) => `${v.toFixed(2).replace(/\.?0+$/, '')} h`} onChange={(v) => set({ sleep_hours: v })}
              hint={usual ? `Usual for this person: ${usual} h · last night: ${initial.sleep_hours} h` : undefined} />
            <Slider label="Bedtime vs usual" value={inp.bedtime_shift_h} min={-2} max={4} step={0.25}
              fmt={(v) => (v === 0 ? 'usual time' : `${v > 0 ? '+' : ''}${v} h ${v > 0 ? 'later' : 'earlier'}`)}
              onChange={(v) => set({ bedtime_shift_h: v })} hint={`Last night: ${initial.bedtime_shift_h > 0 ? '+' : ''}${initial.bedtime_shift_h} h`} />
            <label className="flex cursor-pointer items-center justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-slate-800">CPAP for sleep apnea</div>
                <div className="text-xs text-slate-500">Oxygen dips × 0.2, time awake × 0.6{hasApneaSignal ? ' · this patient has frequent dips' : ''}</div>
              </div>
              <button type="button" role="switch" aria-checked={inp.cpap} onClick={() => set({ cpap: !inp.cpap })}
                className={`relative h-7 w-12 shrink-0 rounded-full transition ${inp.cpap ? 'bg-accent-600' : 'bg-slate-300'}`}>
                <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition ${inp.cpap ? 'left-6' : 'left-1'}`} />
              </button>
            </label>
            <div>
              <div className="mb-1 text-sm font-semibold text-slate-800">Nights covered</div>
              <div className="flex gap-1">
                {[1, 2, 3, 4].map((n) => (
                  <button key={n} onClick={() => set({ nights: n })} className={`tab flex-1 ${inp.nights === n ? 'tab-active' : 'bg-slate-50'}`}>{n === 1 ? 'Tonight' : `${n} nights`}</button>
                ))}
              </div>
              <div className="mt-1 text-xs text-slate-500">Apply the scenario to the most recent night only, or to a short recovery run.</div>
            </div>
            <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
              <button className="btn-ghost" onClick={() => setInp(initial)}>Reset</button>
              <button className="btn-ghost" onClick={() => set({ sleep_hours: 7.5, bedtime_shift_h: 0 })}>7.5 h, usual bedtime</button>
              {hasApneaSignal && <button className="btn-ghost" onClick={() => set({ cpap: true })}>Try CPAP</button>}
            </div>
          </div>
        </Card>

        {/* before -> after */}
        <Card title="Before → after" right={busy ? <span className="text-xs text-slate-400">updating…</span> : res ? <span className="text-xs text-slate-400">{res.compute_ms} ms</span> : null}>
          {res ? (() => {
            const bpLed = res.bp_before > res.risk_before
            return (
            <div className="space-y-4">
              <div className="flex items-center justify-around">
                <Gauge value={bpLed ? res.bp_before : res.risk_before} label="Before" size={150} />
                <span className="text-2xl text-slate-300">→</span>
                <Gauge value={bpLed ? res.bp_after : res.risk_after} label="After" size={150} />
              </div>
              <div className="text-center text-sm text-slate-600">{bpLed ? 'Morning blood pressure > 145 mmHg' : 'Glucose spike > 180 mg/dL, next 24 h'}</div>
              <div className="grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-sm">
                {bpLed
                  ? <Stat label="Glucose spike > 180" before={res.risk_before} after={res.risk_after} />
                  : <Stat label="Morning BP > 145" before={res.bp_before} after={res.bp_after} />}
                <div>
                  <div className="label">Overall status</div>
                  <div className="mt-1 flex items-center gap-1.5"><RiskBadge level={res.level_before} /> → <RiskBadge level={res.level_after} /></div>
                </div>
                <div>
                  <div className="label">Insulin sensitivity</div>
                  <div className={`mt-1 text-lg font-bold ${res.si_change_pct >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{res.si_change_pct > 0 ? '+' : ''}{res.si_change_pct}%</div>
                </div>
                <div>
                  <div className="label">Tomorrow's peak</div>
                  <div className="mt-1 text-lg font-bold">{res.peak_before} → <span style={{ color: res.peak_after > 180 ? LEVEL.critical.hex : ACCENT }}>{res.peak_after}</span> <span className="text-xs font-normal text-slate-400">mg/dL</span></div>
                </div>
              </div>
            </div>
            )
          })() : <Loading label="Running the twin…" />}
        </Card>

        <Card title="Why, after the change">
          {res && <>
            <ReasonList reasons={res.reasons_after} />
            <div className="mt-4 border-t border-slate-100 pt-3">
              <div className="label mb-2">Morning BP</div>
              <ReasonList reasons={res.bp_reasons_after} compact />
            </div>
          </>}
        </Card>
      </div>

      <Card title="Tomorrow's glucose curve (forecast)" right={<span className="text-xs text-slate-500">grey = as things stand · blue = with the scenario · typical meals</span>}>
        {res && <Curve res={res} />}
      </Card>
      <Disclaimer />
    </div>
  )
}

const ACCENT = '#2554e8'

function Stat({ label, before, after }: { label: string; before: number; after: number }) {
  const better = after < before - 0.005
  return (
    <div>
      <div className="label">{label}</div>
      <div className="mt-1 text-lg font-bold">{pct(before)} → <span className={better ? 'text-emerald-600' : after > before + 0.005 ? 'text-red-600' : ''}>{pct(after)}</span></div>
    </div>
  )
}

function Slider({ label, value, min, max, step, fmt, onChange, hint }: {
  label: string; value: number; min: number; max: number; step: number; fmt: (v: number) => string; onChange: (v: number) => void; hint?: string
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-slate-800">{label}</span>
        <span className="text-lg font-bold text-accent-700 tabular-nums">{fmt(value)}</span>
      </div>
      <input type="range" className="mt-2 w-full" min={min} max={max} step={step} value={value} aria-label={label}
        onChange={(e) => onChange(parseFloat(e.target.value))} />
      {hint && <div className="text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

function Curve({ res }: { res: WhatIfResult }) {
  const data = useMemo(() => res.glucose_before.map((g, i) => {
    const m = i * 5
    return { t: `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`, before: g, after: res.glucose_after[i] }
  }), [res])
  const max = Math.max(200, ...res.glucose_before, ...res.glucose_after)
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 10, right: 16, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <ReferenceArea y1={70} y2={180} fill="#10b981" fillOpacity={0.08} />
        <ReferenceLine y={180} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '180 mg/dL', fontSize: 10, fill: '#ef4444', position: 'insideTopRight' }} />
        <XAxis dataKey="t" interval={35} tick={{ fontSize: 11, fill: '#64748b' }} />
        <YAxis domain={[60, Math.ceil(max / 20) * 20]} tick={{ fontSize: 11, fill: '#64748b' }} width={48} />
        <Line dataKey="before" name="As things stand" stroke="#94a3b8" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line dataKey="after" name="With scenario" stroke={ACCENT} strokeWidth={2.5} dot={false} isAnimationActive={false} />
        <Legend verticalAlign="top" height={28} iconType="plainline" />
        <Tooltip formatter={(v, n) => [`${Number(v).toFixed(0)} mg/dL`, String(n ?? '')]} />
      </LineChart>
    </ResponsiveContainer>
  )
}
