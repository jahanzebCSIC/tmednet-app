import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, ZoomControl, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import mpas from '../data/mpas.json'
import mpaYears from '../data/mpa_years.json'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

// Re-triggers Leaflet autoPan after charts have had time to render
function AutoPan() {
  const map = useMap()
  useEffect(() => {
    const id = setTimeout(() => {
      if (map._popup) map._popup._adjustPan()
    }, 120)
    return () => clearTimeout(id)
  }, [map])
  return null
}

// ── Colour helpers ────────────────────────────────────────────────────────────
const CAT_COLOR = { 0:'#5aab6e', 1:'#f0c040', 2:'#e8934a', 3:'#d94f3d', 4:'#8b0000' }

function mhwColor(pct) {
  if (pct === null || pct === undefined) return '#b0b8c4'
  if (pct >= 90) return '#d94f3d'
  if (pct >= 70) return '#e8934a'
  if (pct >= 40) return '#f0c040'
  return '#4db8d8'
}
function catLabel(c) { return ['—','Moderate','Strong','Severe','Extreme'][c] || '—' }

const mpaById = Object.fromEntries(mpas.map(m => [String(m.MAPAMED_ID), m]))

// Pre-build year data lookup (all per-year fields)
const yearDataByName = (() => {
  const map = {}
  for (const r of mpaYears) {
    if (!map[r.NAME]) map[r.NAME] = []
    const cat = r.Max_category || 0
    map[r.NAME].push({
      year:       r.Year,
      cat,
      catDisplay: cat === 0 ? 0.35 : cat,
      sst:        r.SST_summer_mean ?? null,
      n_events:   r.N_events ?? 0,
      days:       r.Total_days ?? 0,
      max_int:    r.Max_intensity ?? null,
      cum_int:    r.Cum_intensity ?? null,
      mean_int:   r.Mean_intensity ?? null,
      cat_name:   r.Max_cat_name ?? null,
    })
  }
  for (const k in map) map[k].sort((a, b) => a.year - b.year)
  return map
})()

// Static year-detail panel — always renders at full height to prevent layout shift
function YearDetailPanel({ d, cols = 3 }) {
  const hasData = !!(d && d.cat)

  // Always render all 6 tiles so the container height never changes
  const fields = [
    ['Categoría',     hasData ? <span style={{ color: CAT_COLOR[d.cat] ?? '#aaa', fontWeight: 700 }}>{d.cat_name || catLabel(d.cat)}</span> : '—'],
    ['Nº eventos',    hasData ? d.n_events : '—'],
    ['Días en MHW',   hasData ? d.days + ' d' : '—'],
    ['Intens. máx.',  hasData && d.max_int  != null ? d.max_int.toFixed(2)  + ' °C' : '—'],
    ['Intens. acum.', hasData && d.cum_int  != null ? d.cum_int.toFixed(1)  + ' °C·d' : '—'],
    ['Intens. media', hasData && d.mean_int != null ? d.mean_int.toFixed(2) + ' °C' : '—'],
  ]

  return (
    <div style={{ position: 'relative' }}>
      {/* Always-rendered grid — sets the stable height */}
      <div style={{ visibility: hasData ? 'visible' : 'hidden' }}>
        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#546e7a', marginBottom: '0.3rem' }}>
          Año {d?.year ?? '—'}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: '0.3rem' }}>
          {fields.map(([k, v]) => (
            <div key={k} style={{ background: '#f0f7fa', borderRadius: 5, padding: '0.25rem 0.4rem' }}>
              <div style={{ fontSize: '0.58rem', color: '#78909c', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{k}</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1a2e3b', marginTop: '0.05rem' }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Overlay placeholder — absolutely positioned so it doesn't affect height */}
      {!hasData && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {!d ? (
            <span style={{ fontSize: '0.68rem', color: '#b0bec5', fontStyle: 'italic', textAlign: 'center', padding: '0 0.5rem' }}>
              Pasa el ratón sobre una barra para ver el detalle del año
            </span>
          ) : (
            <span style={{ fontSize: '0.72rem', color: '#90a4ae', textAlign: 'center' }}>
              <strong style={{ color: '#546e7a' }}>{d.year}</strong> — Sin MHW estival detectada
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// Bar chart + static detail panel (no floating tooltip)
function MhwBarChart({ data, width, useResponsive = false, detailCols = 3 }) {
  const [hovered, setHovered] = useState(null)
  const chart = (
    <BarChart
      width={useResponsive ? undefined : width}
      height={90}
      data={data}
      margin={{ top: 2, right: 6, bottom: 0, left: -18 }}
    >
      <XAxis dataKey="year" tick={{ fontSize: 7 }} interval="preserveStartEnd" />
      <YAxis domain={[0, 4]} tick={{ fontSize: 7 }} ticks={[0, 1, 2, 3, 4]} />
      <Bar dataKey="catDisplay" radius={[2, 2, 0, 0]} cursor="pointer"
        onMouseEnter={(d) => setHovered(d?.payload ?? d)}
        onMouseLeave={() => setHovered(null)}
      >
        {data.map((d, i) => <Cell key={i} fill={d === hovered ? '#1a6b8a' : (CAT_COLOR[d.cat] ?? '#e8e8e8')} />)}
      </Bar>
    </BarChart>
  )
  return (
    <div>
      {useResponsive
        ? <ResponsiveContainer width="100%" height={90}>{chart}</ResponsiveContainer>
        : chart
      }
      <div style={{
        marginTop: '0.4rem',
        background: '#f8fafb', borderRadius: 7,
        padding: '0.45rem 0.6rem', border: '1px solid #e8edf2',
      }}>
        <YearDetailPanel d={hovered} cols={detailCols} />
      </div>
    </div>
  )
}

// ── Popup content ─────────────────────────────────────────────────────────────
function MpaPopupContent({ m }) {
  const yd    = yearDataByName[m.NAME] ?? []
  const sstYd = yd.filter(d => d.sst !== null)
  const hasSst = sstYd.length > 0
  const W = 460

  const trendSegment = useMemo(() => {
    if (!hasSst || m.Warming_trend_per_decade == null) return null
    const xs     = sstYd.map(d => d.year)
    const mid    = xs.reduce((a, b) => a + b, 0) / xs.length
    const ssts   = sstYd.map(d => d.sst)
    const midSST = ssts.reduce((a, b) => a + b, 0) / ssts.length
    const slope  = m.Warming_trend_per_decade / 10
    return [
      { x: xs[0],             y: midSST + slope * (xs[0]             - mid) },
      { x: xs[xs.length - 1], y: midSST + slope * (xs[xs.length - 1] - mid) },
    ]
  }, [hasSst, m, sstYd])

  const stats = [
    { label: 'Co-ocurrencia MHW', value: m.Pct_MHW != null ? m.Pct_MHW + '%' : 'N/D',    color: mhwColor(m.Pct_MHW) },
    { label: 'Categoría máx.',    value: catLabel(m.Max_category_ever),                    color: CAT_COLOR[m.Max_category_ever] ?? '#aaa' },
    { label: 'Intensidad máx.',   value: m.Max_intensity_ever != null ? m.Max_intensity_ever.toFixed(1) + '°C' : 'N/D', color: '#2a96b8' },
    { label: 'Años con datos',    value: m.Years_with_data ?? m.Years_recorded ?? '—',     color: '#6b8091' },
    ...(m.Warming_trend_per_decade != null
      ? [{ label: 'Calentamiento SST', value: (m.Warming_trend_per_decade > 0 ? '+' : '') + m.Warming_trend_per_decade.toFixed(2) + '°C/dec', color: '#e8934a' }]
      : []),
    ...(m.GIS_M_AREA != null
      ? [{ label: 'Área marina', value: m.GIS_M_AREA.toFixed(1) + ' km²', color: '#6b8091' }]
      : []),
  ]

  const sLabel = 'system-ui, sans-serif'

  return (
    <div style={{ width: W, fontFamily: sLabel }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: '0.7rem', paddingBottom: '0.6rem', borderBottom: '1px solid #eee' }}>
        <div style={{ fontWeight: 700, fontSize: '1rem', lineHeight: 1.3, color: '#1a2e3b', marginBottom: '0.25rem' }}>
          {m.NAME}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#6b8091', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span>{m.Country}</span>
          {m.DESIG_ENG && <span style={{ color: '#aaa' }}>·</span>}
          {m.DESIG_ENG && <span>{m.DESIG_ENG}</span>}
          <span style={{
            background: mhwColor(m.Pct_MHW), color: '#fff', borderRadius: 10,
            padding: '0.15rem 0.55rem', fontSize: '0.7rem', fontWeight: 700, marginLeft: 'auto',
          }}>
            {m.Pct_MHW != null ? m.Pct_MHW + '% MHW' : 'Sin SST'}
          </span>
        </div>
      </div>

      {/* ── Key stats grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.45rem', marginBottom: '0.9rem' }}>
        {stats.map(({ label, value, color }) => (
          <div key={label} style={{ background: '#f6fafb', borderRadius: 7, padding: '0.45rem 0.6rem', borderLeft: `3px solid ${color}` }}>
            <div style={{ fontSize: '0.6rem', color: '#888', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.15rem' }}>{label}</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1a2e3b' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* ── Charts ── */}
      {yd.length === 0 ? (
        <div style={{ fontSize: '0.75rem', color: '#aaa', textAlign: 'center', padding: '0.5rem 0' }}>Sin datos temporales disponibles</div>
      ) : (
        <>
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b8091', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.3rem' }}>
            Categoría MHW por año
          </div>
          <MhwBarChart data={yd} width={W} detailCols={3} />

          {hasSst && (
            <>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b8091', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.75rem', marginBottom: '0.3rem' }}>
                SST media estival (jun–sep) °C
              </div>
              <LineChart width={W} height={95} data={sstYd} margin={{ top: 4, right: 6, bottom: 0, left: -18 }}>
                <XAxis dataKey="year" tick={{ fontSize: 8 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 8 }} domain={['auto', 'auto']} />
                <Tooltip formatter={v => `${Number(v).toFixed(2)}°C`} labelFormatter={l => `Año ${l}`} />
                <Line type="monotone" dataKey="sst" dot={false} stroke="#2a96b8" strokeWidth={2} />
                {trendSegment && (
                  <ReferenceLine stroke="#e8934a" strokeDasharray="4 3" strokeWidth={1.8} segment={trendSegment} />
                )}
              </LineChart>
            </>
          )}
        </>
      )}
    </div>
  )
}

// ── MHW filter categories
const MHW_CATS = [
  { id:'all',  label:'Todos',    test: () => true },
  { id:'high', label:'≥ 90%',   test: m => m.Pct_MHW >= 90 },
  { id:'med',  label:'70–90%',  test: m => m.Pct_MHW >= 70 && m.Pct_MHW < 90 },
  { id:'low',  label:'40–70%',  test: m => m.Pct_MHW >= 40 && m.Pct_MHW < 70 },
  { id:'vlow', label:'< 40%',   test: m => m.Pct_MHW !== null && m.Pct_MHW < 40 },
  { id:'none', label:'Sin SST', test: m => m.Pct_MHW === null || m.Pct_MHW === undefined },
]

// ── Polygon styles (display only — no click) ──────────────────────────────────
const polyBorder = (pct, vis) => ({
  fillColor:   mhwColor(pct),
  fillOpacity: vis ? 0.18 : 0,
  color:       mhwColor(pct),
  weight:      vis ? 1.2 : 0,
  opacity:     vis ? 0.65 : 0,
})
const polyFilled = (pct) => ({
  fillColor:   mhwColor(pct),
  fillOpacity: 0.55,
  color:       '#fff',
  weight:      2.5,
  opacity:     1,
})


// ── MapController ─────────────────────────────────────────────────────────────
function MapController({ filter, visibleMpas }) {
  const map = useMap()
  const prevFilter = useRef('all')
  useEffect(() => {
    if (filter === prevFilter.current) return
    prevFilter.current = filter
    const pts = filter === 'all' ? [] : visibleMpas.filter(m => m.Country === filter)
    if (filter === 'all' || !pts.length) {
      map.flyTo([38, 15], 5, { duration: 1 })
    } else {
      const lats = pts.map(m => m.Lat), lons = pts.map(m => m.Lon)
      map.flyToBounds([
        [Math.min(...lats)-0.5, Math.min(...lons)-0.5],
        [Math.max(...lats)+0.5, Math.max(...lons)+0.5],
      ], { padding:[40,40], duration:1 })
    }
  }, [filter, map, visibleMpas])
  return null
}

// ── Polygon display layer (non-interactive) ───────────────────────────────────
function PolygonDisplayLayer({ geoData, visibleIds, selected }) {
  const layerRefs   = useRef({})
  const selectedRef = useRef(null)
  const visibleRef  = useRef(visibleIds)

  useEffect(() => { visibleRef.current = visibleIds }, [visibleIds])

  // Sort: largest area first → at bottom of SVG stack → small AMPs on top
  const sortedData = useMemo(() => {
    if (!geoData) return null
    return {
      ...geoData,
      features: [...geoData.features].sort(
        (a,b) => (b.properties.GIS_M_AREA ?? 0) - (a.properties.GIS_M_AREA ?? 0)
      ),
    }
  }, [geoData])

  useEffect(() => {
    const selId = selected ? String(selected.MAPAMED_ID) : null
    if (selectedRef.current && selectedRef.current !== selId) {
      const layer = layerRefs.current[selectedRef.current]
      if (layer) {
        const vis = visibleRef.current.has(selectedRef.current)
        layer.setStyle(polyBorder(mpaById[selectedRef.current]?.Pct_MHW, vis))
      }
    }
    if (selId && layerRefs.current[selId]) {
      layerRefs.current[selId].setStyle(polyFilled(selected.Pct_MHW))
      layerRefs.current[selId].bringToFront()
    }
    selectedRef.current = selId
    Object.entries(layerRefs.current).forEach(([id, layer]) => {
      if (id === selId) return
      const vis = visibleIds.has(id)
      layer.setStyle(polyBorder(mpaById[id]?.Pct_MHW, vis))
    })
  }, [visibleIds, selected])

  const onEachFeature = useCallback((feature, layer) => {
    const id = String(feature.properties.MAPAMED_ID)
    layerRefs.current[id] = layer
    // Always non-interactive — clicks go to markers on top
    layer.on('add', () => {
      if (layer._path) layer._path.style.pointerEvents = 'none'
      else if (layer._layers) Object.values(layer._layers).forEach(s => { if (s._path) s._path.style.pointerEvents = 'none' })
    })
  }, [])

  const style = useCallback((feature) => {
    const mpa = mpaById[String(feature.properties.MAPAMED_ID)]
    return polyBorder(mpa?.Pct_MHW, true)
  }, [])

  if (!sortedData) return null
  return <GeoJSON key="mpa-poly" data={sortedData} style={style} onEachFeature={onEachFeature} />
}

// ── Sidebar filter pill ───────────────────────────────────────────────────────
function Pill({ active, color, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding:'0.25rem 0.6rem', borderRadius:20, fontSize:'0.72rem', fontWeight:600,
      cursor:'pointer', border: active ? '2px solid transparent' : '1.5px solid var(--sand-200)',
      background: active ? color : 'var(--white)', color: active ? '#fff' : 'var(--ink-60)',
      transition:'all 0.15s',
    }}>{children}</button>
  )
}

// ── Mobile detection hook ─────────────────────────────────────────────────────
function useIsMobile() {
  const [mob, setMob] = useState(() => typeof window !== 'undefined' && window.innerWidth <= 768)
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)')
    const h = (e) => setMob(e.matches)
    mq.addEventListener('change', h)
    return () => mq.removeEventListener('change', h)
  }, [])
  return mob
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function MapPage() {
  const [selected,         setSelected]        = useState(null)
  const [country,          setCountry]         = useState('all')
  const [mhwFilter,        setMhwFilter]       = useState('all')
  const [ampSearch,        setAmpSearch]       = useState('')
  const [geoData,          setGeoData]         = useState(null)
  const [cardExpanded,     setCardExpanded]    = useState(false)
  const [showMobileFilter, setShowMobileFilter] = useState(false)
  const isMobile = useIsMobile()
  const mapRef = useRef(null)

  useEffect(() => {
    import('../data/mpa_polygons.json').then(m => setGeoData(m.default ?? m)).catch(() => {})
  }, [])

  const countries = useMemo(() => ['all', ...new Set(mpas.map(m => m.Country))].sort(), [])

  // Combined visibility: country + MHW filter
  const mhwTest = useMemo(() => MHW_CATS.find(c => c.id === mhwFilter)?.test ?? (() => true), [mhwFilter])

  const visibleMpas = useMemo(() =>
    mpas.filter(m =>
      (country === 'all' || m.Country === country) && mhwTest(m)
    ), [country, mhwTest])

  const visibleIds = useMemo(() => new Set(visibleMpas.map(m => String(m.MAPAMED_ID))), [visibleMpas])

  // AMP options for selector (filtered by country)
  const ampOptions = useMemo(() =>
    mpas
      .filter(m => country === 'all' || m.Country === country)
      .sort((a,b) => a.NAME.localeCompare(b.NAME)), [country])

  // If selected AMP is not visible after filter change, deselect
  useEffect(() => {
    if (selected && !visibleIds.has(String(selected.MAPAMED_ID))) setSelected(null)
  }, [visibleIds, selected])

  const yearsField = mpas[0]?.Years_with_data !== undefined ? 'Years_with_data' : 'Years_recorded'

  const yearData = useMemo(() => {
    if (!selected) return []
    return mpaYears
      .filter(r => r.NAME === selected.NAME)
      .sort((a,b) => a.Year - b.Year)
      .map(r => {
        const cat = r.Max_category || 0
        return {
          year:       r.Year,
          cat,
          catDisplay: cat === 0 ? 0.35 : cat,
          sst:        r.SST_summer_mean ?? null,
          n_events:   r.N_events ?? 0,
          days:       r.Total_days ?? 0,
          max_int:    r.Max_intensity ?? null,
          cum_int:    r.Cum_intensity ?? null,
          mean_int:   r.Mean_intensity ?? null,
          cat_name:   r.Max_cat_name ?? null,
        }
      })
  }, [selected])

  const hasSSTseries = yearData.some(d => d.sst !== null)

  // Drag state for bottom card handle
  const dragState = useRef({ startY: null, dragging: false })

  const onHandleTouchStart = useCallback((e) => {
    dragState.current = { startY: e.touches[0].clientY, dragging: false }
  }, [])

  const onHandleTouchMove = useCallback((e) => {
    if (dragState.current.startY === null) return
    if (Math.abs(e.touches[0].clientY - dragState.current.startY) > 8)
      dragState.current.dragging = true
  }, [])

  const onHandleTouchEnd = useCallback((e) => {
    const { startY, dragging } = dragState.current
    dragState.current = { startY: null, dragging: false }
    if (startY === null) return
    const delta = e.changedTouches[0].clientY - startY
    e.preventDefault()
    if (!dragging || Math.abs(delta) < 15) {
      setCardExpanded(o => !o)   // tap = toggle
    } else if (delta > 30) {
      setCardExpanded(false)     // drag down = collapse
    } else if (delta < -30) {
      setCardExpanded(true)      // drag up = expand
    }
  }, [])

  // When an AMP is selected — open card expanded immediately
  const handleSelect = useCallback((mpa) => {
    setSelected(mpa)
    setCardExpanded(true)
    setShowMobileFilter(false)
  }, [])

  // ── Shared filter controls (used in both desktop sidebar and mobile filter sheet)
  const filterControls = (
    <>
      <label style={{ display:'block', fontSize:'0.72rem', fontWeight:600, color:'var(--ink-60)', textTransform:'uppercase', letterSpacing:'0.04em', marginBottom:'0.25rem' }}>País</label>
      <select className="filter-select" style={{ width:'100%', marginBottom:'0.75rem' }}
        value={country} onChange={e => { setCountry(e.target.value); setSelected(null); setAmpSearch('') }}>
        {countries.map(c => <option key={c} value={c}>{c === 'all' ? 'Todos los países' : c}</option>)}
      </select>
      <label style={{ display:'block', fontSize:'0.72rem', fontWeight:600, color:'var(--ink-60)', textTransform:'uppercase', letterSpacing:'0.04em', marginBottom:'0.25rem' }}>
        AMP <span style={{ fontWeight:400, textTransform:'none' }}>({ampOptions.length})</span>
      </label>
      <select className="filter-select" style={{ width:'100%', marginBottom:'0.75rem' }}
        value={selected ? String(selected.MAPAMED_ID) : ''}
        onChange={e => { const mpa = mpaById[e.target.value]; if (mpa) handleSelect(mpa); else setSelected(null) }}>
        <option value=''>— Seleccionar AMP —</option>
        {ampOptions.map(m => <option key={m.MAPAMED_ID} value={String(m.MAPAMED_ID)}>{m.NAME}</option>)}
      </select>
      <label style={{ display:'block', fontSize:'0.72rem', fontWeight:600, color:'var(--ink-60)', textTransform:'uppercase', letterSpacing:'0.04em', marginBottom:'0.4rem' }}>Co-ocurrencia MHW</label>
      <div style={{ display:'flex', flexWrap:'wrap', gap:'0.3rem' }}>
        {MHW_CATS.map(cat => (
          <Pill key={cat.id} active={mhwFilter === cat.id}
            color={cat.id==='high'?'#d94f3d':cat.id==='med'?'#e8934a':cat.id==='low'?'#c8a020':cat.id==='vlow'?'#2a96b8':cat.id==='none'?'#888':'var(--teal-600)'}
            onClick={() => setMhwFilter(cat.id)}>
            {cat.label}
          </Pill>
        ))}
      </div>
      <div style={{ marginTop:'0.5rem', fontSize:'0.7rem', color:'var(--ink-40)' }}>
        {visibleMpas.length} AMP{visibleMpas.length !== 1 ? 's' : ''} visibles
      </div>
    </>
  )

  return (
    <div className="map-shell">

      {/* ═══════════════ DESKTOP SIDEBAR ═══════════════ */}
      <div className="map-sidebar">
        {/* ── Filtros ── */}
        <div style={{ padding:'0.9rem 1rem', borderBottom:'1px solid var(--sand-200)' }}>
          <div style={{ fontWeight:700, fontSize:'0.9rem', marginBottom:'0.75rem' }}>Filtros</div>
          {filterControls}
        </div>

        {/* ── Leyenda ── */}
        <div style={{ padding:'0.75rem 1rem', borderBottom:'1px solid var(--sand-200)' }}>
          <div style={{ fontSize:'0.7rem', fontWeight:600, color:'var(--ink-60)', marginBottom:'0.4rem', textTransform:'uppercase', letterSpacing:'0.04em' }}>Leyenda</div>
          {[['≥90%','#d94f3d'],['70–90%','#e8934a'],['40–70%','#f0c040'],['<40%','#4db8d8'],['Sin datos','#b0b8c4']].map(([l,c]) => (
            <div key={l} style={{ display:'flex', alignItems:'center', gap:'0.5rem', marginBottom:'0.25rem', fontSize:'0.75rem' }}>
              <div style={{ width:12,height:12,borderRadius:'50%',background:c,flexShrink:0 }}/>
              <span>{l}</span>
            </div>
          ))}
        </div>

        {/* ── AMP detail ── */}
        {selected ? (
          <div style={{ padding:'1rem', flex:1 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'0.65rem' }}>
              <h3 style={{ fontSize:'0.9rem', fontWeight:700, lineHeight:1.3, flex:1 }}>{selected.NAME}</h3>
              <button onClick={() => setSelected(null)} style={{ color:'var(--ink-60)', fontSize:'1.1rem', padding:'0 0.25rem' }}>✕</button>
            </div>
            <div style={{ fontSize:'0.75rem', color:'var(--ink-60)', marginBottom:'0.75rem' }}>
              {selected.Country} · {selected.DESIG_ENG || 'MPA'}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.4rem', marginBottom:'0.9rem' }}>
              {[
                ['Co-ocurrencia MHW', selected.Pct_MHW !== null ? selected.Pct_MHW+'%' : 'N/D'],
                ['Intensidad máx.', selected.Max_intensity_ever != null ? selected.Max_intensity_ever.toFixed(1)+'°C' : 'N/D'],
                ['Años con datos', selected[yearsField] ?? '—'],
                ['Categoría máx.', catLabel(selected.Max_category_ever)],
                ...(selected.Warming_trend_per_decade != null ? [['Calentamiento SST', (selected.Warming_trend_per_decade>0?'+':'')+selected.Warming_trend_per_decade.toFixed(2)+'°C/dec']] : []),
                ...(selected.GIS_M_AREA != null ? [['Área marina', selected.GIS_M_AREA.toFixed(1)+' km²']] : []),
              ].map(([k,v]) => (
                <div key={k} style={{ background:'var(--teal-50)', borderRadius:6, padding:'0.45rem' }}>
                  <div style={{ fontSize:'0.6rem', color:'var(--ink-60)', fontWeight:600, textTransform:'uppercase', letterSpacing:'0.04em' }}>{k}</div>
                  <div style={{ fontSize:'0.85rem', fontWeight:700, color:'var(--teal-700)', marginTop:'0.1rem' }}>{v}</div>
                </div>
              ))}
            </div>

            {yearData.length > 0 && (
              <>
                <div style={{ fontSize:'0.7rem', fontWeight:600, color:'var(--ink-60)', textTransform:'uppercase', letterSpacing:'0.04em', marginBottom:'0.35rem' }}>Categoría MHW por año</div>
                <MhwBarChart data={yearData} useResponsive detailCols={2} />

                {hasSSTseries && (
                  <>
                    <div style={{ fontSize:'0.7rem', fontWeight:600, color:'var(--ink-60)', textTransform:'uppercase', letterSpacing:'0.04em', marginBottom:'0.35rem', marginTop:'0.65rem' }}>SST media estival (jun–sep) °C</div>
                    <ResponsiveContainer width="100%" height={85}>
                      <LineChart data={yearData.filter(d=>d.sst!==null)} margin={{ top:4, right:4, bottom:0, left:-22 }}>
                        <XAxis dataKey="year" tick={{ fontSize:7 }} interval="preserveStartEnd"/>
                        <YAxis tick={{ fontSize:7 }} domain={['auto','auto']}/>
                        <Tooltip formatter={v=>`${v.toFixed(2)}°C`} labelFormatter={l=>`Año ${l}`}/>
                        <Line type="monotone" dataKey="sst" dot={false} stroke="var(--teal-600)" strokeWidth={1.5}/>
                        {selected.Warming_trend_per_decade != null && (
                          <ReferenceLine stroke="#e8934a" strokeDasharray="3 3" strokeWidth={1.5}
                            segment={(() => {
                              const pts = yearData.filter(d=>d.sst!==null)
                              if (!pts.length) return []
                              const xs = pts.map(d=>d.year)
                              const mid = xs.reduce((a,b)=>a+b,0)/xs.length
                              const ssts = pts.map(d=>d.sst)
                              const midSST = ssts.reduce((a,b)=>a+b,0)/ssts.length
                              const slope = selected.Warming_trend_per_decade / 10
                              return [{ x:xs[0], y:midSST+slope*(xs[0]-mid) }, { x:xs[xs.length-1], y:midSST+slope*(xs[xs.length-1]-mid) }]
                            })()}
                          />
                        )}
                      </LineChart>
                    </ResponsiveContainer>
                  </>
                )}
              </>
            )}
          </div>
        ) : (
          <div style={{ padding:'1.5rem 1rem', color:'var(--ink-40)', fontSize:'0.8rem', textAlign:'center' }}>
            Selecciona un AMP desde el mapa o el desplegable
          </div>
        )}
      </div>

      {/* ═══════════════ MAP AREA ═══════════════ */}
      <div className="map-area">

        {/* ── MOBILE TOP BAR — CSS shows on mobile, hides on desktop ── */}
        <div className="mob-top-bar">
          <button
            onClick={() => setShowMobileFilter(o => !o)}
            className={`mob-filter-btn${showMobileFilter ? ' active' : ''}`}
          >
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="2" width="12" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="3" y="6" width="8" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="5" y="10" width="4" height="1.5" rx="0.75" fill="currentColor"/>
            </svg>
            Filtros
          </button>
          {country !== 'all' && (
            <span className="mob-chip">
              {country}
              <span className="mob-chip-x" onClick={() => { setCountry('all'); setSelected(null) }}>✕</span>
            </span>
          )}
          {mhwFilter !== 'all' && (
            <span className="mob-chip secondary">
              {MHW_CATS.find(c=>c.id===mhwFilter)?.label}
              <span className="mob-chip-x" onClick={() => setMhwFilter('all')}>✕</span>
            </span>
          )}
          <span className="mob-count">{visibleMpas.length} AMPs</span>
        </div>

        {/* ── MOBILE FILTER SHEET — rendered by JS, CSS handles position ── */}
        {showMobileFilter && (
          <div className="mob-filter-sheet">
            {filterControls}
            <button className="mob-apply-btn" onClick={() => setShowMobileFilter(false)}>
              Ver en el mapa
            </button>
          </div>
        )}

        {/* ── MOBILE BOTTOM CARD — rendered by JS when AMP selected ── */}
        {selected && (
          <div className="mob-card" style={{ maxHeight: cardExpanded ? '75vh' : '7rem' }}>
            <div
              className="mob-card-handle"
              onTouchStart={onHandleTouchStart}
              onTouchMove={onHandleTouchMove}
              onTouchEnd={onHandleTouchEnd}
              onClick={() => setCardExpanded(o => !o)}
            >
              <div className="mob-card-bar" />
              <div className="mob-card-header">
                <div className="mob-card-dot" style={{ background: mhwColor(selected.Pct_MHW) }} />
                <div className="mob-card-name">{selected.NAME}</div>
                <span className="mob-card-badge" style={{ background: mhwColor(selected.Pct_MHW) }}>
                  {selected.Pct_MHW != null ? selected.Pct_MHW+'%' : 'Sin SST'}
                </span>
                <span className="mob-card-chevron">{cardExpanded ? '▼' : '▲'}</span>
              </div>
            </div>
            {cardExpanded && (
              <div className="mob-card-body">
                <div className="mob-stats-grid">
                  {[
                    ['Categoría máx.', catLabel(selected.Max_category_ever)],
                    ['Intensidad máx.', selected.Max_intensity_ever != null ? selected.Max_intensity_ever.toFixed(1)+'°C' : 'N/D'],
                    ['Años con datos', selected[yearsField] ?? '—'],
                    ['Calentamiento', selected.Warming_trend_per_decade != null ? (selected.Warming_trend_per_decade>0?'+':'')+selected.Warming_trend_per_decade.toFixed(2)+'°C/dec' : 'N/D'],
                  ].map(([k,v]) => (
                    <div key={k} className="mob-stat-tile">
                      <div className="mob-stat-label">{k}</div>
                      <div className="mob-stat-value">{v}</div>
                    </div>
                  ))}
                </div>
                {yearData.length > 0 && (
                  <>
                    <div className="mob-chart-label">Categoría MHW por año</div>
                    <MhwBarChart data={yearData} useResponsive detailCols={2} />
                    {hasSSTseries && (
                      <>
                        <div className="mob-chart-label" style={{ marginTop:'0.65rem' }}>SST media estival (jun–sep) °C</div>
                        <ResponsiveContainer width="100%" height={90}>
                          <LineChart data={yearData.filter(d=>d.sst!==null)} margin={{ top:4, right:4, bottom:0, left:-22 }}>
                            <XAxis dataKey="year" tick={{ fontSize:7 }} interval="preserveStartEnd"/>
                            <YAxis tick={{ fontSize:7 }} domain={['auto','auto']}/>
                            <Tooltip formatter={v=>`${v.toFixed(2)}°C`} labelFormatter={l=>`Año ${l}`}/>
                            <Line type="monotone" dataKey="sst" dot={false} stroke="var(--teal-600)" strokeWidth={1.5}/>
                          </LineChart>
                        </ResponsiveContainer>
                      </>
                    )}
                  </>
                )}
                <button className="mob-card-close" onClick={() => setSelected(null)}>Cerrar</button>
              </div>
            )}
          </div>
        )}

        {/* ── MAP ── */}
        <MapContainer center={[38,15]} zoom={5} style={{ height:'100%', width:'100%' }} zoomControl={false}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            maxZoom={19}
          />
          <ZoomControl position="bottomright" />
          <MapController filter={country} visibleMpas={visibleMpas}/>

          {geoData && (
            <PolygonDisplayLayer geoData={geoData} visibleIds={visibleIds} selected={selected}/>
          )}

          {selected && <FlyToSelected selected={selected} geoData={geoData}/>}

          {visibleMpas.map(m => {
            const isSel = String(selected?.MAPAMED_ID) === String(m.MAPAMED_ID)
            return (
              <CircleMarker
                key={m.MAPAMED_ID ?? m.NAME}
                center={[m.Lat, m.Lon]}
                radius={isSel ? 11 : 7}
                pathOptions={{
                  fillColor:   mhwColor(m.Pct_MHW),
                  fillOpacity: 1,
                  color:       isSel ? '#fff' : 'rgba(0,0,0,0.3)',
                  weight:      isSel ? 3 : 1.5,
                  opacity:     1,
                }}
                eventHandlers={{
                  click: () => handleSelect(m),
                  mouseover: (e) => { if (!isSel) e.target.setStyle({ radius:10, weight:2.5, color:'#fff' }) },
                  mouseout:  (e) => { if (!isSel) e.target.setStyle({ radius:7, weight:1.5, color:'rgba(0,0,0,0.3)' }) },
                }}
              >
                {window.innerWidth > 768 && (
                  <Popup
                    minWidth={488} maxWidth={488} className="mpa-popup"
                    autoPan={true}
                    autoPanPaddingTopLeft={[10, 80]}
                    autoPanPaddingBottomRight={[10, 30]}
                  >
                    <AutoPan />
                    <MpaPopupContent m={m} />
                  </Popup>
                )}
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>
    </div>
  )
}

// Flies to the selected AMP polygon bounds when selection changes
function FlyToSelected({ selected, geoData }) {
  const map = useMap()
  const prevId = useRef(null)
  useEffect(() => {
    const id = selected ? String(selected.MAPAMED_ID) : null
    if (!id || id === prevId.current) return
    prevId.current = id
    if (!geoData) {
      // No polygon data: fly to centroid
      map.flyTo([selected.Lat, selected.Lon], 11, { duration: 0.8 })
      return
    }
    const feat = geoData.features?.find(f => String(f.properties.MAPAMED_ID) === id)
    if (!feat) {
      map.flyTo([selected.Lat, selected.Lon], 11, { duration: 0.8 })
      return
    }
    // Compute bounds from GeoJSON feature directly (no Leaflet layer needed)
    try {
      const coords = extractCoords(feat.geometry)
      if (!coords.length) return
      const lats = coords.map(c => c[1]), lons = coords.map(c => c[0])
      const bounds = [[Math.min(...lats)-0.05, Math.min(...lons)-0.05],[Math.max(...lats)+0.05, Math.max(...lons)+0.05]]
      map.flyToBounds(bounds, { padding:[50,50], maxZoom:14, duration:0.8 })
    } catch (_) {
      map.flyTo([selected.Lat, selected.Lon], 11, { duration: 0.8 })
    }
  }, [selected, map, geoData])
  return null
}

function extractCoords(geom) {
  if (!geom) return []
  if (geom.type === 'Polygon') return geom.coordinates.flat()
  if (geom.type === 'MultiPolygon') return geom.coordinates.flat(2)
  return []
}
