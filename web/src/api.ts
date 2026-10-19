// Typed client for the frozen SleepTwin API contract (plan Section 8).
// Set VITE_USE_MOCKS=1 to develop against the frozen mock JSON in public/mock (persona A only).

export type Level = 'critical' | 'warning' | 'stable'

export interface PatientRow {
  id: string
  name: string
  age: number
  sex: string
  conditions: string[]
  risk: number
  bp_risk: number
  risk_level: Level
  spike_2h_risk: number | null
  spike_2h_alert: boolean
  top_reason: string
  persona: string | null
}

export interface Reason { text: string; impact: number; kind?: 'driver' | 'modifier' | 'protective' | 'noted' }

export interface Lab { name: string; value: number | null; prior: number | null; unit: string; date: string; prior_date: string }

export interface PatientDetail {
  id: string
  persona: string | null
  profile: {
    demographics: { name: string; age: number; sex: string; bmi: number; waist_cm: number; city: string }
    conditions: string[]
    diagnoses: { name: string; year: number | null; active: boolean }[]
    labs: Lab[]
    medications: string[]
    genetic_markers: {
      simulated: boolean
      prs_t2d: number
      tcf7l2_risk_alleles: number
      mtnr1b_risk_allele: number
      notes: Record<string, string>
    }
  }
  risk: number
  bp_risk: number
  risk_level: Level
  glucose_level: Level
  bp_level: Level
  reasons: Reason[]
  bp_reasons: Reason[]
  spike_2h: {
    risk: number | null
    minutes_ahead: number | null
    alert: boolean
    current_glucose: number | null
    trend_mg_dl_per_min: number | null
    reasons: string[]
    as_of?: string
  }
  masking: { on_beta_blocker: boolean; flagged: boolean; hrv_change_pct: number | null; rhr_delta: number | null; text: string } | null
  apnea_flag: { odi_7d: number; tst_7d: number; diagnosed: boolean; text: string } | null
  data_quality: { level: 'good' | 'low'; missing_nights_7d: number; cgm_missing_pct_24h: number }
  baseline_glucose?: {
    usual_mean: number | null
    usual_sd: number | null
    fasting: number | null
    fasting_prior: number | null
    target_range: [number, number]
  }
  forecast_for: string
  disclaimer: string
  simulated: boolean
}

export type Band = [number | null, number | null]

export interface TrendDay {
  date: string
  day: number
  tst: number | null
  tst_band: Band
  hrv: number | null
  hrv_band: Band
  rhr: number | null
  rhr_band: Band
  odi: number | null
  odi_band: Band
  steps: number | null
  steps_band: Band
  efficiency: number | null
  deep_pct: number | null
  rem_pct: number | null
  waso: number | null
  tir: number | null
  cgm_peak: number | null
  missing: boolean
  partial: boolean
}

export interface Trends {
  id: string
  days: TrendDay[]
  baseline_days: number
  personal_normal: Record<string, { mean: number; sd: number }>
  hypnogram: { date: string; epoch_min: number; stages: { t: string; stage: 'Wake' | 'Light' | 'Deep' | 'REM' }[]; missing: boolean }
  cgm_48h: { t: string; glucose: number | null }[]
  cgm_target: [number, number]
}

export interface WhatIfInput { sleep_hours: number; bedtime_shift_h: number; cpap: boolean; nights: number }

export interface WhatIfResult {
  id: string
  inputs: WhatIfInput
  risk_before: number
  risk_after: number
  bp_before: number
  bp_after: number
  level_before: Level
  level_after: Level
  glucose_before: number[]
  glucose_after: number[]
  peak_before: number
  peak_after: number
  si_change_pct: number
  reasons_after: Reason[]
  bp_reasons_after: Reason[]
  current_night: { sleep_hours: number | null; bedtime_shift_h: number | null; odi: number | null; usual_sleep_hours: number | null }
  compute_ms: number
}

export interface TierMetrics {
  auroc: number
  auprc: number
  prevalence: number
  sensitivity: number
  specificity: number
  false_alerts_per_patient_week: number
  threshold: number
}

export interface TargetResult {
  ehr_only: TierMetrics
  wearables_only: TierMetrics
  fused: TierMetrics
  t2d_subgroup?: Record<string, number>
  interpretation: string
}

export interface ModelSummary {
  nextday: {
    n_patients: number
    n_rows: number
    prediction_days: string
    cv: string
    glucose_event_24h: TargetResult
    bp_event: TargetResult
    personas: Record<string, { glucose_risk: number; bp_risk: number }>
    top_features_glucose: Record<string, number>
  } | null
  spike_2h: {
    n_samples: number
    n_patients: number
    event_rate: number
    auroc: number
    auprc: number
    threshold: number
    sensitivity: number
    false_alerts_per_patient_week: number
    episodes: number
    episodes_warned: number
    episode_recall: number
    median_lead_min: number
    iqr_lead_min: [number, number]
    trend_only_auroc: number
  } | null
  lifesnaps_validation: {
    available: boolean
    n_users: number
    n_nights: number
    n_short_nights: number
    definition: string
    rhr_z_short_mean: number
    rhr_z_normal_mean: number
    hrv_z_short_mean: number
    hrv_z_normal_mean: number
    rhr_paired_diff_median: number
    hrv_paired_diff_median: number
    rhr_users_higher_after_short_pct: number
    hrv_users_lower_after_short_pct: number
    rhr_wilcoxon_p: number
    hrv_wilcoxon_p: number
    interpretation: string
    boxplot: { rhr: { short: number[]; normal: number[] }; hrv: { short: number[]; normal: number[] }; percentiles: number[] }
  } | null
  data_card: Record<string, unknown>
  disclaimer: string
}

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === '1'

async function get<T>(path: string, mock?: string): Promise<T> {
  if (USE_MOCKS && mock) {
    const r = await fetch(`/mock/${mock}`)
    return r.json() as Promise<T>
  }
  const r = await fetch(path)
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new Error(body.detail || `${r.status} ${r.statusText}`)
  }
  return r.json() as Promise<T>
}

export const api = {
  patients: () => get<PatientRow[]>('/api/patients', 'patients.json'),
  patient: (id: string) => get<PatientDetail>(`/api/patients/${encodeURIComponent(id)}`, 'patient_A.json'),
  trends: (id: string) => get<Trends>(`/api/patients/${encodeURIComponent(id)}/trends`, 'trends_A.json'),
  summary: () => get<ModelSummary>('/api/model/summary', 'model_summary.json'),
  whatIf: async (id: string, body: WhatIfInput): Promise<WhatIfResult> => {
    if (USE_MOCKS) return (await fetch('/mock/what_if_A.json')).json()
    const r = await fetch(`/api/patients/${encodeURIComponent(id)}/what-if`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  },
}
