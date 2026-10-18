import { BrowserRouter, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { PatientProvider, SimulatedBadge } from './components/ui'
import { useCurrentPatient } from './lib/state'
import PatientsPage from './pages/PatientsPage'
import OverviewPage from './pages/OverviewPage'
import TrendsPage from './pages/TrendsPage'
import WhatIfPage from './pages/WhatIfPage'
import AboutPage from './pages/AboutPage'

const PERSONAS = [
  { id: 'A', label: 'A', title: 'Persona A – 54M diabetic executive, 4 short nights' },
  { id: 'B', label: 'B', title: 'Persona B – 41F shift worker, hidden sleep apnea' },
  { id: 'C', label: 'C', title: 'Persona C – 27M healthy runner, one bad night' },
]

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden>
        <rect width="32" height="32" rx="8" fill="#2554e8" />
        <path d="M20.5 7.5a9 9 0 1 0 4 15.9A10 10 0 0 1 20.5 7.5z" fill="#fff" />
        <path d="M6 17h4l2-4 3 8 2-4h3" stroke="#2554e8" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="leading-tight">
        <div className="text-base font-extrabold tracking-tight text-slate-900">SleepTwin</div>
        <div className="hidden text-[11px] text-slate-500 sm:block">Sleep-driven cardiometabolic digital twin</div>
      </div>
    </div>
  )
}

function safeDecode(s: string) {
  try { return decodeURIComponent(s) } catch { return s }
}

function Header() {
  const { currentId: storedId, setCurrentId } = useCurrentPatient()
  const nav = useNavigate()
  const loc = useLocation()
  // the URL is the source of truth on patient pages (no flash of the previously selected patient)
  const routeId = loc.pathname.match(/^\/patients\/([^/]+)/)?.[1]
  const currentId = routeId ? safeDecode(routeId) : storedId
  const links = [
    { to: '/', label: 'Patients', end: true },
    { to: `/patients/${currentId}`, label: 'Overview', end: true },
    { to: `/patients/${currentId}/trends`, label: 'Trends' },
    { to: `/patients/${currentId}/what-if`, label: 'What-If' },
    { to: '/about', label: 'How It Works' },
  ]
  const switchTo = (id: string) => {
    setCurrentId(id)
    const m = loc.pathname.match(/^\/patients\/[^/]+(\/.*)?$/)
    nav(`/patients/${id}${m && m[1] ? m[1] : ''}`)
  }
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <NavLink to="/"><Logo /></NavLink>
        <nav className="order-3 flex w-full gap-1 overflow-x-auto md:order-0 md:w-auto">
          {links.map((l) => (
            <NavLink key={l.label} to={l.to} end={l.end}
              className={({ isActive }) => `tab whitespace-nowrap ${isActive ? 'tab-active' : ''}`}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1" role="group" aria-label="Demo personas">
            <span className="px-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Persona</span>
            {PERSONAS.map((p) => (
              <button key={p.id} title={p.title} onClick={() => switchTo(p.id)}
                className={`h-7 w-7 rounded-lg text-sm font-bold transition ${currentId === p.id ? 'bg-accent-600 text-white shadow-sm' : 'text-slate-700 hover:bg-white'}`}>
                {p.label}
              </button>
            ))}
          </div>
          <SimulatedBadge />
        </div>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <PatientProvider>
        <div className="min-h-screen bg-white">
          <Header />
          <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
            <Routes>
              <Route path="/" element={<PatientsPage />} />
              <Route path="/patients/:id" element={<OverviewPage />} />
              <Route path="/patients/:id/trends" element={<TrendsPage />} />
              <Route path="/patients/:id/what-if" element={<WhatIfPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="*" element={<div className="py-24 text-center text-slate-500">Page not found.</div>} />
            </Routes>
          </main>
          <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
            SleepTwin by Team WeBareBears, PCCOE · Research prototype · Model-based projection for clinical decision support · All patient data is simulated · MIT licensed
          </footer>
        </div>
      </PatientProvider>
    </BrowserRouter>
  )
}
