import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { PatientDetail, Reason } from '../api'
import { Card, Disclaimer, ErrorState, Gauge, Loading, RiskBadge } from '../components/ui'
import { pct, useAsync, useCurrentPatient } from '../lib/state'

export default function OverviewPage() {
  const { id = 'A' } = useParams()
  const { setCurrentId } = useCurrentPatient()
  useEffect(() => setCurrentId(id), [id, setCurrentId])
  const { data, error, loading, reload } = useAsync(() => api.patient(id), [id])
  if (loading) return <Loading />
  if (error || !data) return <ErrorState message={error || 'no data'} onRetry={reload} />
  return <Overview d={data} />
}

function Overview({ d }: { d: PatientDetail }) {
  const p = d.profile
  const dem = p.demographics
  const glucoseFirst = d.risk >= d.bp_risk
  const [showGlucoseBaseline, setShowGlucoseBaseline] = useState(false)
  const trends = useAsync(() => api.trends(d.id), [d.id])

  const fastingLab = p.labs.find((l) => l.name.toLowerCase().includes('fasting glucose'))

  const { usualCgmMean, baselinePeakMean } = useMemo(() => {
    const mean = d.baseline_glucose?.usual_mean ?? null
    let peakMean: number | null = null
    if (trends.data?.days?.length) {
      const baseDays = trends.data.days.slice(0, 14).filter((day) => day.cgm_peak != null)
      if (baseDays.length > 0) {
        peakMean = Math.round(baseDays.reduce((acc, cur) => acc + (cur.cgm_peak ?? 0), 0) / baseDays.length)
      }
    }
    return { usualCgmMean: mean, baselinePeakMean: peakMean }
  }, [d.baseline_glucose, trends.data])
  return (
    <div className="space-y-5">
      {/* header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">{dem.name}</h1>
            <RiskBadge level={d.risk_level} size="lg" />
            {d.persona && <span className="chip bg-accent-50 text-accent-700 ring-1 ring-accent-100">Demo persona {d.persona}</span>}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            {d.id} · {dem.age} y · {dem.sex === 'M' ? 'Male' : 'Female'} · BMI {dem.bmi} · {dem.city} (fictional)
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {p.conditions.map((c) => <span key={c} className="chip bg-slate-100 text-slate-700">{c}</span>)}
            <DataQualityChip dq={d.data_quality} />
          </div>
        </div>
        <div className="flex gap-2">
          <Link to={`/patients/${d.id}/trends`} className="btn-ghost">Trends</Link>
          <Link to={`/patients/${d.id}/what-if`} className="btn-primary">Open What-If →</Link>
        </div>
      </div>

      <SpikeBanner d={d} />

      {/* risk + why + signals */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card title="Next-24-hour forecast">
          <div className="flex flex-col items-center gap-2">
            <Gauge value={d.risk} label="Glucose spike > 180 mg/dL" size={230} />
            <div className="mt-2 flex w-full items-center justify-center gap-6 border-t border-slate-100 pt-3">
              <Gauge value={d.bp_risk} label="Morning BP > 145" size={130} />
            </div>
            <p className="text-center text-xs text-slate-500">
              Forecast for {d.forecast_for}, issued after last night's sleep synced. 7-night sleep/HR/HRV window + health record.
            </p>
          </div>
        </Card>

        <Card
          title={showGlucoseBaseline ? 'Normal vs. usual glucose level' : `Why ${glucoseFirst ? 'glucose' : 'BP'} risk is ${d.risk_level === 'stable' ? 'low' : 'high'}`}
          right={
            <button
              type="button"
              onClick={() => setShowGlucoseBaseline((prev) => !prev)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition shadow-2xs"
              aria-expanded={showGlucoseBaseline}
            >
              {showGlucoseBaseline ? 'Show reasons' : 'Normal glucose'}
            </button>
          }
        >
          {showGlucoseBaseline ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg bg-slate-50 p-2.5 ring-1 ring-slate-200/70">
                  <div className="text-[11px] font-medium text-slate-500">Usual Baseline (Days 1–14)</div>
                  <div className="mt-0.5 text-base font-bold text-slate-900">
                    {usualCgmMean ? `${usualCgmMean}` : (fastingLab?.value ? `~${Math.round(fastingLab.value * 0.95)}` : '—')}{' '}
                    <span className="text-[11px] font-normal text-slate-400">mg/dL</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {baselinePeakMean ? `Avg daily peak: ${baselinePeakMean} mg/dL` : 'Personal learned mean'}
                  </div>
                </div>

                <div className="rounded-lg bg-slate-50 p-2.5 ring-1 ring-slate-200/70">
                  <div className="text-[11px] font-medium text-slate-500">Clinical Normal Target</div>
                  <div className="mt-0.5 text-base font-bold text-emerald-700">
                    70–180 <span className="text-[11px] font-normal text-slate-400">mg/dL</span>
                  </div>
                  <div className="text-[10px] text-slate-400">CGM Time-in-Range (TIR) target</div>
                </div>

                <div className="rounded-lg bg-slate-50 p-2.5 ring-1 ring-slate-200/70">
                  <div className="text-[11px] font-medium text-slate-500">Usual Fasting Glucose</div>
                  <div className="mt-0.5 text-base font-bold text-slate-900">
                    {fastingLab?.value ?? '—'} <span className="text-[11px] font-normal text-slate-400">mg/dL</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Prior lab: {fastingLab?.prior ?? '—'} mg/dL (target &lt; 100)
                  </div>
                </div>

                <div className="rounded-lg bg-slate-50 p-2.5 ring-1 ring-slate-200/70">
                  <div className="text-[11px] font-medium text-slate-500">Current Glucose</div>
                  <div className="mt-0.5 text-base font-bold text-slate-900">
                    {d.spike_2h?.current_glucose != null ? d.spike_2h.current_glucose : '—'}{' '}
                    <span className="text-[11px] font-normal text-slate-400">mg/dL</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {d.spike_2h?.trend_mg_dl_per_min != null
                      ? `Trend: ${d.spike_2h.trend_mg_dl_per_min > 0 ? '+' : ''}${(d.spike_2h.trend_mg_dl_per_min * 30).toFixed(0)} mg/dL / 30m`
                      : 'Live CGM sensor reading'}
                  </div>
                </div>
              </div>

              <p className="text-xs text-slate-500 leading-relaxed pt-1">
                SleepTwin evaluates tomorrow’s projection against this patient’s own learned normal ({usualCgmMean ? `${usualCgmMean} mg/dL` : 'personal mean'} ± 1 SD) rather than a generic population threshold.
              </p>
            </div>
          ) : (
            <>
              <ReasonList reasons={glucoseFirst ? d.reasons : d.bp_reasons} />
              <div className="mt-4 border-t border-slate-100 pt-3">
                <div className="label mb-2">{glucoseFirst ? `Morning BP · ${pct(d.bp_risk)}` : `Glucose · ${pct(d.risk)}`}</div>
                <ReasonList reasons={glucoseFirst ? d.bp_reasons : d.reasons} compact />
              </div>
            </>
          )}

          <p className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-400">
            {showGlucoseBaseline
              ? 'Comparing personal learned baseline (days 1–14) against clinical target.'
              : 'From SHAP explanations of the fused model; bar = push on the risk.'}
          </p>
        </Card>

        <Card title="Signals to watch">
          <div className="space-y-3 text-sm">
            {d.masking ? (
              <div className={`rounded-xl p-3 ring-1 ${d.masking.flagged ? 'bg-amber-50 ring-amber-200 text-amber-900' : 'bg-slate-50 ring-slate-200 text-slate-700'}`}>
                <div className="font-semibold">{d.masking.flagged ? 'Hidden strain (beta-blocker masking)' : 'Beta-blocker aware'}</div>
                <div className="mt-1">{d.masking.text}</div>
              </div>
            ) : null}
            {d.apnea_flag && (
              <div className="rounded-xl bg-amber-50 p-3 text-amber-900 ring-1 ring-amber-200">
                <div className="font-semibold">{d.apnea_flag.diagnosed ? 'Sleep apnea active' : 'Possible hidden sleep apnea'}</div>
                <div className="mt-1">{d.apnea_flag.text}</div>
              </div>
            )}
            <SpikeMini d={d} />
            <div className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200">
              <div className="font-semibold text-slate-800">Data quality</div>
              <div className="mt-1 text-slate-600">
                {d.data_quality.missing_nights_7d} missing night(s) in the last 7 · CGM gaps {d.data_quality.cgm_missing_pct_24h}% yesterday
                {d.data_quality.level === 'low' && <div className="mt-1 font-medium text-amber-700">Low data – treat this forecast with extra caution.</div>}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* EHR */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Card 1: Diagnoses & Medications */}
        <Card title="Health record – diagnoses & medications">
          <div className="space-y-4 text-sm">
            <div>
              <div className="mb-1.5 font-bold text-slate-800 text-xs uppercase tracking-wide">Diagnoses</div>
              {p.diagnoses.length === 0 ? <div className="text-slate-500 text-xs">None recorded</div> : (
                <ul className="space-y-1.5">
                  {p.diagnoses.map((x) => {
                    const style = getDiagnosisStyle(x.name)
                    return (
                      <li key={x.name} className="flex items-center justify-between text-xs">
                        <span className="inline-flex items-center gap-2 font-medium text-slate-800">
                          <span className={`h-2 w-2 rounded-full ${style.dot}`} />
                          <span>{x.name}</span>
                        </span>
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                          {x.year ? `since ${x.year}` : 'year unknown'}
                        </span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>

            <div>
              <div className="mb-1.5 font-bold text-slate-800 text-xs uppercase tracking-wide">Medications</div>
              {p.medications.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {p.medications.map((m) => {
                    const chipStyle = getMedicationStyle(m)
                    return (
                      <span key={m} className={`rounded-lg px-2.5 py-1 text-xs font-semibold border shadow-2xs ${chipStyle}`}>
                        {m}
                      </span>
                    )
                  })}
                </div>
              ) : <div className="text-slate-500 text-xs">None</div>}
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
              <span className="text-slate-500">Waist Circumference</span>
              <span className={`rounded-md px-2 py-0.5 font-bold tabular-nums border ${
                dem.waist_cm >= 100
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : 'bg-slate-50 text-slate-700 border-slate-200'
              }`}>
                {dem.waist_cm} cm {dem.waist_cm >= 100 ? '(Elevated)' : ''}
              </span>
            </div>
          </div>
        </Card>

        {/* Card 2: Lab Results (Color-Coded Latest vs Prior) */}
        <Card title="Lab results (latest vs prior)">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-[10.5px] font-bold uppercase tracking-wider text-slate-400">
                <th className="py-1.5 text-left font-bold">Biomarker</th>
                <th className="py-1.5 text-right font-bold">Latest Value</th>
                <th className="w-20 py-1.5 text-right font-bold pr-1">Prior</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {p.labs.map((l) => {
                const evalInfo = getLabEvaluation(l.name, l.value, l.prior)
                return (
                  <tr key={l.name} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-2 text-slate-700 font-medium">{l.name}</td>
                    <td className="py-2 text-right tabular-nums">
                      <span className={`text-[13px] ${evalInfo.valueColor}`}>
                        {l.value}
                      </span>
                      <span className="ml-1 text-[10px] font-normal text-slate-400">{l.unit}</span>
                    </td>
                    <td className="w-20 py-2 text-right tabular-nums text-slate-500 pr-1">
                      <span className="text-slate-500 text-xs">{l.prior}</span>{' '}
                      <span className={`inline-block ml-0.5 text-xs ${evalInfo.deltaColor}`}>
                        {evalInfo.arrow}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="mt-2 text-[11px] text-slate-400">
            Latest {p.labs[0]?.date} · prior {p.labs[0]?.prior_date}
          </div>
        </Card>

        {/* Card 3: Genetic Markers (Color-Coded Risk) */}
        <Card title="Genetic markers" right={<span className="chip bg-violet-50 text-violet-700 ring-1 ring-violet-200">Simulated</span>}>
          <div className="space-y-2.5 text-xs">
            <Marker
              name="T2D polygenic risk score"
              value={`${p.genetic_markers.prs_t2d > 0 ? '+' : ''}${p.genetic_markers.prs_t2d} SD`}
              note={p.genetic_markers.notes.prs_t2d}
              badgeClass={
                p.genetic_markers.prs_t2d >= 1.0
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : p.genetic_markers.prs_t2d <= -1.0
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-50 text-slate-700 border-slate-200'
              }
            />
            <Marker
              name="TCF7L2 rs7903146"
              value={`${p.genetic_markers.tcf7l2_risk_alleles} risk allele${p.genetic_markers.tcf7l2_risk_alleles === 1 ? '' : 's'}`}
              note={p.genetic_markers.notes.tcf7l2_risk_alleles}
              badgeClass={
                p.genetic_markers.tcf7l2_risk_alleles === 2
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : p.genetic_markers.tcf7l2_risk_alleles === 1
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }
            />
            <Marker
              name="MTNR1B rs10830963"
              value={p.genetic_markers.mtnr1b_risk_allele ? 'Carrier' : 'Non-carrier'}
              note={p.genetic_markers.notes.mtnr1b_risk_allele}
              badgeClass={
                p.genetic_markers.mtnr1b_risk_allele
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }
            />
            <p className="pt-1 text-[11px] text-slate-400 leading-snug">
              Simulated from 1000 Genomes South-Asian allele frequencies; small, cited effects. Context, not a headline.
            </p>
          </div>
        </Card>
      </div>

      <Disclaimer />
    </div>
  )
}

function getDiagnosisStyle(name: string) {
  const n = name.toLowerCase()
  if (n.includes('diabetes') || n.includes('glucose')) {
    return { dot: 'bg-rose-500' }
  }
  if (n.includes('hypertension') || n.includes('pressure') || n.includes('bp')) {
    return { dot: 'bg-amber-500' }
  }
  if (n.includes('lipid') || n.includes('cholesterol')) {
    return { dot: 'bg-indigo-500' }
  }
  if (n.includes('apnea') || n.includes('sleep')) {
    return { dot: 'bg-purple-500' }
  }
  return { dot: 'bg-blue-500' }
}

function getMedicationStyle(name: string) {
  const n = name.toLowerCase()
  // Glucose lowering: emerald
  if (
    n.includes('metformin') ||
    n.includes('sulfonylurea') ||
    n.includes('glipizide') ||
    n.includes('glimepiride') ||
    n.includes('sglt') ||
    n.includes('dpp') ||
    n.includes('insulin')
  ) {
    return 'bg-emerald-50 text-emerald-800 border-emerald-200/90'
  }
  // Cardiovascular / BP: amber
  if (
    n.includes('beta-blocker') ||
    n.includes('metoprolol') ||
    n.includes('atenolol') ||
    n.includes('ace inhibitor') ||
    n.includes('lisinopril') ||
    n.includes('arb') ||
    n.includes('losartan') ||
    n.includes('amlodipine')
  ) {
    return 'bg-amber-50 text-amber-800 border-amber-200/90'
  }
  // Lipids: purple
  if (n.includes('statin') || n.includes('atorvastatin') || n.includes('rosuvastatin')) {
    return 'bg-purple-50 text-purple-800 border-purple-200/90'
  }
  return 'bg-blue-50 text-blue-800 border-blue-200/90'
}

function getLabEvaluation(name: string, value: number | null, prior?: number | null) {
  if (value == null) {
    return { status: 'normal', deltaColor: 'text-slate-400', arrow: '→', valueColor: 'text-slate-500' }
  }
  const n = name.toLowerCase()
  let status: 'normal' | 'elevated' | 'high' = 'normal'
  let higherIsBetter = false

  if (n.includes('hba1c')) {
    if (value >= 8.0) status = 'high'
    else if (value >= 5.7) status = 'elevated'
  } else if (n.includes('fasting glucose')) {
    if (value >= 126) status = 'high'
    else if (value >= 100) status = 'elevated'
  } else if (n.includes('ldl')) {
    if (value >= 130) status = 'high'
    else if (value >= 100) status = 'elevated'
  } else if (n.includes('hdl')) {
    higherIsBetter = true
    if (value < 40) status = 'elevated'
  } else if (n.includes('triglycerides')) {
    if (value >= 150) status = 'elevated'
  } else if (n.includes('egfr')) {
    higherIsBetter = true
    if (value < 60) status = 'high'
    else if (value < 90) status = 'elevated'
  } else if (n.includes('sbp')) {
    if (value >= 140) status = 'high'
    else if (value >= 130) status = 'elevated'
  } else if (n.includes('dbp')) {
    if (value >= 90) status = 'high'
    else if (value >= 80) status = 'elevated'
  }

  const delta = prior != null ? value - prior : 0
  let deltaColor = 'text-slate-400'
  let arrow = '→'

  if (Math.abs(delta) > 1e-4) {
    if (higherIsBetter) {
      if (delta > 0) {
        deltaColor = 'text-emerald-600 font-bold'
        arrow = '↑'
      } else {
        deltaColor = 'text-rose-600 font-bold'
        arrow = '↓'
      }
    } else {
      if (delta > 0) {
        deltaColor = 'text-rose-600 font-bold'
        arrow = '↑'
      } else {
        deltaColor = 'text-emerald-600 font-bold'
        arrow = '↓'
      }
    }
  }

  const valueColor =
    status === 'high'
      ? 'text-rose-700 font-extrabold'
      : status === 'elevated'
      ? 'text-amber-700 font-bold'
      : 'text-slate-800 font-semibold'

  return { status, deltaColor, arrow, valueColor }
}

function Marker({
  name,
  value,
  note,
  badgeClass,
}: {
  name: string
  value: string
  note: string
  badgeClass?: string
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-2.5">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800 text-xs">{name}</span>
        <span
          className={`rounded-md px-2 py-0.5 text-xs font-bold tabular-nums border ${
            badgeClass || 'bg-white text-slate-700 border-slate-200'
          }`}
        >
          {value}
        </span>
      </div>
      <div className="mt-1 text-[11px] text-slate-500 leading-snug">{note}</div>
    </div>
  )
}

export function ReasonList({ reasons, compact = false }: { reasons: Reason[]; compact?: boolean }) {
  const max = Math.max(0.3, ...reasons.map((r) => Math.abs(r.impact)))
  if (!reasons.length) return <div className="text-sm text-slate-500">Nothing stands out – within personal normal.</div>
  return (
    <ol className={compact ? 'space-y-1.5' : 'space-y-3'}>
      {reasons.map((r, i) => {
        const up = r.impact > 0 && r.kind !== 'noted'
        const noted = r.kind === 'noted'
        return (
          <li key={i} className="text-sm">
            <div className="flex items-start gap-2">
              {compact && <span className={`text-xs ${noted ? 'text-slate-400' : up ? 'text-red-500' : 'text-emerald-600'}`}>{noted ? '•' : up ? '▲' : '▼'}</span>}
              {!compact && <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${noted ? 'bg-slate-100 text-slate-500' : up ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>{noted ? 'i' : i + 1}</span>}
              <span className={`${compact ? 'text-slate-600' : 'font-medium text-slate-800'} ${r.kind === 'modifier' ? 'italic' : ''}`}>{r.text}</span>
            </div>
            {!compact && !noted && (
              <div className="ml-7 mt-1 h-1.5 rounded-full bg-slate-100">
                <div className="h-1.5 rounded-full" style={{ width: `${(Math.abs(r.impact) / max) * 100}%`, background: up ? '#ef4444' : '#10b981' }} />
              </div>
            )}
          </li>
        )
      })}
    </ol>
  )
}

function DataQualityChip({ dq }: { dq: PatientDetail['data_quality'] }) {
  return dq.level === 'low'
    ? <span className="chip bg-amber-50 text-amber-700 ring-1 ring-amber-200">Low data</span>
    : <span className="chip bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">Data OK</span>
}

function SpikeBanner({ d }: { d: PatientDetail }) {
  const s = d.spike_2h
  if (!s.alert) return null
  return (
    <div className="flex flex-col items-start gap-3 rounded-2xl bg-red-600 px-5 py-4 text-white shadow-xs sm:flex-row sm:items-center sm:gap-4" role="alert">
      <div className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/15 text-2xl sm:flex">⚠</div>
      <div className="min-w-0 flex-1">
        <div className="text-lg font-bold">
          2-hour alert: glucose likely to cross 180 mg/dL{s.minutes_ahead ? ` in ~${s.minutes_ahead} min` : ' within 2 hours'}
        </div>
        <div className="text-sm text-red-50">{s.reasons.join(' · ')}</div>
      </div>
      <div className="sm:text-right">
        <div className="text-3xl font-extrabold">{pct(s.risk)}</div>
        <div className="text-xs text-red-100">as of {s.as_of?.slice(11)} · now {s.current_glucose} mg/dL</div>
      </div>
    </div>
  )
}

function SpikeMini({ d }: { d: PatientDetail }) {
  const s = d.spike_2h
  return (
    <div className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-slate-800">Live CGM (2-hour watch)</span>
        <span className={`font-bold ${s.alert ? 'text-red-600' : 'text-slate-700'}`}>{s.risk == null ? '–' : pct(s.risk)}</span>
      </div>
      <div className="mt-1 text-slate-600">
        {s.current_glucose == null ? 'CGM signal missing right now.' :
          <>Now {s.current_glucose} mg/dL{s.trend_mg_dl_per_min != null && <> · trend {s.trend_mg_dl_per_min > 0 ? '+' : ''}{(s.trend_mg_dl_per_min * 30).toFixed(0)} mg/dL per 30 min</>}</>}
      </div>
      {!s.alert && <div className="mt-1 text-xs text-slate-500">No spike expected in the next 2 hours.</div>}
    </div>
  )
}
