import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { Level } from '../api'
import { Disclaimer, Empty, ErrorState, Loading, PageTitle, RiskBadge } from '../components/ui'
import { LEVEL, pct, useAsync, useCurrentPatient } from '../lib/state'

const FILTERS: { key: 'all' | Level; label: string }[] = [
  { key: 'all', label: 'All' }, { key: 'critical', label: 'Critical' }, { key: 'warning', label: 'Warning' }, { key: 'stable', label: 'Stable' },
]

export default function PatientsPage() {
  const { data, error, loading, reload } = useAsync(() => api.patients(), [])
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState<'all' | Level>('all')
  const nav = useNavigate()
  const { setCurrentId } = useCurrentPatient()

  const counts = useMemo(() => {
    const c = { critical: 0, warning: 0, stable: 0 }
    data?.forEach((p) => { c[p.risk_level] += 1 })
    return c
  }, [data])

  const rows = useMemo(() => {
    if (!data) return []
    const s = q.trim().toLowerCase()
    return data.filter((p) => (filter === 'all' || p.risk_level === filter) &&
      (!s || p.name.toLowerCase().includes(s) || p.id.toLowerCase() === s || p.id.toLowerCase().includes(s) ||
        p.conditions.join(' ').toLowerCase().includes(s)))
  }, [data, q, filter])

  if (loading) return <Loading />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const open = (id: string) => { setCurrentId(id); nav(`/patients/${id}`) }

  return (
    <div>
      <PageTitle title="Patients"
        sub="Sorted by tomorrow's risk (the higher of glucose-spike and morning-BP risk). Most at-risk first." />

      <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {(['critical', 'warning', 'stable'] as Level[]).map((l) => (
          <button key={l} onClick={() => setFilter(filter === l ? 'all' : l)}
            className={`card card-pad flex items-center justify-between text-left transition hover:shadow-md ${filter === l ? 'ring-2 ring-accent-200' : ''}`}>
            <div>
              <div className="label">{LEVEL[l].label}</div>
              <div className="mt-1 text-3xl font-extrabold text-slate-900">{counts[l]}</div>
            </div>
            <span className="h-10 w-10 rounded-full" style={{ background: LEVEL[l].hex, opacity: 0.15 }} />
          </button>
        ))}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="relative w-full max-w-sm">
          <svg className="absolute left-3 top-2.5 text-slate-400" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, ID or condition…"
            className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm outline-hidden focus:border-accent-500 focus:ring-2 focus:ring-accent-100" />
        </div>
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)} className={`tab ${filter === f.key ? 'tab-active' : ''}`}>{f.label}</button>
          ))}
        </div>
        <span className="ml-auto text-sm text-slate-500">{rows.length} of {data?.length} patients</span>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Conditions</th>
                <th className="px-4 py-3 text-right">Glucose spike</th>
                <th className="px-4 py-3 text-right">BP surge</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-center">2-h alert</th>
                <th className="px-4 py-3">Main reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((p) => (
                <tr key={p.id} onClick={() => open(p.id)} className="cursor-pointer hover:bg-accent-50/40">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 font-semibold text-slate-900">
                      {p.name}
                      {p.persona && <span className="chip bg-accent-50 text-accent-700 ring-1 ring-accent-100">Persona {p.persona}</span>}
                    </div>
                    <div className="text-xs text-slate-500">{p.id} · {p.age}{p.sex}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {p.conditions.map((c) => <span key={c} className="chip bg-slate-100 text-slate-700">{c}</span>)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-base font-bold tabular-nums">{pct(p.risk)}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{pct(p.bp_risk)}</td>
                  <td className="px-4 py-3"><RiskBadge level={p.risk_level} /></td>
                  <td className="px-4 py-3 text-center">
                    {p.spike_2h_alert ? (
                      <span title={`Glucose likely to cross 180 mg/dL within 2 h (${pct(p.spike_2h_risk)})`}
                        className="chip bg-red-50 text-red-700 ring-1 ring-red-200">⚠ {pct(p.spike_2h_risk)}</span>
                    ) : <span className="text-slate-300">—</span>}
                  </td>
                  <td className="max-w-xs px-4 py-3 text-slate-600">{p.top_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <Empty>No patients match “{q}”.</Empty>}
        </div>
      </div>
      <div className="mt-5"><Disclaimer compact /></div>
    </div>
  )
}
