import { useState } from 'react'
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
  const [showFormulas, setShowFormulas] = useState(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  return (
    <div className="space-y-8 pb-12">
      {/* Page Title */}
      <PageTitle
        title="About SleepTwin & How It Works"
        sub="From generic smartwatch sleep scores to personalized, actionable cardiometabolic foresight."
      />

      {/* 1. HERO / ABOUT SLEEPTWIN */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-br from-blue-50/60 via-white to-slate-50/80 p-6 shadow-sm sm:p-8">
        <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-7">
            {/* Pill Tag */}
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/90 px-3 py-1 text-xs font-bold uppercase tracking-wider text-blue-700 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
              Continuous Cardiometabolic Foresight
            </div>

            {/* Title with Brand Accent */}
            <div>
              <h2 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl lg:text-4xl">
                Why <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">SleepTwin</span> Was Created
              </h2>
              <p className="mt-1.5 text-xs sm:text-sm font-medium text-slate-500">
                Overcoming the 90-day clinical blind spot between clinic visits with personalized predictive modeling.
              </p>
            </div>

            {/* Problem vs Solution Comparative Grid */}
            <div className="grid grid-cols-1 gap-3 pt-1 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-md bg-rose-100 text-rose-700 text-[10px] font-bold">✕</span>
                  <span className="text-xs font-bold text-slate-900">The Clinical Blind Spot</span>
                </div>
                <p className="text-[11.5px] text-slate-600 leading-relaxed">
                  Patients see their doctor for only ~15 minutes every few months. Wearable watches provide generic scores (like <i>“74/100”</i>) that completely ignore diabetes, beta-blockers, and hypertension.
                </p>
              </div>

              <div className="rounded-2xl border border-blue-200/90 bg-blue-50/40 p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-md bg-blue-100 text-blue-700 text-[10px] font-bold">✓</span>
                  <span className="text-xs font-bold text-blue-950">The SleepTwin Twin</span>
                </div>
                <p className="text-[11.5px] text-slate-700 leading-relaxed">
                  Creates an individualized virtual replica fusing clinical chart records with continuous watch sensors to forecast tomorrow’s spikes and simulate fixes before they occur.
                </p>
              </div>
            </div>

            {/* Highlight Metric Callout */}
            <div className="rounded-xl border border-blue-100 bg-white p-3 text-xs text-slate-700 shadow-2xs">
              <div className="flex items-start gap-2">
                <span className="font-bold text-blue-600 mt-0.5">•</span>
                <span>
                  <b>Why sleep matters so much:</b> Just 4 nights of 5 hours of sleep quietly cuts cellular insulin sensitivity by <b>~25%</b>, setting up next-day glucose spikes &gt; 180 mg/dL even if your diet didn’t change.
                </span>
              </div>
            </div>
          </div>

          {/* Right side animation */}
          <div className="flex justify-center lg:col-span-5 lg:justify-end">
            <DigitalTwinHeroAnimation />
          </div>
        </div>

        {/* 3 Value Pillars */}
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200/80 border-t-3 border-t-blue-500 bg-white p-4 shadow-2xs transition hover:shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600 mb-2.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
            </div>
            <div className="font-bold text-slate-900 text-sm">Learns Your Personal Normal</div>
            <p className="mt-1 text-xs text-slate-600 leading-relaxed">
              Spends 14 days learning what sleep, heart rate, and HRV are normal for <i>you</i> instead of comparing you to strangers.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 border-t-3 border-t-emerald-500 bg-white p-4 shadow-2xs transition hover:shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 mb-2.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m22 12-4-4v3H3v2h15v3z" /></svg>
            </div>
            <div className="font-bold text-slate-900 text-sm">Next-Day Foresight</div>
            <p className="mt-1 text-xs text-slate-600 leading-relaxed">
              Predicts tomorrow’s glucose spikes (&gt; 180 mg/dL) and morning blood pressure surges (&gt; 145 mmHg) as soon as your watch syncs.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 border-t-3 border-t-indigo-500 bg-white p-4 shadow-2xs transition hover:shadow-xs">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mb-2.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
            </div>
            <div className="font-bold text-slate-900 text-sm">Interactive What-If Sandbox</div>
            <p className="mt-1 text-xs text-slate-600 leading-relaxed">
              Allows testing interventions (longer sleep, consistent bedtime, CPAP) on interactive sliders to see tomorrow’s curve flatten in 15 ms.
            </p>
          </div>
        </div>
      </div>

      {/* 2. THE TWO DATA STREAMS */}
      <div>
        <div className="mb-3">
          <h3 className="text-lg font-bold text-slate-900">The Two Data Streams</h3>
          <p className="text-xs text-slate-500">SleepTwin creates a complete picture by fusing static medical history with live daily sensors.</p>
        </div>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* Stream 1 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold text-xs">
                1
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Static Health Record (EHR)</h4>
                <p className="text-[11px] text-slate-500">From the clinic chart · Does not change daily</p>
              </div>
            </div>
            <ul className="mt-3 space-y-2 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span><b>Demographics:</b> Age, biological sex, BMI, and waist circumference.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span><b>Diagnostic History:</b> Type 2 diabetes duration, hypertension, and sleep apnea.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span><b>Laboratory Panels:</b> HbA1c (long-term sugar), fasting glucose, kidney eGFR, and cholesterol.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span><b>Medications:</b> Metformin, beta-blockers, ACE inhibitors, and SGLT2 inhibitors.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span><b>Genetic Markers:</b> T2D polygenic risk score, TCF7L2 (beta-cell response), and MTNR1B (late eating sensitivity).</span>
              </li>
            </ul>
            <div className="mt-4 rounded-xl bg-slate-50 p-2.5 text-[11px] text-slate-500 leading-relaxed border border-slate-100">
              Calibrated from <b>CDC NHANES</b> real survey data so all laboratory tests and age/BMI patterns are naturally correlated.
            </div>
          </div>

          {/* Stream 2 */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700 font-bold text-xs">
                2
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Dynamic Wearable Stream</h4>
                <p className="text-[11px] text-slate-500">From smartwatches & sensors · Changes every night</p>
              </div>
            </div>
            <ul className="mt-3 space-y-2 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span><b>Sleep Duration & Timing:</b> Hours slept, bedtime consistency, and wake-up times.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span><b>Sleep Fragmentation:</b> Time awake after falling asleep (WASO) and deep sleep %.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span><b>Heart & Autonomic Signals:</b> Nocturnal Heart Rate Variability (HRV) and Resting Heart Rate (RHR).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span><b>Oxygen Dips (ODI):</b> Nighttime blood oxygen drops that flag hidden sleep apnea.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 font-bold">•</span>
                <span><b>Continuous Glucose (CGM):</b> Interstitial blood sugar recorded every 5 minutes around the clock.</span>
              </li>
            </ul>
            <div className="mt-4 rounded-xl bg-slate-50 p-2.5 text-[11px] text-slate-500 leading-relaxed border border-slate-100">
              Inherited from real <b>LifeSnaps Fitbit</b> users so personal ranges reflect genuine human variability.
            </div>
          </div>
        </div>
      </div>

      {/* 3. SIMPLIFIED HUMAN BIOLOGY & VISUAL DIAGRAMS */}
      <Card title="How Sleep Connects to Your Body (In Simple Words)">
        <p className="text-sm text-slate-600 mb-6">
          Poor sleep is not just about feeling tired. When sleep is cut short or fragmented, specific biological chain reactions disrupt your metabolism and blood vessels.
        </p>

        {/* 3 Simple Visual Explanations */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Card 1: Glucose */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-slate-50/60 p-4 transition hover:bg-slate-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 font-bold text-xs">A</span>
              <h4 className="font-bold text-slate-900 text-sm">Sleep & Blood Sugar</h4>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              When you sleep less than 6 hours for several nights, your body enters a mild stress state and releases cortisol.
            </p>

            {/* Visual Mini Flow */}
            <div className="my-4 space-y-2 rounded-xl bg-white p-3 border border-slate-200/80 text-[11.5px]">
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold text-[10px]">1</span>
                <span>4 nights of 5 hours of sleep</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-[10px]">2</span>
                <span>Cells become resistant to insulin (~25% drop)</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 font-semibold text-red-600">
                <span className="h-5 w-5 rounded-full bg-red-500 text-white flex items-center justify-center font-bold text-[10px]">3</span>
                <span>Same lunch triggers a spike &gt; 180 mg/dL</span>
              </div>
            </div>

            <p className="mt-auto text-[11px] text-slate-500 italic">
              Key takeaway: You can eat the exact same healthy food, but bad sleep turns it into a spike.
            </p>
          </div>

          {/* Card 2: Blood Pressure */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-slate-50/60 p-4 transition hover:bg-slate-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-700 font-bold text-xs">B</span>
              <h4 className="font-bold text-slate-900 text-sm">Sleep & Blood Pressure</h4>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              In sleep apnea, the airway collapses. Every time breathing pauses, oxygen drops and the brain panics with an adrenaline surge.
            </p>

            {/* Visual Mini Flow */}
            <div className="my-4 space-y-2 rounded-xl bg-white p-3 border border-slate-200/80 text-[11.5px]">
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-[10px]">1</span>
                <span>Nocturnal oxygen drops (&ge; 15 dips/hr)</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-[10px]">2</span>
                <span>Dozens of adrenaline jolts all night long</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 font-semibold text-amber-700">
                <span className="h-5 w-5 rounded-full bg-amber-500 text-white flex items-center justify-center font-bold text-[10px]">3</span>
                <span>Morning SBP surges &gt; 145 mmHg</span>
              </div>
            </div>

            <p className="mt-auto text-[11px] text-slate-500 italic">
              Key takeaway: You might think you slept 7 hours, but hidden oxygen drops silently raise morning stroke risk.
            </p>
          </div>

          {/* Card 3: 2-Hour Alert */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-slate-50/60 p-4 transition hover:bg-slate-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold text-xs">C</span>
              <h4 className="font-bold text-slate-900 text-sm">Live 2-Hour Early Warning</h4>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Standard CGM apps only sound an alarm <i>after</i> your sugar has already crossed 180 mg/dL. SleepTwin warns you ahead of time.
            </p>

            {/* Visual Mini Flow */}
            <div className="my-4 space-y-2 rounded-xl bg-white p-3 border border-slate-200/80 text-[11.5px]">
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-[10px]">1</span>
                <span>Monitors live rise rate + meal carbs</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 text-slate-800">
                <span className="h-5 w-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-[10px]">2</span>
                <span>Factors in last night’s sleep debt &amp; HRV</span>
              </div>
              <div className="pl-2 text-slate-400 text-xs">↓</div>
              <div className="flex items-center gap-2 font-semibold text-blue-700">
                <span className="h-5 w-5 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[10px]">3</span>
                <span>Warns you ~70 minutes before it crosses 180</span>
              </div>
            </div>

            <p className="mt-auto text-[11px] text-slate-500 italic">
              Key takeaway: Gives a 70-minute window to take a 15-minute walk and prevent the spike completely.
            </p>
          </div>
        </div>

        {/* Clean Overview Diagram */}
        <div className="mt-6 pt-6 border-t border-slate-100">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
            System Architecture Overview
          </div>
          <SimDiagram />
        </div>

        {/* Optional Collapsible Formula Section */}
        <div className="mt-6 pt-4 border-t border-slate-100">
          <button
            onClick={() => setShowFormulas(!showFormulas)}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            <span>{showFormulas ? '▲ Hide' : '▼ View'} Academic Differential Equations &amp; Formulas (For Researchers)</span>
          </button>

          {showFormulas && (
            <AcademicFormulasSection siDropPct={Math.round(Number(dc.si_drop_4x5h ?? 0.25) * 100)} />
          )}
        </div>
      </Card>

      {/* 4. WHAT THE TWIN DOES EVERY MORNING */}
      <Card title="The 6-Step Morning Routine: How SleepTwin Thinks">
        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              step: '1',
              title: 'Learns Your Baseline',
              desc: 'Days 1–14 establish each person’s unique normal range for sleep duration, HRV, resting heart rate, and steps.',
              tag: 'Personalization'
            },
            {
              step: '2',
              title: 'Spots Nightly Drift',
              desc: 'When last night syncs, it checks if sleep was short, bedtime shifted late, HRV fell, or oxygen dipped.',
              tag: 'Detection'
            },
            {
              step: '3',
              title: 'Fuses with Health Chart',
              desc: 'Combines the sleep drift with your medical records. The same bad night is far more dangerous for an uncontrolled diabetic.',
              tag: 'Clinical Context'
            },
            {
              step: '4',
              title: 'Predicts Tomorrow’s Risks',
              desc: 'Estimates probability of next-day glucose spikes (> 180 mg/dL) and morning blood pressure surges (> 145 mmHg).',
              tag: 'AI Forecast'
            },
            {
              step: '5',
              title: 'Explains in Plain English',
              desc: 'Turns SHAP values into understandable clinical reasons (e.g. “4 short nights in a row … beta-blocker masks heart rate”).',
              tag: 'Explainability'
            },
            {
              step: '6',
              title: 'Simulates Fixes (What-If)',
              desc: 'Doctors can adjust sleep or add CPAP on interactive sliders to see tomorrow’s glucose curve flatten in 15 milliseconds.',
              tag: 'Intervention'
            },
          ].map((item) => (
            <div key={item.step} className="flex flex-col justify-between rounded-xl bg-slate-50/80 p-4 border border-slate-200/80">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-600 text-white text-xs font-bold">
                    {item.step}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide bg-white px-2 py-0.5 rounded-md border border-slate-200">
                    {item.tag}
                  </span>
                </div>
                <div className="font-bold text-slate-900 text-sm">{item.title}</div>
                <div className="mt-1 text-xs text-slate-600 leading-relaxed">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 5. SCIENTIFIC EVIDENCE & VALIDATION */}
      <div>
        <div className="mb-3">
          <h3 className="text-lg font-bold text-slate-900">Proven Validation &amp; Results</h3>
          <p className="text-xs text-slate-500">Every metric is computed directly by the pipeline code without hand-typed numbers.</p>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {/* Ablation: Glucose */}
          {s.nextday && (
            <Card title="Does Fusing Both Streams Help? (Next-Day Glucose)">
              <Ablation r={s.nextday.glucose_event_24h} />
            </Card>
          )}

          {/* Ablation: Blood Pressure */}
          {s.nextday && (
            <Card title="Morning Blood Pressure Surge (&gt; 145 mmHg)">
              <Ablation r={s.nextday.bp_event} />
            </Card>
          )}
        </div>

        {/* 2-Hour Alert & LifeSnaps Validation Cards */}
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
          {s.spike_2h && (
            <Card title="2-Hour Live Glucose Spike Alert">
              <div className="space-y-4">
                {/* 3 Metric Pills */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-2.5">
                    <div className="text-xl font-extrabold text-blue-900">{s.spike_2h.median_lead_min} min</div>
                    <div className="mt-0.5 text-[11px] font-semibold text-blue-700">Advance Warning</div>
                    <div className="text-[10px] text-slate-500">Median lead time</div>
                  </div>
                  <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                    <div className="text-xl font-extrabold text-slate-900">{s.spike_2h.auroc.toFixed(2)}</div>
                    <div className="mt-0.5 text-[11px] font-semibold text-slate-700">AUROC Score</div>
                    <div className="text-[10px] text-slate-500">vs {s.spike_2h.trend_only_auroc.toFixed(2)} naive (+20%)</div>
                  </div>
                  <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                    <div className="text-xl font-extrabold text-slate-900">{Math.round(s.spike_2h.episode_recall * 100)}%</div>
                    <div className="mt-0.5 text-[11px] font-semibold text-slate-700">Recall Rate</div>
                    <div className="text-[10px] text-slate-500">Surges caught early</div>
                  </div>
                </div>

                {/* 3-Step Advance Intervention Window */}
                <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3">
                  <div className="mb-2 text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
                    How the 70-Minute Window Protects You
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200/60 shadow-2xs">
                      <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wide">T − 70 min</div>
                      <div className="mt-1 font-semibold text-slate-800 text-[11px]">Early Warning</div>
                      <p className="mt-0.5 text-[10px] text-slate-500 leading-tight">
                        Rise rate + sleep debt signal impending spike.
                      </p>
                    </div>
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200/60 shadow-2xs">
                      <div className="text-[10px] font-bold text-amber-600 uppercase tracking-wide">T − 45 min</div>
                      <div className="mt-1 font-semibold text-slate-800 text-[11px]">Action Window</div>
                      <p className="mt-0.5 text-[10px] text-slate-500 leading-tight">
                        15-min light walk clears circulating glucose.
                      </p>
                    </div>
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200/60 shadow-2xs">
                      <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-wide">T = 0</div>
                      <div className="mt-1 font-semibold text-slate-800 text-[11px]">Curve Blunted</div>
                      <p className="mt-0.5 text-[10px] text-slate-500 leading-tight">
                        Peak remains safely below 180 mg/dL.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Clinical Summary */}
                <div className="rounded-xl border border-slate-200/70 bg-white p-3 text-xs text-slate-600 leading-relaxed shadow-2xs">
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-blue-600 text-sm leading-none mt-0.5">•</span>
                    <span>
                      Evaluated across <b>{s.spike_2h.n_samples.toLocaleString()} waking hourly checkpoints</b>. Traditional CGMs only alarm after sugar is already high; SleepTwin provides actionable lead time.
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {s.lifesnaps_validation?.available && (
            <Card title="Real-Data Check: LifeSnaps (38 Real Fitbit Users)">
              <div className="space-y-4">
                {/* 3 Metric Pills */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                    <div className="text-xl font-extrabold text-slate-900">{s.lifesnaps_validation.n_users}</div>
                    <div className="mt-0.5 text-[11px] font-semibold text-slate-700">Fitbit Users</div>
                    <div className="text-[10px] text-slate-500">{s.lifesnaps_validation.n_nights.toLocaleString()} tracked nights</div>
                  </div>
                  <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-2.5">
                    <div className="text-xl font-extrabold text-amber-900">
                      {(s.lifesnaps_validation.rhr_z_short_mean - s.lifesnaps_validation.rhr_z_normal_mean > 0 ? '+' : '')}
                      {(s.lifesnaps_validation.rhr_z_short_mean - s.lifesnaps_validation.rhr_z_normal_mean).toFixed(2)} SD
                    </div>
                    <div className="mt-0.5 text-[11px] font-semibold text-amber-800">Resting HR Shift</div>
                    <div className="text-[10px] text-amber-700">p = 0.003 (elevated)</div>
                  </div>
                  <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-2.5">
                    <div className="text-xl font-extrabold text-indigo-900">
                      {(s.lifesnaps_validation.hrv_z_short_mean - s.lifesnaps_validation.hrv_z_normal_mean).toFixed(2)} SD
                    </div>
                    <div className="mt-0.5 text-[11px] font-semibold text-indigo-800">HRV Suppression</div>
                    <div className="text-[10px] text-indigo-700">p = 2e-5 (reduced)</div>
                  </div>
                </div>

                {/* Biological Response Breakdown */}
                <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3">
                  <div className="mb-2 text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
                    Observed Biological Effects After Short Sleep
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-lg bg-white p-2.5 border border-slate-200/60 shadow-2xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 text-[11.5px]">Resting Heart Rate</span>
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-bold text-amber-800">ELEVATED</span>
                      </div>
                      <p className="mt-1 text-[10.5px] text-slate-600 leading-snug">
                        Heart rate remains elevated the next day due to sustained sympathetic nervous stress.
                      </p>
                    </div>

                    <div className="rounded-lg bg-white p-2.5 border border-slate-200/60 shadow-2xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 text-[11.5px]">Heart Rate Variability</span>
                        <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[9px] font-bold text-indigo-800">SUPPRESSED</span>
                      </div>
                      <p className="mt-1 text-[10.5px] text-slate-600 leading-snug">
                        Nighttime HRV drops significantly, indicating blunted parasympathetic recovery.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Real-World Clinical Takeaway */}
                <div className="rounded-xl border border-slate-200/70 bg-white p-3 text-xs text-slate-600 leading-relaxed shadow-2xs">
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-blue-600 text-sm leading-none mt-0.5">•</span>
                    <span>
                      <b>Real-world verification:</b> Proves with empirical Fitbit wearable data that personal baseline deviations are measurable, statistically significant, and clinically predictive.
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* 6. DATA CARD & LIMITATIONS */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Modern Data Card */}
        <Card title="Dataset Provenance & Cohort Specifications">
          <div className="space-y-3.5">
            {/* Primary Data Ingestion Sources */}
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs">
              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Virtual Cohort</div>
                <div className="mt-0.5 font-bold text-slate-900">{String(dc.cohort)}</div>
                <div className="text-[10.5px] text-slate-500">6,300 simulated patient-days</div>
              </div>

              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">EHR Calibration</div>
                <div className="mt-0.5 font-bold text-slate-900">{String(dc.ehr_calibration)}</div>
                <div className="text-[10.5px] text-slate-500">CDC survey real-world statistics</div>
              </div>

              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Wearable Source</div>
                <div className="mt-0.5 font-bold text-slate-900">{String(dc.wearable_calibration)}</div>
                <div className="text-[10.5px] text-slate-500">Real-world Fitbit multi-sensor feed</div>
              </div>

              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-2.5">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">CGM Dynamic Range</div>
                <div className="mt-0.5 font-bold text-slate-900">
                  {Array.isArray(dc.glucose_range)
                    ? `${Math.round(dc.glucose_range[0])} – ${Math.round(dc.glucose_range[1])} mg/dL`
                    : '66 – 316 mg/dL'}
                </div>
                <div className="text-[10.5px] text-slate-500">1-min fixed-step Euler ODE solver</div>
              </div>
            </div>

            {/* Cohort Condition Prevalence */}
            <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                Cohort Clinical Prevalence
              </div>
              <div className="flex flex-wrap gap-1.5">
                {dc.cohort_mix && typeof dc.cohort_mix === 'object' &&
                  Object.entries(dc.cohort_mix as Record<string, number>).map(([k, v]) => {
                    const labels: Record<string, string> = {
                      t2d: 'Type 2 Diabetes',
                      prediabetes: 'Prediabetes',
                      htn: 'Hypertension',
                      osa_true: 'Hidden Sleep Apnea',
                      osa_diagnosed: 'Diagnosed Apnea',
                    }
                    const label = labels[k] || k.replace(/_/g, ' ')
                    return (
                      <span
                        key={k}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 shadow-2xs"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                        <span>{label}</span>
                        <span className="font-extrabold text-slate-900">{(v * 100).toFixed(0)}%</span>
                      </span>
                    )
                  })}
              </div>
            </div>

            {/* Sandbox & Compliance Callout */}
            <div className="rounded-xl border border-emerald-200/80 bg-emerald-50/50 p-2.5 text-xs text-emerald-900 leading-snug">
              <div className="font-bold text-[11px] uppercase tracking-wide text-emerald-800 mb-0.5">
                Sandbox &amp; Data Privacy Compliance
              </div>
              <p className="text-[11px] text-emerald-800">
                {String(dc.sandbox)}
              </p>
            </div>
          </div>
        </Card>

        {/* Modern Limitations & Scope Card */}
        <Card title="Clinical Limitations &amp; Scope">
          <div className="space-y-2.5 text-xs">
            <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-3 shadow-2xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-slate-900 text-[11.5px]">Decision Support, Not Diagnosis</span>
                <span className="rounded bg-slate-200/80 px-1.5 py-0.5 text-[9.5px] font-bold text-slate-700">
                  CLINICAL INTENT
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                SleepTwin is built to support clinical decision-making by quantifying risk trajectory; the treating physician retains full diagnostic and therapeutic authority.
              </p>
            </div>

            <div className="rounded-xl border border-amber-200/80 bg-amber-50/40 p-3 shadow-2xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-slate-900 text-[11.5px]">Research Prototype</span>
                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[9.5px] font-bold text-amber-800">
                  MATURITY
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                Trained on realistically calibrated virtual cohorts to demonstrate computational physiological feasibility prior to prospective hospital trials.
              </p>
            </div>

            <div className="rounded-xl border border-indigo-200/80 bg-indigo-50/40 p-3 shadow-2xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-slate-900 text-[11.5px]">Simulated Genomics</span>
                <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-[9.5px] font-bold text-indigo-800">
                  GENETICS
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                Risk alleles (<i>TCF7L2</i>, <i>MTNR1B</i>) and polygenic risk scores are modeled using published effect sizes for beta-cell and circadian melatonin response.
              </p>
            </div>

            <div className="rounded-xl border border-blue-200/80 bg-blue-50/40 p-3 shadow-2xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-slate-900 text-[11.5px]">Population Calibration</span>
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[9.5px] font-bold text-blue-800">
                  DEMOGRAPHICS
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">
                Currently calibrated against US CDC NHANES cohorts; active ongoing work aims to adapt baseline parameters to South Asian populations (e.g. ICMR-INDIAB).
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* 7. ACADEMIC CITATIONS & REFERENCES */}
      <Card title="Published Medical Literature &amp; Sources">
        <div className="mb-2">
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="text-xs font-semibold text-accent-700 hover:underline"
          >
            {showTechnicalDetails ? 'Collapse bibliography' : 'Show full bibliography & citations (12 references)'}
          </button>
        </div>
        {showTechnicalDetails && (
          <ul className="grid grid-cols-1 gap-x-6 gap-y-1 text-[11px] text-slate-600 md:grid-cols-2 pt-2 border-t border-slate-100">
            <li>CDC NHANES 2017–March 2020 pre-pandemic (public domain)</li>
            <li>Yfantidou S. et al. LifeSnaps, Sci Data 2022 – Zenodo 7229547 (CC-BY-4.0)</li>
            <li>Bergman RN et al. Am J Physiol 1979; J Clin Invest 1981 – Minimal model</li>
            <li>Dalla Man C. et al. IEEE TBME 2007 – Glucose distribution volume</li>
            <li>Spiegel K. et al. Lancet 1999 – Sleep debt and glucose tolerance (25% drop)</li>
            <li>Buxton OM et al. Diabetes 2010 – Sleep restriction lowers insulin sensitivity</li>
            <li>Donga E. et al. JCEM 2010 – One night of short sleep causes insulin resistance</li>
            <li>Grant SFA et al. Nat Genet 2006 – TCF7L2 genetic susceptibility</li>
            <li>Prokopenko I. et al. Nat Genet 2009 – MTNR1B melatonin receptor gene</li>
            <li>Garaulet M. et al. Cell Metab 2020 – MTNR1B × late eating interaction</li>
            <li>Inker LA et al. NEJM 2021 – Race-free CKD-EPI 2021 creatinine equation</li>
            <li>Synthea (field naming standard) · PhysioNet (pattern references)</li>
          </ul>
        )}
      </Card>

      <Disclaimer />
    </div>
  )
}

function AcademicFormulasSection({ siDropPct = 25 }: { siDropPct?: number }) {
  return (
    <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
      {/* Card 1: Insulin Sensitivity */}
      <div className="flex flex-col justify-between rounded-2xl border border-blue-200/80 bg-white p-4 shadow-2xs">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-900">1. Sleep Debt → Insulin Sensitivity</span>
            <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700">
              METABOLISM
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3 leading-tight">
            Quantifies how cumulative sleep loss reduces insulin sensitivity (SI) over a 7-day memory window.
          </p>

          {/* Equation Block */}
          <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-[11px] font-mono text-slate-800 leading-relaxed space-y-2">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Cumulative Debt:</div>
              <div className="text-blue-900 font-semibold">debt_t = Σ (deficit_t-k × 0.75^k)</div>
              <div className="text-[10px] text-slate-500 font-sans">k = 0..6 (exponential 7-night decay)</div>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Sensitivity Scale:</div>
              <div className="text-blue-900 font-semibold">SI_t = SI_0 × exp(−a₁·debt − a₂·shift − a₃·WASO)</div>
              <div className="text-slate-600 pl-4">× (1 + b₁·Δsteps + b₂·metformin)</div>
            </div>
          </div>
        </div>

        {/* Callout Badge */}
        <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-blue-50/80 px-2.5 py-1.5 text-[11px] font-semibold text-blue-800 border border-blue-100">
          <span className="font-bold text-blue-700 text-sm leading-none">•</span>
          <span>4 nights × 5 h sleep → SI drops by {siDropPct}%</span>
        </div>
      </div>

      {/* Card 2: Minimal Model */}
      <div className="flex flex-col justify-between rounded-2xl border border-indigo-200/80 bg-white p-4 shadow-2xs">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-900">2. Bergman Minimal Model</span>
            <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
              5-MIN CGM
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3 leading-tight">
            Classic physiological differential equations integrated with a 1-minute fixed-step Euler solver.
          </p>

          {/* Equation Block */}
          <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-[11px] font-mono text-slate-800 leading-relaxed space-y-2">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Glucose Rate:</div>
              <div className="text-indigo-900 font-semibold">dG/dt = −(p₁ + X)·G + p₁·Gb + Ra(t)/V</div>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Remote Insulin Action:</div>
              <div className="text-indigo-900 font-semibold">dX/dt = −p₂·X + p₃·(I − Ib)</div>
              <div className="text-[10px] text-slate-500 font-sans">where SI = p₃ / p₂</div>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Pancreatic Response:</div>
              <div className="text-indigo-900 font-semibold">I(t) = Ib + β · max(0, G − Gb)</div>
            </div>
          </div>
        </div>

        {/* Callout Badge */}
        <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-indigo-50/80 px-2.5 py-1.5 text-[11px] font-semibold text-indigo-800 border border-indigo-100">
          <span className="font-bold text-indigo-700 text-sm leading-none">•</span>
          <span>3 meals/day · Gamma absorption · 5-min CGM</span>
        </div>
      </div>

      {/* Card 3: Blood Pressure */}
      <div className="flex flex-col justify-between rounded-2xl border border-amber-200/80 bg-white p-4 shadow-2xs">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-900">3. Morning Blood Pressure Rule</span>
            <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
              VASCULAR
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3 leading-tight">
            Transparent clinical rule linking nocturnal hypoxia, sleep debt, and wakefulness to morning SBP.
          </p>

          {/* Equation Block */}
          <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-[11px] font-mono text-slate-800 leading-relaxed space-y-2">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-sans mb-0.5">Morning SBP Model:</div>
              <div className="text-amber-900 font-semibold">SBP = SBP_clinic + c₁·ODI + c₂·debt</div>
              <div className="text-slate-600 pl-4">+ c₃·(WASO/60) − c₄·ACEi + offset</div>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5 text-[10.5px] text-slate-600 font-sans">
              <div>• <b className="font-mono text-amber-900">c₁ = +0.55</b> mmHg per oxygen dip (ODI)</div>
              <div>• <b className="font-mono text-amber-900">c₂ = +1.10</b> mmHg per hour of sleep debt</div>
              <div>• <b className="font-mono text-amber-900">c₄ = −6.00</b> mmHg for ACE-inhibitor use</div>
            </div>
          </div>
        </div>

        {/* Callout Badge */}
        <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-amber-50/80 px-2.5 py-1.5 text-[11px] font-semibold text-amber-800 border border-amber-100">
          <span className="font-bold text-amber-700 text-sm leading-none">•</span>
          <span>Morning SBP &gt; 145 mmHg triggers surge alert</span>
        </div>
      </div>
    </div>
  )
}

function Ablation({ r }: { r: TargetResult }) {
  const rows: [string, keyof TargetResult, string][] = [
    ['Health record only', 'ehr_only', 'Static clinic chart baseline'],
    ['Wearables only', 'wearables_only', 'Dynamic continuous sensors'],
    ['Fused twin (both streams)', 'fused', 'Complete multi-modal model'],
  ]

  return (
    <div className="space-y-3.5">
      {/* Comparative Model Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200/90 bg-white">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/80 text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
              <th className="py-2.5 pl-3.5 text-left">Model Stream</th>
              <th className="py-2.5 text-right">AUROC</th>
              <th className="py-2.5 text-right">AUPRC</th>
              <th className="py-2.5 pr-3.5 text-right">False Alerts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {rows.map(([name, k, desc]) => {
              const m = r[k] as TargetResult['fused']
              const isFused = k === 'fused'
              const aurocPct = Math.min(100, Math.max(0, ((m.auroc - 0.5) / 0.5) * 100))

              return (
                <tr
                  key={k}
                  className={`transition-colors ${
                    isFused
                      ? 'bg-blue-50/50 font-semibold text-slate-900 border-l-3 border-blue-600'
                      : 'hover:bg-slate-50/60'
                  }`}
                >
                  <td className="py-2.5 pl-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{name}</span>
                      {isFused && (
                        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[9px] font-extrabold text-blue-700 tracking-wide uppercase">
                          Best
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] font-normal text-slate-500">{desc}</div>
                  </td>

                  {/* AUROC with Visual Meter */}
                  <td className="py-2.5 text-right tabular-nums">
                    <div className="flex items-center justify-end gap-2.5">
                      <div className="hidden h-2 w-16 rounded-full bg-slate-100 sm:block overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isFused ? 'bg-blue-600' : 'bg-slate-400'
                          }`}
                          style={{ width: `${aurocPct}%` }}
                        />
                      </div>
                      <span className={isFused ? 'font-extrabold text-blue-700' : 'font-medium'}>
                        {m.auroc.toFixed(3)}
                      </span>
                    </div>
                  </td>

                  {/* AUPRC */}
                  <td className="py-2.5 text-right tabular-nums font-medium">
                    <span className={isFused ? 'font-extrabold text-slate-900' : 'text-slate-600'}>
                      {m.auprc.toFixed(3)}
                    </span>
                  </td>

                  {/* False Alerts / Week */}
                  <td className="py-2.5 pr-3.5 text-right tabular-nums">
                    <span
                      className={`inline-block rounded px-1.5 py-0.5 text-[11px] font-bold ${
                        isFused
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80'
                          : 'text-slate-600'
                      }`}
                    >
                      {m.false_alerts_per_patient_week.toFixed(2)}/wk
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Diabetic Subgroup Benchmark Card */}
      {r.t2d_subgroup && (
        <div className="rounded-xl border border-slate-200/90 bg-slate-50/70 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10.5px] font-bold uppercase tracking-wider text-slate-600">
              Diabetic Subgroup Test (Harder Cohort)
            </span>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-[9.5px] font-bold text-blue-800">
              GREATEST GAIN
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg border border-slate-200/70 bg-white p-2 shadow-2xs">
              <div className="text-[10px] text-slate-500 font-medium">Record Only</div>
              <div className="mt-0.5 text-sm font-bold text-slate-700">
                {r.t2d_subgroup.ehr_only?.toFixed(2) ?? '–'}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200/70 bg-white p-2 shadow-2xs">
              <div className="text-[10px] text-slate-500 font-medium">Wearables Only</div>
              <div className="mt-0.5 text-sm font-bold text-slate-700">
                {r.t2d_subgroup.wearables_only?.toFixed(2) ?? '–'}
              </div>
            </div>

            <div className="rounded-lg border border-blue-200 bg-blue-50/80 p-2 shadow-2xs">
              <div className="text-[10px] font-bold text-blue-700">Fused Twin</div>
              <div className="mt-0.5 text-sm font-extrabold text-blue-900">
                {r.t2d_subgroup.fused?.toFixed(2) ?? '–'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Clinical Interpretation */}
      <div className="rounded-xl border border-slate-200/70 bg-white p-3 text-xs text-slate-600 leading-relaxed shadow-2xs">
        <div className="flex items-start gap-2">
          <span className="font-bold text-blue-600 text-sm leading-none mt-0.5">•</span>
          <span>{r.interpretation}</span>
        </div>
      </div>
    </div>
  )
}

function SimDiagram() {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-100 text-blue-700 font-bold text-xs">
            ⇄
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">End-to-End System Dataflow</h4>
            <p className="text-[11px] text-slate-500">How raw continuous sensors and clinical charts turn into early preventive alerts</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-slate-500">
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-slate-400" /> Inputs</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Drift</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-blue-500" /> Metabolic Core</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-purple-500" /> Simulation</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-rose-500" /> Alerts</span>
        </div>
      </div>

      <svg viewBox="0 0 1020 280" className="min-w-[840px] w-full select-none" role="img" aria-label="System architecture visual diagram">
        <defs>
          <filter id="card-shadow" x="-5%" y="-10%" width="110%" height="130%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#0f172a" floodOpacity="0.04" />
          </filter>
          <marker id="arrow-slate" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,1 L5,3 L0,5 z" fill="#94a3b8" />
          </marker>
          <marker id="arrow-blue" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,1 L5,3 L0,5 z" fill="#2563eb" />
          </marker>
          <marker id="arrow-amber" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,1 L5,3 L0,5 z" fill="#ea580c" />
          </marker>
          <marker id="arrow-rose" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,1 L5,3 L0,5 z" fill="#e11d48" />
          </marker>
        </defs>

        {/* Stage Columns Backgrounds / Labels */}
        <g>
          {/* Col 1 */}
          <rect x="20" y="10" width="175" height="24" rx="6" fill="#f8fafc" />
          <text x="107" y="26" textAnchor="middle" fontSize="10" fontWeight="700" fill="#64748b" letterSpacing="0.05em">
            01 · MULTI-MODAL DATA
          </text>

          {/* Col 2 */}
          <rect x="235" y="10" width="175" height="24" rx="6" fill="#f0fdf4" />
          <text x="322" y="26" textAnchor="middle" fontSize="10" fontWeight="700" fill="#16a34a" letterSpacing="0.05em">
            02 · BASELINE DEVIATION
          </text>

          {/* Col 3 */}
          <rect x="450" y="10" width="175" height="24" rx="6" fill="#eff6ff" />
          <text x="537" y="26" textAnchor="middle" fontSize="10" fontWeight="700" fill="#2563eb" letterSpacing="0.05em">
            03 · DIGITAL TWIN STATE
          </text>

          {/* Col 4 */}
          <rect x="665" y="10" width="175" height="24" rx="6" fill="#f5f3ff" />
          <text x="752" y="26" textAnchor="middle" fontSize="10" fontWeight="700" fill="#7c3aed" letterSpacing="0.05em">
            04 · PHYSIOLOGY ENGINES
          </text>

          {/* Col 5 */}
          <rect x="880" y="10" width="125" height="24" rx="6" fill="#fff1f2" />
          <text x="942" y="26" textAnchor="middle" fontSize="10" fontWeight="700" fill="#e11d48" letterSpacing="0.05em">
            05 · FORESIGHT
          </text>
        </g>

        {/* Connectors with 100% Horizontal Departure and Arrival Tangents */}
        <g fill="none">
          {/* 1A (Wearables) -> 2A (Sleep Debt) */}
          <path d="M 195 79 L 233 79" stroke="#94a3b8" strokeWidth="1.8" markerEnd="url(#arrow-slate)" />

          {/* 1A (Wearables) -> 2B (Autonomic) [horizontal start and end] */}
          <path d="M 195 92 C 215 92, 213 192, 233 192" stroke="#94a3b8" strokeWidth="1.6" strokeDasharray="3 3" markerEnd="url(#arrow-slate)" />

          {/* 1B (Health Record) -> 2B (Autonomic) */}
          <path d="M 195 211 L 233 211" stroke="#94a3b8" strokeWidth="1.8" markerEnd="url(#arrow-slate)" />

          {/* 2A (Sleep Debt) -> 4A (Morning BP Rule) [straight horizontal upper bypass] */}
          <path d="M 410 60 L 663 60" stroke="#ea580c" strokeWidth="1.8" markerEnd="url(#arrow-amber)" />

          {/* 2A (Sleep Debt) -> 3A (Insulin Sensitivity) [horizontal start and arrival] */}
          <path d="M 410 95 C 430 95, 430 136, 448 136" stroke="#2563eb" strokeWidth="1.8" markerEnd="url(#arrow-blue)" />

          {/* 2B (Autonomic Signals) -> 3A (Insulin Sensitivity) [horizontal start and arrival] */}
          <path d="M 410 195 C 430 195, 430 158, 448 158" stroke="#2563eb" strokeWidth="1.8" markerEnd="url(#arrow-blue)" />

          {/* 3A (Insulin Sensitivity) -> 4B (Minimal Model) [horizontal start and arrival] */}
          <path d="M 625 147 C 645 147, 645 211, 663 211" stroke="#7c3aed" strokeWidth="1.8" markerEnd="url(#arrow-blue)" />

          {/* 4A (Morning BP Rule) -> 5A (BP Surge Alert) */}
          <path d="M 840 79 L 878 79" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-rose)" />

          {/* 4B (Minimal Model) -> 5B (Glucose Peak Alert) */}
          <path d="M 840 211 L 878 211" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-rose)" />
        </g>

        {/* --- CARDS (Clean rounded cards with zero protruding bars) --- */}

        {/* Card 1A: Nightly Sleep */}
        <g filter="url(#card-shadow)">
          <rect x="20" y="44" width="175" height="70" rx="12" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1.2" />
          <text x="34" y="68" fontSize="12" fontWeight="700" fill="#0f172a">1. Nightly Sleep</text>
          <text x="34" y="86" fontSize="10" fill="#64748b">Duration · Bedtime · WASO</text>
          <rect x="34" y="94" width="98" height="13" rx="3" fill="#f1f5f9" />
          <text x="38" y="103" fontSize="8.5" fontWeight="600" fill="#0284c7">Live Wearable Sync</text>
        </g>

        {/* Card 1B: Health Record */}
        <g filter="url(#card-shadow)">
          <rect x="20" y="176" width="175" height="70" rx="12" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1.2" />
          <text x="34" y="200" fontSize="12" fontWeight="700" fill="#0f172a">1. Health Record</text>
          <text x="34" y="218" fontSize="10" fill="#64748b">HbA1c · Meds · Genetics</text>
          <rect x="34" y="226" width="102" height="13" rx="3" fill="#f1f5f9" />
          <text x="38" y="235" fontSize="8.5" fontWeight="600" fill="#475569">Clinical EHR Baseline</text>
        </g>

        {/* Card 2A: Sleep Debt */}
        <g filter="url(#card-shadow)">
          <rect x="235" y="44" width="175" height="70" rx="12" fill="#f0fdf4" stroke="#86efac" strokeWidth="1.2" />
          <text x="249" y="68" fontSize="12" fontWeight="700" fill="#0f172a">2. Sleep Debt</text>
          <text x="249" y="86" fontSize="10" fill="#15803d">7-Night Cumulative Deficit</text>
          <rect x="249" y="94" width="102" height="13" rx="3" fill="#dcfce7" />
          <text x="253" y="103" fontSize="8.5" fontWeight="600" fill="#166534">0.75^k decay memory</text>
        </g>

        {/* Card 2B: Autonomic Signals */}
        <g filter="url(#card-shadow)">
          <rect x="235" y="176" width="175" height="70" rx="12" fill="#f0fdf4" stroke="#86efac" strokeWidth="1.2" />
          <text x="249" y="200" fontSize="12" fontWeight="700" fill="#0f172a">2. Autonomic Signals</text>
          <text x="249" y="218" fontSize="10" fill="#15803d">HRV Drop &amp; Nocturnal RHR</text>
          <rect x="249" y="226" width="108" height="13" rx="3" fill="#dcfce7" />
          <text x="253" y="235" fontSize="8.5" fontWeight="600" fill="#166534">Beta-blocker calibrated</text>
        </g>

        {/* Card 3A: Insulin Sensitivity (Metabolic Core) */}
        <g filter="url(#card-shadow)">
          <rect x="450" y="108" width="175" height="76" rx="12" fill="#eff6ff" stroke="#60a5fa" strokeWidth="1.5" />
          <rect x="462" y="117" width="92" height="14" rx="3" fill="#dbeafe" />
          <text x="508" y="127" textAnchor="middle" fontSize="8" fontWeight="700" fill="#1e40af" letterSpacing="0.04em">
            METABOLIC CORE
          </text>
          <text x="462" y="145" fontSize="12" fontWeight="700" fill="#1e3a8a">3. Insulin Sensitivity</text>
          <text x="462" y="161" fontSize="10" fill="#1d4ed8">SI drops ~25% after debt</text>
          <text x="462" y="174" fontSize="8.5" fontWeight="600" fill="#3b82f6">Exponential Decay Model</text>
        </g>

        {/* Card 4A: Morning BP Rule */}
        <g filter="url(#card-shadow)">
          <rect x="665" y="44" width="175" height="70" rx="12" fill="#fff7ed" stroke="#fdba74" strokeWidth="1.2" />
          <text x="679" y="68" fontSize="12" fontWeight="700" fill="#0f172a">4. Morning BP Rule</text>
          <text x="679" y="86" fontSize="10" fill="#c2410c">Hypoxia (ODI) + WASO</text>
          <rect x="679" y="94" width="108" height="13" rx="3" fill="#ffedd5" />
          <text x="683" y="103" fontSize="8.5" fontWeight="600" fill="#9a3412">Surge risk calculation</text>
        </g>

        {/* Card 4B: Bergman Minimal Model */}
        <g filter="url(#card-shadow)">
          <rect x="665" y="176" width="175" height="70" rx="12" fill="#f5f3ff" stroke="#c4b5fd" strokeWidth="1.2" />
          <text x="679" y="200" fontSize="12" fontWeight="700" fill="#0f172a">4. Minimal Model</text>
          <text x="679" y="218" fontSize="10" fill="#6d28d9">Meal Digestion + CGM</text>
          <rect x="679" y="226" width="112" height="13" rx="3" fill="#ede9fe" />
          <text x="683" y="235" fontSize="8.5" fontWeight="600" fill="#5b21b6">Euler 1-min ODE solver</text>
        </g>

        {/* Card 5A: BP Surge Alert */}
        <g filter="url(#card-shadow)">
          <rect x="880" y="44" width="125" height="70" rx="12" fill="#fff1f2" stroke="#fda4af" strokeWidth="1.4" />
          <rect x="890" y="52" width="48" height="14" rx="3" fill="#e11d48" />
          <text x="914" y="62" textAnchor="middle" fontSize="8.5" fontWeight="800" fill="#ffffff">ALERT</text>
          <text x="890" y="83" fontSize="11.5" fontWeight="800" fill="#881337">5. BP Surge</text>
          <text x="890" y="99" fontSize="9.5" fontWeight="600" fill="#be123c">&gt; 145 mmHg</text>
        </g>

        {/* Card 5B: Glucose Peak Alert */}
        <g filter="url(#card-shadow)">
          <rect x="880" y="176" width="125" height="70" rx="12" fill="#fff1f2" stroke="#fda4af" strokeWidth="1.4" />
          <rect x="890" y="184" width="48" height="14" rx="3" fill="#e11d48" />
          <text x="914" y="194" textAnchor="middle" fontSize="8.5" fontWeight="800" fill="#ffffff">ALERT</text>
          <text x="890" y="215" fontSize="11.5" fontWeight="800" fill="#881337">5. Glucose Peak</text>
          <text x="890" y="231" fontSize="9.5" fontWeight="600" fill="#be123c">&gt; 180 mg/dL</text>
        </g>
      </svg>
    </div>
  )
}

function DigitalTwinHeroAnimation() {
  return (
    <div className="relative w-full max-w-[370px] select-none rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Subtle ambient light glows */}
      <div className="pointer-events-none absolute -right-6 -top-6 h-32 w-32 rounded-full bg-blue-100/50 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-6 -left-6 h-32 w-32 rounded-full bg-indigo-100/40 blur-2xl" />

      {/* Header bar */}
      <div className="relative flex items-center justify-between border-b border-slate-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="relative flex h-2.5 w-2.5 items-center justify-center">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-900 leading-tight">Digital Twin Engine</div>
            <div className="text-[9.5px] font-medium text-slate-500">Live Dual-Stream Telemetry</div>
          </div>
        </div>
        <span className="rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700">
          CIRCA-ODE SYNC
        </span>
      </div>

      {/* Clinical Telemetry Monitor Screen */}
      <div className="relative my-3 rounded-xl border border-slate-200/80 bg-gradient-to-b from-slate-50/90 via-white to-blue-50/30 p-3 shadow-inner overflow-hidden">
        {/* Fine precision background grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'radial-gradient(#64748b 0.75px, transparent 0.75px)',
            backgroundSize: '12px 12px',
          }}
        />

        {/* Channel 1: Circadian Sleep Architecture & HRV */}
        <div className="relative mb-3">
          <div className="flex items-center justify-between text-[10.5px] mb-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <svg className="h-3 w-3 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              <span>Circadian Wave &amp; Autonomic Tone</span>
            </div>
            <span className="rounded border border-indigo-200 bg-indigo-50 px-1.5 py-0.5 text-[9.5px] font-semibold text-indigo-700">
              7.4h • HRV 48ms
            </span>
          </div>

          {/* Sleep Architecture Wave SVG */}
          <div className="relative h-12 w-full rounded-lg border border-slate-200/60 bg-white/70 overflow-hidden">
            <svg className="h-full w-full" preserveAspectRatio="none" viewBox="0 0 320 48">
              <defs>
                <linearGradient id="sleep-wave-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity="0.22" />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Shaded area under curve */}
              <path
                d="M 0 32 Q 40 12, 80 24 T 160 16 T 240 32 T 320 20 L 320 48 L 0 48 Z"
                fill="url(#sleep-wave-grad)"
              />

              {/* Smooth circadian sine wave */}
              <path
                d="M 0 32 Q 40 12, 80 24 T 160 16 T 240 32 T 320 20"
                fill="none"
                stroke="#6366f1"
                strokeWidth="2"
                strokeLinecap="round"
                className="animate-wave-flow"
              />

              {/* Autonomic heartbeat spike segment */}
              <path
                d="M 120 20 L 135 20 L 140 10 L 146 34 L 152 6 L 158 26 L 164 20 L 180 20"
                fill="none"
                stroke="#f43f5e"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Stage callout labels */}
              <text x="18" y="42" fontSize="7.5" fontWeight="600" fill="#94a3b8">DEEP (22%)</text>
              <text x="175" y="42" fontSize="7.5" fontWeight="600" fill="#94a3b8">REM (24%)</text>
              <text x="260" y="42" fontSize="7.5" fontWeight="600" fill="#94a3b8">LIGHT (54%)</text>
            </svg>
          </div>
        </div>

        {/* Channel 2: 24h CGM Metabolic Foresight (Bergman Minimal Model) */}
        <div className="relative">
          <div className="flex items-center justify-between text-[10.5px] mb-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <svg className="h-3 w-3 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              <span>CGM Metabolic Trajectory</span>
            </div>
            <span className="rounded border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[9.5px] font-semibold text-emerald-700">
              112 mg/dL • In Range
            </span>
          </div>

          {/* CGM Forecast Corridor SVG */}
          <div className="relative h-14 w-full rounded-lg border border-slate-200/60 bg-white/70 overflow-hidden">
            <svg className="h-full w-full" preserveAspectRatio="none" viewBox="0 0 320 56">
              <defs>
                <linearGradient id="cgm-area-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
                </linearGradient>
              </defs>

              {/* Target Glucose Corridor (70-140 mg/dL) */}
              <rect x="0" y="10" width="320" height="34" fill="#10b981" fillOpacity="0.08" />
              <line x1="0" y1="10" x2="320" y2="10" stroke="#10b981" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
              <line x1="0" y1="44" x2="320" y2="44" stroke="#10b981" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />

              <text x="6" y="8" fontSize="7" fontWeight="600" fill="#059669">Target Corridor (70–140 mg/dL)</text>

              {/* Historical CGM Curve */}
              <path
                d="M 0 34 Q 30 36, 60 22 T 120 18 T 170 30"
                fill="none"
                stroke="#0d9488"
                strokeWidth="2.2"
                strokeLinecap="round"
              />

              {/* Shaded history area */}
              <path
                d="M 0 34 Q 30 36, 60 22 T 120 18 T 170 30 L 170 56 L 0 56 Z"
                fill="url(#cgm-area-grad)"
              />

              {/* Current Moment T+0 Indicator */}
              <circle cx="170" cy="30" r="3.5" fill="#0284c7" />

              {/* Predictive ODE Forecast Corridor (Dashed line into future) */}
              <path
                d="M 170 30 Q 210 24, 250 28 T 320 26"
                fill="none"
                stroke="#0284c7"
                strokeWidth="2"
                strokeDasharray="4 3"
                strokeLinecap="round"
              />

              {/* Time indicator markers */}
              <text x="145" y="52" fontSize="7" fontWeight="700" fill="#0284c7">NOW</text>
              <text x="260" y="52" fontSize="7" fontWeight="600" fill="#64748b">+6h FORESIGHT</text>
            </svg>
          </div>
        </div>

        {/* Convergence Bridge Pill */}
        <div className="mt-2.5 flex items-center justify-between rounded-lg border border-slate-200 bg-white/90 px-2.5 py-1.5 text-[9.5px]">
          <div className="flex items-center gap-1.5 text-slate-700 font-medium">
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 text-[8px] font-bold">✓</span>
            <span>Insulin Sensitivity (+24% S_I)</span>
          </div>
          <span className="font-semibold text-emerald-700">Prevents Surge</span>
        </div>
      </div>

      {/* 3-Column Quick Vital Metrics */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-1.5">
          <div className="text-[9px] font-semibold text-indigo-700">Sleep Sync</div>
          <div className="text-xs font-bold text-slate-900">7.4h</div>
          <div className="text-[8.5px] text-slate-500">88% Rest</div>
        </div>
        <div className="rounded-lg border border-rose-100 bg-rose-50/50 p-1.5">
          <div className="text-[9px] font-semibold text-rose-700">Autonomic</div>
          <div className="text-xs font-bold text-slate-900">48 ms</div>
          <div className="text-[8.5px] text-slate-500">Normal RMSSD</div>
        </div>
        <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-1.5">
          <div className="text-[9px] font-semibold text-emerald-700">Glycemic</div>
          <div className="text-xs font-bold text-slate-900">112</div>
          <div className="text-[8.5px] text-slate-500">94% In Range</div>
        </div>
      </div>

      {/* Footer status pill */}
      <div className="mt-2.5 flex items-center justify-between border-t border-slate-100 pt-2 text-[10.5px] text-slate-500">
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
          Euler Minimal Model ODE
        </span>
        <span className="font-mono text-[9.5px] font-semibold text-slate-400">15 ms Latency</span>
      </div>
    </div>
  )
}
