import { api } from '../api'
import type { ModelSummary, TargetResult } from '../api'
import { Card, Disclaimer, ErrorState, Loading, PageTitle } from '../components/ui'
import { useAsync } from '../lib/state'

export default function AboutPage() {
  const { data, error, loading, reload } = useAsync(() => api.summary(), [])
  if (loading) return <Loading />
  if (error || !data) return <ErrorState message={error || 'no data'} onRetry={reload} />
  return <About s={data} />
}

function About({ s }: { s: ModelSummary }) {
  const dc = s.data_card as Record<string, string | number | number[] | Record<string, number>>
  return (
    <div className="space-y-6">
      <PageTitle title="How it works"
        sub="A smartwatch tells you that you slept badly. SleepTwin tells the doctor what that bad sleep will do to this patient's body tomorrow – and what to change tonight to prevent it." />

      {/* 1. two streams */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Card title="Stream 1 · Static health record (simulated EHR)">
          <ul className="space-y-1.5 text-sm text-slate-700">
            <li><b>Demographics</b> – age, sex, BMI, waist</li>
            <li><b>Past diagnoses with years</b> – T2D, prediabetes, hypertension, sleep apnea, dyslipidemia</li>
            <li><b>Labs (latest + prior)</b> – HbA1c, fasting glucose, LDL/HDL, triglycerides, eGFR, clinic BP</li>
            <li><b>Medications</b> – metformin, SGLT2i, sulfonylurea, beta-blocker, ACE inhibitor</li>
            <li><b>Genetic markers (simulated)</b> – T2D polygenic score, TCF7L2 rs7903146, MTNR1B rs10830963</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500">Resampled from real anonymized <b>CDC NHANES 2017–Mar 2020</b> adults so age, BMI, BP, HbA1c, glucose, kidney function and lipids are correlated like real people. Allele frequencies: 1000 Genomes South-Asian (TCF7L2-T 0.299, MTNR1B-G 0.426).</p>
        </Card>
        <Card title="Stream 2 · Dynamic wearable data (simulated)">
          <ul className="space-y-1.5 text-sm text-slate-700">
            <li><b>Sleep stages</b> every 5 min + nightly duration, efficiency, deep/REM %, time awake, bedtime shift</li>
            <li><b>HRV</b> (RMSSD) and <b>resting heart rate</b> every night</li>
            <li><b>Steps</b> per day</li>
            <li><b>Oxygen dips</b> (ODI) at night – sleep-apnea signal</li>
            <li><b>CGM glucose</b> every 5 minutes for all 21 days</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500">Each virtual patient inherits the personal sleep/HR/HRV/step ranges of a real <b>LifeSnaps</b> Fitbit volunteer, adjusted for age, BMI and diabetes. Includes stress episodes, sensor dropout (~5%) and beta-blocker masking.</p>
        </Card>
      </div>

      {/* 2. simulator */}
      <Card title="The simulator – how sleep reaches blood sugar">
        <SimDiagram />
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Formula title="Sleep debt → insulin sensitivity">
{`debt_t = Σ_{k=0..6} max(0, TST_base − TST_{t−k})·0.75^k
SI_t   = SI_0 · exp(−a1·debt − a2·|shift|·(1+g·MTNR1B) − a3·WASO/60)
              · (1 + b1·Δsteps + b2·metformin) · LogNormal(0, σ)
4 nights × 5 h → SI −${Math.round(Number(dc.si_drop_4x5h ?? 0.25) * 100)}%`}
          </Formula>
          <Formula title="Bergman minimal model → CGM">
{`dG/dt = −(p1 + X)·G + p1·Gb + Ra(t)/V
dX/dt = −p2·X + p3·(I − Ib)     SI = p3/p2
I(t)  = Ib + β·max(0, G − Gb)
Ra(t) = 3 meals/day, carbs ~ N(60, 15) g
CGM   = G + N(0, 5), every 5 min`}
          </Formula>
          <Formula title="Morning blood pressure">
{`SBP_morning = SBP_clinic + c1·ODI + c2·debt
            + c3·WASO/60 − c4·ACE-inhibitor
            + home-vs-clinic offset + N(0, 6)
BP event    = SBP_morning > 145`}
          </Formula>
        </div>
      </Card>

      {/* 3. how the twin decides */}
      <Card title="What the twin does every morning">
        <ol className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Learns each person’s normal', 'Days 1–14 set a personal baseline for sleep, HRV, heart rate, oxygen dips, steps and glucose.'],
            ['Spots drift', 'Each night is compared with that person’s own normal (z-scores, weighted sleep debt, bedtime shift).'],
            ['Combines everything', 'A LightGBM model fuses the drift with the health record – the same bad night counts more for a poorly controlled diabetic.'],
            ['Predicts', 'P(tomorrow’s CGM peak > 180 mg/dL) and P(morning SBP > 145). A second model gives a 2-hour spike warning from the live CGM.'],
            ['Explains', 'SHAP values are turned into plain-English reasons (“4 short nights in a row … made worse by high HbA1c”).'],
            ['Tests fixes', 'What-If re-runs the physiology and the models for a different sleep, bedtime or CPAP scenario in milliseconds.'],
          ].map(([t, d], i) => (
            <li key={t} className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200">
              <div className="font-semibold text-slate-900"><span className="mr-1 text-accent-600">{i + 1}.</span>{t}</div>
              <div className="mt-1 text-slate-600">{d}</div>
            </li>
          ))}
        </ol>
      </Card>

      {/* 4. results */}
      {s.nextday && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card title="Does fusing both streams help? (glucose, main)">
            <Ablation r={s.nextday.glucose_event_24h} />
          </Card>
          <Card title="Morning BP surge (secondary)">
            <Ablation r={s.nextday.bp_event} />
          </Card>
        </div>
      )}
      {s.nextday && <p className="-mt-2 text-xs text-slate-500">{s.nextday.n_rows.toLocaleString()} patient-days, {s.nextday.cv}; no patient appears in both training and test. Alert threshold 0.5.</p>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {s.spike_2h && (
          <Card title="2-hour spike alert">
            <div className="grid grid-cols-3 gap-3 text-center">
              <Big v={`${s.spike_2h.median_lead_min} min`} l="median warning lead time" />
              <Big v={s.spike_2h.auroc.toFixed(2)} l={`AUROC (trend arrow alone ${s.spike_2h.trend_only_auroc.toFixed(2)})`} />
              <Big v={`${Math.round(s.spike_2h.episode_recall * 100)}%`} l="of spikes warned in advance" />
            </div>
            <p className="mt-3 text-sm text-slate-600">
              {s.spike_2h.n_samples.toLocaleString()} hourly check-points (CGM &lt; 160 mg/dL). False alerts: {s.spike_2h.false_alerts_per_patient_week.toFixed(2)} per patient-week.
              Lead-time IQR {s.spike_2h.iqr_lead_min[0]}–{s.spike_2h.iqr_lead_min[1]} min. Event rate {(s.spike_2h.event_rate * 100).toFixed(1)}%.
            </p>
          </Card>
        )}
        {s.lifesnaps_validation?.available && (
          <Card title="Real-data check · LifeSnaps (real Fitbit volunteers)">
            <div className="grid grid-cols-3 gap-3 text-center">
              <Big v={`${s.lifesnaps_validation.n_users}`} l={`users · ${s.lifesnaps_validation.n_nights.toLocaleString()} nights`} />
              <Big v={`${(s.lifesnaps_validation.rhr_z_short_mean - s.lifesnaps_validation.rhr_z_normal_mean > 0 ? '+' : '')}${(s.lifesnaps_validation.rhr_z_short_mean - s.lifesnaps_validation.rhr_z_normal_mean).toFixed(2)} SD`} l={`resting HR after short nights (p=${s.lifesnaps_validation.rhr_wilcoxon_p.toPrecision(2)})`} />
              <Big v={`${(s.lifesnaps_validation.hrv_z_short_mean - s.lifesnaps_validation.hrv_z_normal_mean).toFixed(2)} SD`} l={`HRV after short nights (p=${s.lifesnaps_validation.hrv_wilcoxon_p.toPrecision(2)})`} />
            </div>
            <img src="/api/reports/lifesnaps_boxplot.png" alt="Boxplot of resting HR and HRV z-scores after short vs normal nights" className="mt-3 w-full rounded-lg ring-1 ring-slate-200" />
            <p className="mt-2 text-xs text-slate-500">{s.lifesnaps_validation.definition}. Each person is compared with their own normal – the core idea behind the twin.</p>
          </Card>
        )}
      </div>

      {/* 5. data card + limits */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Data card">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-slate-500">Cohort</dt><dd>{String(dc.cohort)}</dd>
            <dt className="text-slate-500">EHR calibration</dt><dd>{String(dc.ehr_calibration)}</dd>
            <dt className="text-slate-500">Wearable calibration</dt><dd>{String(dc.wearable_calibration)}</dd>
            <dt className="text-slate-500">Cohort mix</dt><dd>{mix(dc.cohort_mix as Record<string, number>)}</dd>
            <dt className="text-slate-500">Event rates</dt><dd>glucose {(Number(dc.event_rate_glucose) * 100).toFixed(1)}% · BP {(Number(dc.event_rate_bp) * 100).toFixed(1)}% of patient-days</dd>
            <dt className="text-slate-500">CGM range</dt><dd>{(dc.glucose_range as number[]).map((x) => Math.round(x)).join('–')} mg/dL</dd>
            <dt className="text-slate-500">Missing data</dt><dd>{(Number(dc.missing_nights_pct) * 100).toFixed(1)}% nights · {(Number(dc.cgm_missing_pct) * 100).toFixed(1)}% CGM</dd>
            <dt className="text-slate-500">Sandbox</dt><dd>{String(dc.sandbox)}</dd>
          </dl>
        </Card>
        <Card title="Limits – what it is NOT">
          <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700">
            <li><b>Not a diagnosis tool.</b> It helps a doctor decide; the doctor stays in charge.</li>
            <li><b>Not clinically proven.</b> Trained on realistic virtual patients – it proves the idea works, not that it is ready for hospitals.</li>
            <li><b>Circularity:</b> glucose labels come from the same simulator that encodes the sleep → insulin-sensitivity effect.</li>
            <li>Pooled AUROC is helped by easy healthy-vs-diabetic differences; the T2D-only number is the harder test.</li>
            <li>NHANES is a US population; Indian calibration (e.g. ICMR-INDIAB) is future work. Genetic markers are simulated.</li>
            <li><b>Next step:</b> retrospective validation on real, anonymized CGM + wearable data with ethics approval.</li>
          </ul>
        </Card>
      </div>

      <Card title="Sources">
        <ul className="grid grid-cols-1 gap-x-6 gap-y-1 text-xs text-slate-600 md:grid-cols-2">
          <li>CDC NHANES 2017–March 2020 pre-pandemic (public domain)</li>
          <li>Yfantidou S. et al. LifeSnaps, Sci Data 2022 – Zenodo 7229547 (CC-BY-4.0)</li>
          <li>Bergman RN et al. Am J Physiol 1979; J Clin Invest 1981 – minimal model</li>
          <li>Dalla Man C. et al. IEEE TBME 2007 – glucose distribution volume</li>
          <li>Spiegel K. et al. Lancet 1999 – sleep debt and glucose tolerance</li>
          <li>Buxton OM et al. Diabetes 2010 – sleep restriction lowers insulin sensitivity</li>
          <li>Donga E. et al. JCEM 2010 – one night of short sleep, insulin resistance</li>
          <li>Grant SFA et al. Nat Genet 2006 – TCF7L2; Prokopenko I. et al. Nat Genet 2009 – MTNR1B</li>
          <li>Garaulet M. et al. – MTNR1B × late eating (glucose tolerance)</li>
          <li>1000 Genomes Phase 3 allele frequencies via Ensembl REST</li>
          <li>Inker LA et al. NEJM 2021 – race-free CKD-EPI eGFR</li>
          <li>Synthea (field naming reference) · PhysioNet (optional pattern references)</li>
        </ul>
      </Card>

      <Disclaimer />
    </div>
  )
}

const mix = (m?: Record<string, number>) => m ? Object.entries(m).map(([k, v]) => `${k.replace('_', ' ')} ${(v * 100).toFixed(0)}%`).join(' · ') : '–'

function Big({ v, l }: { v: string; l: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200">
      <div className="text-2xl font-extrabold text-slate-900">{v}</div>
      <div className="mt-0.5 text-xs text-slate-500">{l}</div>
    </div>
  )
}

function Formula({ title, children }: { title: string; children: string }) {
  return (
    <div>
      <div className="mb-1 text-sm font-semibold text-slate-800">{title}</div>
      <pre className="overflow-x-auto rounded-xl bg-slate-900 p-3 text-[11.5px] leading-relaxed text-slate-100">{children}</pre>
    </div>
  )
}

function Ablation({ r }: { r: TargetResult }) {
  const rows: [string, keyof TargetResult][] = [['Health record only', 'ehr_only'], ['Wearables only', 'wearables_only'], ['Fused twin (both)', 'fused']]
  const best = r.fused.auroc
  return (
    <div>
      <table className="w-full text-sm">
        <thead className="text-left text-xs uppercase tracking-wide text-slate-500">
          <tr><th className="py-1">Model</th><th className="py-1 text-right">AUROC</th><th className="py-1 text-right">AUPRC</th><th className="py-1 text-right">False alerts / pt-wk</th></tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map(([name, k]) => {
            const m = r[k] as TargetResult['fused']
            return (
              <tr key={k} className={k === 'fused' ? 'font-semibold' : ''}>
                <td className="py-2">{name}</td>
                <td className="py-2 text-right tabular-nums">
                  <div className="flex items-center justify-end gap-2">
                    <div className="hidden h-1.5 w-24 rounded-full bg-slate-100 sm:block"><div className="h-1.5 rounded-full" style={{ width: `${((m.auroc - 0.5) / 0.5) * 100}%`, background: k === 'fused' ? '#2554e8' : '#94a3b8' }} /></div>
                    {m.auroc.toFixed(3)}
                  </div>
                </td>
                <td className="py-2 text-right tabular-nums">{m.auprc.toFixed(3)}</td>
                <td className="py-2 text-right tabular-nums">{m.false_alerts_per_patient_week.toFixed(2)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {r.t2d_subgroup && <p className="mt-2 text-xs text-slate-500">Within diabetics only (harder): record {r.t2d_subgroup.ehr_only?.toFixed(2)} · wearables {r.t2d_subgroup.wearables_only?.toFixed(2)} · fused {r.t2d_subgroup.fused?.toFixed(2)}{best ? '' : ''}</p>}
      <p className="mt-2 text-sm text-slate-600">{r.interpretation}</p>
    </div>
  )
}

function SimDiagram() {
  const box = (x: number, y: number, w: number, t: string, s: string, fill = '#eef4ff', stroke = '#bfd3fe') => (
    <g>
      <rect x={x} y={y} width={w} height={54} rx={10} fill={fill} stroke={stroke} />
      <text x={x + w / 2} y={y + 23} textAnchor="middle" fontSize="13" fontWeight="700" fill="#0f172a">{t}</text>
      <text x={x + w / 2} y={y + 41} textAnchor="middle" fontSize="11" fill="#475569">{s}</text>
    </g>
  )
  const arrow = (x1: number, y1: number, x2: number, y2: number) => <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#64748b" strokeWidth="1.6" markerEnd="url(#ah)" />
  return (
    <div className="overflow-x-auto">
      <svg viewBox="0 0 980 230" className="min-w-[760px]" role="img" aria-label="Simulator diagram">
        <defs><marker id="ah" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b" /></marker></defs>
        {box(10, 20, 170, 'Nightly sleep', 'TST, bedtime, WASO', '#f8fafc', '#cbd5e1')}
        {box(10, 150, 170, 'Health record', 'BMI, HbA1c, age, genes', '#f8fafc', '#cbd5e1')}
        {box(230, 20, 170, 'Sleep debt', '7-night weighted')}
        {box(450, 85, 170, 'Insulin sensitivity', 'SI_t (−25% @ 4×5 h)')}
        {box(670, 85, 150, 'Bergman model', 'meals → glucose')}
        {box(860, 85, 110, 'CGM', 'every 5 min', '#ecfdf5', '#a7f3d0')}
        {box(450, 165, 170, 'β-cell response', 'TCF7L2, HbA1c')}
        {box(670, 0, 150, 'Morning BP', 'ODI, debt, WASO', '#fff7ed', '#fed7aa')}
        {box(230, 100, 170, 'HRV / resting HR', 'autonomic strain')}
        {arrow(180, 47, 228, 47)}
        {arrow(400, 47, 450, 100)}
        {arrow(180, 177, 450, 120)}
        {arrow(180, 185, 448, 192)}
        {arrow(620, 112, 668, 112)}
        {arrow(620, 192, 680, 140)}
        {arrow(820, 112, 858, 112)}
        {arrow(400, 35, 668, 25)}
        {arrow(100, 74, 228, 120)}
      </svg>
    </div>
  )
}
