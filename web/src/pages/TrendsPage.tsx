import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Area, Bar, CartesianGrid, Cell, ComposedChart, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from '../api'
import type { TrendDay, Trends } from '../api'
import { Card, Disclaimer, ErrorState, Loading, PageTitle } from '../components/ui'
import { useAsync, useCurrentPatient } from '../lib/state'

const ACCENT = '#2554e8'
const BAND = '#10b981'
const TABS = ['Glucose', 'Sleep', 'Heart', 'Activity & oxygen'] as const
type Tab = (typeof TABS)[number]

export default function TrendsPage() {
  const { id = 'A' } = useParams()
  const { setCurrentId } = useCurrentPatient()
  useEffect(() => setCurrentId(id), [id, setCurrentId])
  const { data, error, loading, reload } = useAsync(() => api.trends(id), [id])
  const p = useAsync(() => api.patient(id), [id])
  const [tab, setTab] = useState<Tab>('Glucose')
  if (loading) return <Loading />
  if (error || !data) return <ErrorState message={error || 'no data'} onRetry={reload} />
  return (
    <div>
      <PageTitle
        title={<>Trends {p.data && <span className="text-slate-400">· {p.data.profile.demographics.name}</span>}</>}
        sub={<>Last 21 days. The <span className="font-semibold text-emerald-600">green band</span> is this person's own normal, learned from days 1–14 (mean ± 1 SD).</>}
        right={<Link to={`/patients/${id}/what-if`} className="btn-primary">Open What-If →</Link>}
      />
      <div className="mb-5 flex flex-wrap gap-1" role="tablist">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} className={`tab ${tab === t ? 'tab-active' : ''}`}>{t}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {tab === 'Glucose' && <>
          <Card title="CGM – last 48 hours" right={<span className="text-xs text-slate-500">target 70–180 mg/dL</span>}><CgmChart t={data} /></Card>
          <Card title="Daily glucose peak vs 180 mg/dL" right={<span className="text-xs text-slate-500">red = spike day · grey = today so far</span>}><PeakChart days={data.days} /></Card>
        </>}
        {tab === 'Sleep' && <>
          <Card title="Sleep duration (hours)"><BandChart days={data.days} k="tst" band="tst_band" unit="h" /></Card>
          <Card title={`Last night's sleep stages (${data.hypnogram.date})`}><Hypnogram t={data} /></Card>
        </>}
        {tab === 'Heart' && <>
          <Card title="HRV (RMSSD, ms) – drops under strain"><BandChart days={data.days} k="hrv" band="hrv_band" unit="ms" /></Card>
          <Card title="Resting heart rate (bpm)"><BandChart days={data.days} k="rhr" band="rhr_band" unit="bpm" /></Card>
        </>}
        {tab === 'Activity & oxygen' && <>
          <Card title="Steps per day"><BandChart days={data.days} k="steps" band="steps_band" unit="" /></Card>
          <Card title="Oxygen dips per hour (ODI) – sleep apnea signal"><BandChart days={data.days} k="odi" band="odi_band" unit="/h" danger={15} /></Card>
        </>}
      </div>
      <MissingNote days={data.days} />
      <div className="mt-5"><Disclaimer compact /></div>
    </div>
  )
}

function MissingNote({ days }: { days: TrendDay[] }) {
  const miss = days.filter((d) => d.missing)
  if (!miss.length) return null
  return <p className="mt-3 text-xs text-slate-500">Gaps = watch not worn ({miss.map((d) => `day ${d.day}`).join(', ')}). The twin treats missing nights as “no information”, not as good sleep.</p>
}

const dayTick = (d: string) => d.slice(5)

function BandChart({ days, k, band, unit, danger }: { days: TrendDay[]; k: keyof TrendDay; band: keyof TrendDay; unit: string; danger?: number }) {
  const data = useMemo(() => days.map((d) => ({ date: d.date, v: d[k] as number | null, band: d[band] as [number, number] })), [days, k, band])
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <XAxis dataKey="date" tickFormatter={dayTick} tick={{ fontSize: 11, fill: '#64748b' }} interval={2} />
        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} domain={['auto', 'auto']} width={48} />
        <ReferenceArea x1={days[0].date} x2={days[13].date} fill="#f8fafc" label={{ value: 'learning personal normal', position: 'insideTop', fontSize: 10, fill: '#94a3b8' }} />
        <Area dataKey="band" stroke="none" fill={BAND} fillOpacity={0.14} isAnimationActive={false} name="Personal normal" />
        {danger != null && <ReferenceLine y={danger} stroke="#ef4444" strokeDasharray="4 4" label={{ value: `${danger}${unit}`, fontSize: 10, fill: '#ef4444', position: 'right' }} />}
        <Line dataKey="v" stroke={ACCENT} strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} name="Value" />
        <Tooltip formatter={(v, name) => name === 'Personal normal' && Array.isArray(v) ? [`${Number(v[0]).toFixed(1)} – ${Number(v[1]).toFixed(1)} ${unit}`, name] : [`${typeof v === 'number' ? (unit === '' ? v.toLocaleString() : v.toFixed(1)) : '—'} ${unit}`, String(name ?? '')]} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function CgmChart({ t }: { t: Trends }) {
  const data = t.cgm_48h.map((p) => ({ t: p.t, g: p.glucose }))
  const ticks = data.filter((p) => p.t.endsWith('T00:00') || p.t.endsWith('T06:00') || p.t.endsWith('T12:00') || p.t.endsWith('T18:00')).map((p) => p.t)
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 10, right: 10, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <ReferenceArea y1={t.cgm_target[0]} y2={t.cgm_target[1]} fill={BAND} fillOpacity={0.1} />
        <ReferenceLine y={180} stroke="#ef4444" strokeDasharray="4 4" />
        <XAxis dataKey="t" ticks={ticks} tickFormatter={(s: string) => `${s.slice(5, 10)} ${s.slice(11)}`} tick={{ fontSize: 11, fill: '#64748b' }} />
        <YAxis domain={[50, 300]} ticks={[70, 100, 140, 180, 250, 300]} allowDataOverflow tick={{ fontSize: 11, fill: '#64748b' }} width={48} />
        <Line dataKey="g" stroke={ACCENT} strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} name="Glucose" />
        <Tooltip labelFormatter={(s) => String(s ?? '').replace('T', ' ')} formatter={(v) => [`${v ?? '—'} mg/dL`, 'Glucose']} />
      </LineChart>
    </ResponsiveContainer>
  )
}

function PeakChart({ days }: { days: TrendDay[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={days} margin={{ top: 10, right: 10, left: -8, bottom: 0 }}>
        <CartesianGrid stroke="#f1f5f9" vertical={false} />
        <XAxis dataKey="date" tickFormatter={dayTick} tick={{ fontSize: 11, fill: '#64748b' }} interval={2} />
        <YAxis domain={[80, 'auto']} tick={{ fontSize: 11, fill: '#64748b' }} width={48} />
        <ReferenceLine y={180} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '180', fontSize: 10, fill: '#ef4444', position: 'right' }} />
        <Bar dataKey="cgm_peak" radius={[4, 4, 0, 0]} isAnimationActive={false} name="Peak">
          {days.map((d) => <Cell key={d.date} fill={d.partial ? '#cbd5e1' : (d.cgm_peak ?? 0) > 180 ? '#ef4444' : ACCENT} />)}
        </Bar>
        <Tooltip content={({ active, payload }) => {
          if (!active || !payload?.length) return null
          const d = payload[0].payload as TrendDay
          return (
            <div className="rounded-lg bg-white px-3 py-2 text-xs shadow-sm ring-1 ring-slate-200">
              <div className="font-semibold">{d.date}{d.partial ? ' (today, until 13:00)' : ''}</div>
              <div>Peak {d.cgm_peak} mg/dL</div>
              <div>Time in range (70–180): {d.tir}%</div>
            </div>
          )
        }} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

const STAGE_Y: Record<string, number> = { Wake: 3, REM: 2, Light: 1, Deep: 0 }
function Hypnogram({ t }: { t: Trends }) {
  const data = t.hypnogram.stages.map((s) => ({ t: s.t, y: STAGE_Y[s.stage], stage: s.stage }))
  const counts = t.hypnogram.stages.reduce<Record<string, number>>((a, s) => ({ ...a, [s.stage]: (a[s.stage] || 0) + 1 }), {})
  const total = t.hypnogram.stages.length
  return (
    <div>
      <ResponsiveContainer width="100%" height={230}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#f1f5f9" vertical={false} />
          <XAxis dataKey="t" interval={Math.max(1, Math.floor(data.length / 7))} tick={{ fontSize: 11, fill: '#64748b' }} />
          <YAxis dataKey="y" domain={[0, 3]} ticks={[0, 1, 2, 3]} tickFormatter={(v: number) => ['Deep', 'Light', 'REM', 'Wake'][v]} tick={{ fontSize: 11, fill: '#64748b' }} width={48} />
          <Line type="stepAfter" dataKey="y" stroke={ACCENT} strokeWidth={2} dot={false} isAnimationActive={false} />
          <Tooltip formatter={(_v, _n, item) => [String((item?.payload as { stage?: string } | undefined)?.stage ?? ''), 'Stage']} />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
        {['Deep', 'Light', 'REM', 'Wake'].map((s) => (
          <span key={s}><b>{s}</b> {Math.round(((counts[s] || 0) / total) * 100)}% · {((counts[s] || 0) * 5)} min</span>
        ))}
      </div>
    </div>
  )
}
