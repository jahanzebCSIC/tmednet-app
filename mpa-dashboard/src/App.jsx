import { useState } from 'react'
import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import MapPage from './pages/MapPage'
import MPAsPage from './pages/MPAsPage'
import Methodology from './pages/Methodology'
import './App.css'

const NAV = [
  { to: '/home',        label: 'Home' },
  { to: '/map',         label: 'Mapa' },
  { to: '/mpas',        label: 'AMPs' },
  { to: '/methodology', label: 'Metodología' },
]

function Navbar() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  // Close menu on navigation
  const close = () => setOpen(false)

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <span className="brand-dot" />
          <span className="brand-title">MPA<span className="brand-accent">·</span>MHW</span>
          <span className="brand-sub">Mediterranean</span>
        </div>

        {/* Desktop links */}
        <ul className={`navbar-links${open ? ' open' : ''}`}>
          {NAV.map(({ to, label }) => (
            <li key={to}>
              <NavLink to={to} onClick={close}
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                {label}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Mobile hamburger */}
        <button className={`nav-hamburger${open ? ' open' : ''}`}
          onClick={() => setOpen(o => !o)}
          aria-label="Menú">
          <span /><span /><span />
        </button>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<Home />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/mpas" element={<MPAsPage />} />
          <Route path="/methodology" element={<Methodology />} />
        </Routes>
      </main>
    </div>
  )
}
