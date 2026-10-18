// Non-component helpers shared by the pages (kept out of .tsx component files for React Fast Refresh).
import { createContext, useContext, useEffect, useState } from 'react'
import type { Level } from '../api'

// ---------------------------------------------------------------- current patient
export interface PatientCtx { currentId: string; setCurrentId: (id: string) => void }
export const PatientContext = createContext<PatientCtx>({ currentId: 'A', setCurrentId: () => {} })
export const useCurrentPatient = () => useContext(PatientContext)

// ---------------------------------------------------------------- data loading
/** Runs `fn` whenever `deps` change. Loading is derived (no synchronous setState inside the effect). */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [tick, setTick] = useState(0)
  const key = JSON.stringify([...deps, tick])
  const [state, setState] = useState<{ key: string | null; data: T | null; error: string | null }>({
    key: null, data: null, error: null,
  })
  useEffect(() => {
    let alive = true
    fn()
      .then((data) => { if (alive) setState({ key, data, error: null }) })
      .catch((e: Error) => { if (alive) setState({ key, data: null, error: e.message }) })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  const loading = state.key !== key
  return {
    data: loading ? null : state.data,
    error: loading ? null : state.error,
    loading,
    reload: () => setTick((t) => t + 1),
  }
}

// ---------------------------------------------------------------- risk helpers
export const LEVEL: Record<Level, { label: string; text: string; bg: string; ring: string; hex: string }> = {
  critical: { label: 'Critical', text: 'text-red-700', bg: 'bg-red-50', ring: 'ring-red-200', hex: '#dc2626' },
  warning: { label: 'Warning', text: 'text-amber-700', bg: 'bg-amber-50', ring: 'ring-amber-200', hex: '#d97706' },
  stable: { label: 'Stable', text: 'text-emerald-700', bg: 'bg-emerald-50', ring: 'ring-emerald-200', hex: '#059669' },
}

export function levelOf(p: number): Level {
  return p >= 0.75 ? 'critical' : p >= 0.4 ? 'warning' : 'stable'
}

export const pct = (p: number | null | undefined, d = 0) => (p == null ? '–' : `${(p * 100).toFixed(d)}%`)
