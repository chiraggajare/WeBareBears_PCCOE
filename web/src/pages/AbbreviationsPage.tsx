import { useMemo, useState } from 'react'
import { Card, Disclaimer, Empty, PageTitle } from '../components/ui'

export interface AbbreviationItem {
  abbr: string
  fullTerm: string
  category: 'Sleep & Wearables' | 'Glucose & Metabolism' | 'Cardiovascular & Labs' | 'Genetics & ML'
  description: string
}

export const ABBREVIATIONS: AbbreviationItem[] = [
  // Sleep & Wearables
  {
    abbr: 'TST',
    fullTerm: 'Total Sleep Time',
    category: 'Sleep & Wearables',
    description: 'Total hours/minutes of sleep scored in a night. Used to calculate weighted 7-night sleep debt.',
  },
  {
    abbr: 'WASO',
    fullTerm: 'Wake After Sleep Onset',
    category: 'Sleep & Wearables',
    description: 'Minutes spent awake between sleep onset and final morning awakening; reflects sleep fragmentation.',
  },
  {
    abbr: 'REM',
    fullTerm: 'Rapid Eye Movement',
    category: 'Sleep & Wearables',
    description: 'The sleep stage associated with dreaming and memory consolidation, tracked in the hypnogram.',
  },
  {
    abbr: 'ODI',
    fullTerm: 'Oxygen Desaturation Index',
    category: 'Sleep & Wearables',
    description: 'Number of oxygen desaturation dips (≥ 3–4%) per hour of sleep. Values ≥ 15/h indicate sleep apnea risk.',
  },
  {
    abbr: 'HRV',
    fullTerm: 'Heart Rate Variability',
    category: 'Sleep & Wearables',
    description: 'Variation in time intervals between consecutive heartbeats; drops under autonomic strain and stress.',
  },
  {
    abbr: 'RMSSD',
    fullTerm: 'Root Mean Square of Successive Differences',
    category: 'Sleep & Wearables',
    description: 'The standard time-domain metric (in milliseconds) used by SleepTwin to quantify nightly HRV.',
  },
  {
    abbr: 'RHR',
    fullTerm: 'Resting Heart Rate',
    category: 'Sleep & Wearables',
    description: 'Lowest sustained heart rate during rest/sleep (in beats per minute, bpm).',
  },
  {
    abbr: 'CPAP',
    fullTerm: 'Continuous Positive Airway Pressure',
    category: 'Sleep & Wearables',
    description: 'Therapy device preventing airway collapse in sleep apnea; modeled in What-If (reduces ODI by 80%).',
  },

  // Glucose & Metabolism
  {
    abbr: 'CGM',
    fullTerm: 'Continuous Glucose Monitoring / Monitor',
    category: 'Glucose & Metabolism',
    description: 'Sensor reading interstitial glucose every 5 minutes continuously over 24-hour cycles.',
  },
  {
    abbr: 'TIR',
    fullTerm: 'Time in Range',
    category: 'Glucose & Metabolism',
    description: 'Percentage of the day spent within the safe target glucose range (70–180 mg/dL).',
  },
  {
    abbr: 'SI',
    fullTerm: 'Insulin Sensitivity Index',
    category: 'Glucose & Metabolism',
    description: 'Physiological parameter from the Bergman minimal model; drops sharply (~25%) following accumulated sleep debt.',
  },
  {
    abbr: 'HbA1c',
    fullTerm: 'Hemoglobin A1c (Glycated Hemoglobin)',
    category: 'Glucose & Metabolism',
    description: 'Key blood test indicating average blood sugar over the previous 2 to 3 months (target < 7% for diabetics).',
  },
  {
    abbr: 'T2D',
    fullTerm: 'Type 2 Diabetes Mellitus',
    category: 'Glucose & Metabolism',
    description: 'Chronic metabolic disorder characterized by high blood glucose and insulin resistance.',
  },

  // Cardiovascular & Labs
  {
    abbr: 'BP',
    fullTerm: 'Blood Pressure',
    category: 'Cardiovascular & Labs',
    description: 'Vascular pressure measured in mmHg, tracked for morning surges and clinical baseline comparisons.',
  },
  {
    abbr: 'SBP',
    fullTerm: 'Systolic Blood Pressure',
    category: 'Cardiovascular & Labs',
    description: 'Peak arterial pressure during heart contraction; morning SBP > 145 mmHg is a key alert trigger.',
  },
  {
    abbr: 'DBP',
    fullTerm: 'Diastolic Blood Pressure',
    category: 'Cardiovascular & Labs',
    description: 'Resting arterial pressure between heart contractions (in mmHg).',
  },
  {
    abbr: 'HTN',
    fullTerm: 'Hypertension',
    category: 'Cardiovascular & Labs',
    description: 'High blood pressure diagnosis; a core comorbidity monitored in SleepTwin alongside T2D.',
  },
  {
    abbr: 'OSA',
    fullTerm: 'Obstructive Sleep Apnea',
    category: 'Cardiovascular & Labs',
    description: 'Sleep disorder involving repeated upper airway collapse leading to nocturnal hypoxia and BP surges.',
  },
  {
    abbr: 'eGFR',
    fullTerm: 'Estimated Glomerular Filtration Rate',
    category: 'Cardiovascular & Labs',
    description: 'Kidney filtration indicator in mL/min/1.73m² (calculated via CKD-EPI equation in EHR labs).',
  },
  {
    abbr: 'LDL',
    fullTerm: 'Low-Density Lipoprotein Cholesterol',
    category: 'Cardiovascular & Labs',
    description: 'Lipid profile component ("bad cholesterol"); tracked in EHR laboratory records.',
  },
  {
    abbr: 'HDL',
    fullTerm: 'High-Density Lipoprotein Cholesterol',
    category: 'Cardiovascular & Labs',
    description: 'Protective lipid profile component ("good cholesterol"); tracked in EHR laboratory records.',
  },
  {
    abbr: 'BMI',
    fullTerm: 'Body Mass Index',
    category: 'Cardiovascular & Labs',
    description: 'Anthropometric measure (kg/m²) computed from height and weight; correlates with apnea and diabetes risk.',
  },
  {
    abbr: 'SGLT2i',
    fullTerm: 'Sodium-Glucose Cotransporter-2 Inhibitor',
    category: 'Cardiovascular & Labs',
    description: 'Class of diabetes medications promoting renal glucose excretion (e.g. empagliflozin).',
  },
  {
    abbr: 'ACEi',
    fullTerm: 'Angiotensin-Converting Enzyme Inhibitor',
    category: 'Cardiovascular & Labs',
    description: 'Class of blood pressure medications relaxing veins and arteries (e.g. lisinopril).',
  },

  // Genetics & ML
  {
    abbr: 'TCF7L2',
    fullTerm: 'Transcription Factor 7-Like 2',
    category: 'Genetics & ML',
    description: 'Major diabetes susceptibility gene (rs7903146 variant); modulates pancreatic beta-cell insulin secretion.',
  },
  {
    abbr: 'MTNR1B',
    fullTerm: 'Melatonin Receptor 1B',
    category: 'Genetics & ML',
    description: 'Circadian-linked gene (rs10830963 variant); carriers experience impaired glucose tolerance with late-night eating.',
  },
  {
    abbr: 'PRS',
    fullTerm: 'Polygenic Risk Score',
    category: 'Genetics & ML',
    description: 'Summarized genetic predisposition score expressed in standard deviations from the population mean.',
  },
  {
    abbr: 'SHAP',
    fullTerm: 'SHapley Additive exPlanations',
    category: 'Genetics & ML',
    description: 'Game-theoretic explainability technique used by SleepTwin to rank clinical reasons behind each risk score.',
  },
  {
    abbr: 'AUROC',
    fullTerm: 'Area Under Receiver Operating Characteristic',
    category: 'Genetics & ML',
    description: 'Classification metric measuring discrimination ability across all threshold trade-offs (0.5 = random, 1.0 = perfect).',
  },
  {
    abbr: 'AUPRC',
    fullTerm: 'Area Under Precision-Recall Curve',
    category: 'Genetics & ML',
    description: 'Evaluation metric particularly informative for imbalanced clinical event prediction.',
  },
  {
    abbr: 'EHR',
    fullTerm: 'Electronic Health Record',
    category: 'Genetics & ML',
    description: 'Digital longitudinal patient health records encompassing medical history, diagnoses, medications, and labs.',
  },
  {
    abbr: 'NHANES',
    fullTerm: 'National Health and Nutrition Examination Survey',
    category: 'Genetics & ML',
    description: 'CDC public survey dataset used to realistically correlate clinical and metabolic variables in simulated patients.',
  },
  {
    abbr: 'IQR',
    fullTerm: 'Interquartile Range',
    category: 'Genetics & ML',
    description: 'Statistical spread between the 25th and 75th percentiles (middle 50% of the distribution).',
  },
  {
    abbr: 'SD',
    fullTerm: 'Standard Deviation',
    category: 'Genetics & ML',
    description: 'Measure of dispersion; used in the baseline period (days 1–14) to define each patient’s personal normal band (± 1 SD).',
  },
]

const CATEGORIES = ['All', 'Sleep & Wearables', 'Glucose & Metabolism', 'Cardiovascular & Labs', 'Genetics & ML'] as const
type CategoryFilter = (typeof CATEGORIES)[number]

const CATEGORY_CHIPS: Record<AbbreviationItem['category'], string> = {
  'Sleep & Wearables': 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200',
  'Glucose & Metabolism': 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  'Cardiovascular & Labs': 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  'Genetics & ML': 'bg-violet-50 text-violet-700 ring-1 ring-violet-200',
}

export default function AbbreviationsPage() {
  const [q, setQ] = useState('')
  const [category, setCategory] = useState<CategoryFilter>('All')

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase()
    return ABBREVIATIONS.filter((item) => {
      const matchesCat = category === 'All' || item.category === category
      if (!matchesCat) return false
      if (!s) return true
      return (
        item.abbr.toLowerCase().includes(s) ||
        item.fullTerm.toLowerCase().includes(s) ||
        item.description.toLowerCase().includes(s)
      )
    })
  }, [q, category])

  return (
    <div className="space-y-6">
      <PageTitle
        title="Abbreviations & Glossary"
        sub="A quick clinical and technical reference for all abbreviations, metrics, and acronyms used across SleepTwin."
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-sm">
          <svg
            className="absolute left-3 top-2.5 text-slate-400"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search abbreviation, term or meaning…"
            className="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm outline-hidden focus:border-accent-500 focus:ring-2 focus:ring-accent-100"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`tab ${category === c ? 'tab-active' : ''}`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Table Card */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Abbreviation</th>
                <th className="px-4 py-3">Full Term</th>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Clinical Context & Usage in SleepTwin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((item) => (
                <tr key={item.abbr} className="hover:bg-slate-50/60 transition-colors">
                  <td className="whitespace-nowrap px-4 py-3">
                    <span className="font-mono text-base font-bold text-slate-900">{item.abbr}</span>
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{item.fullTerm}</td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span className={`chip ${CATEGORY_CHIPS[item.category]}`}>
                      {item.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 leading-relaxed">{item.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <Empty>No abbreviations match “{q}” in category “{category}”.</Empty>
          )}
        </div>
      </Card>

      <div className="text-right text-xs text-slate-400">
        Showing {filtered.length} of {ABBREVIATIONS.length} terms
      </div>

      <Disclaimer />
    </div>
  )
}
