import { useState, useMemo } from 'react'
import mpas from '../data/mpas.json'

const COUNTRY_FLAGS = {
  Spain:'🇪🇸', Italy:'🇮🇹', France:'🇫🇷', Greece:'🇬🇷',
  Croatia:'🇭🇷', Tunisia:'🇹🇳', Algeria:'🇩🇿', Cyprus:'🇨🇾',
  Israel:'🇮🇱', Morocco:'🇲🇦', Malta:'🇲🇹', Turkey:'🇹🇷',
}

function PctBar({ value }) {
  if (value === null || value === undefined) return <span style={{color:'var(--ink-60)',fontSize:'0.8rem'}}>N/D</span>
  const color = value >= 90 ? '#d94f3d' : value >= 70 ? '#e8934a' : value >= 40 ? '#f0c040' : '#4db8d8'
  return (
    <div style={{display:'flex',alignItems:'center',gap:'0.5rem'}}>
      <div style={{width:80,height:8,background:'var(--sand-200)',borderRadius:4,overflow:'hidden'}}>
        <div style={{width:`${value}%`,height:'100%',background:color,borderRadius:4}}/>
      </div>
      <span style={{fontVariantNumeric:'tabular-nums',fontSize:'0.875rem',fontWeight:600,color}}>{value}%</span>
    </div>
  )
}

function CatBadge({ cat }) {
  if (!cat) return <span className="badge badge-none">—</span>
  const c = Math.round(cat)
  if (c >= 3) return <span className="badge badge-severe">Severe</span>
  if (c === 2) return <span className="badge badge-strong">Strong</span>
  if (c === 1) return <span className="badge badge-moderate">Moderate</span>
  return <span className="badge badge-none">—</span>
}

const DESIG_TYPES = ['all', 'National', 'International', 'Regional', 'European']

export default function MPAsPage() {
  const [search, setSearch]     = useState('')
  const [country, setCountry]   = useState('all')
  const [desigType, setDesigType] = useState('all')
  const [sortCol, setSortCol]   = useState('Pct_MHW')
  const [sortDir, setSortDir]   = useState('desc')

  const countries = useMemo(() => ['all', ...new Set(mpas.map(m=>m.Country))].sort(), [])

  // Years field — new data has Years_with_data, old has Years_recorded
  const yearsField = mpas[0]?.Years_with_data !== undefined ? 'Years_with_data' : 'Years_recorded'

  const filtered = useMemo(() => {
    let data = mpas
    if (country !== 'all') data = data.filter(m=>m.Country===country)
    if (desigType !== 'all') data = data.filter(m=>m.DESIG_TYPE===desigType)
    if (search) {
      const q = search.toLowerCase()
      data = data.filter(m=>
        m.NAME.toLowerCase().includes(q) ||
        m.Country.toLowerCase().includes(q) ||
        (m.DESIG_ENG||'').toLowerCase().includes(q)
      )
    }
    return [...data].sort((a,b)=>{
      const av = a[sortCol] ?? -Infinity, bv = b[sortCol] ?? -Infinity
      return sortDir === 'asc' ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1)
    })
  }, [search, country, desigType, sortCol, sortDir])

  const toggleSort = col => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('desc') }
  }

  const th = (col, label) => (
    <th onClick={()=>toggleSort(col)} style={{cursor:'pointer',userSelect:'none',whiteSpace:'nowrap'}}>
      {label} {sortCol===col ? (sortDir==='asc'?'↑':'↓') : <span style={{opacity:.3}}>↕</span>}
    </th>
  )

  // Trend field
  const hasTrend = mpas.some(m => m.Warming_trend_per_decade !== null && m.Warming_trend_per_decade !== undefined)

  return (
    <div className="page">
      <h1 style={{fontFamily:"'DM Serif Display',serif",fontSize:'1.8rem',marginBottom:'0.5rem'}}>
        Áreas Marinas Protegidas
      </h1>
      <p style={{color:'var(--ink-60)',marginBottom:'1.5rem'}}>
        {filtered.length} de {mpas.length} AMPs · Haz clic en las columnas para ordenar
      </p>

      <div className="filter-bar" style={{flexWrap:'wrap',gap:'0.5rem'}}>
        <input
          className="search-input"
          placeholder="Buscar por nombre, país o designación…"
          value={search}
          onChange={e=>setSearch(e.target.value)}
          style={{flex:'1 1 200px'}}
        />
        <select className="filter-select" value={country} onChange={e=>setCountry(e.target.value)}>
          {countries.map(c=><option key={c} value={c}>{c==='all'?'Todos los países':c}</option>)}
        </select>
        <select className="filter-select" value={desigType} onChange={e=>setDesigType(e.target.value)}>
          {DESIG_TYPES.map(t=><option key={t} value={t}>{t==='all'?'Todos los tipos':t}</option>)}
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {th('NAME','Nombre AMP')}
              {th('Country','País')}
              <th>Tipo</th>
              <th>Designación</th>
              {th(yearsField,'Años datos')}
              {th('Pct_MHW','% con MHW')}
              {th('Max_intensity_ever','Int. máx.')}
              {th('Max_category_ever','Cat. máx.')}
              {hasTrend && th('Warming_trend_per_decade','Trend SST')}
            </tr>
          </thead>
          <tbody>
            {filtered.map(m=>(
              <tr key={m.MAPAMED_ID || m.NAME}>
                <td style={{fontWeight:500,maxWidth:200}}>
                  <div style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}} title={m.NAME}>{m.NAME}</div>
                </td>
                <td style={{whiteSpace:'nowrap'}}>{COUNTRY_FLAGS[m.Country]||''} {m.Country}</td>
                <td style={{fontSize:'0.75rem',color:'var(--ink-60)',whiteSpace:'nowrap'}}>
                  {m.DESIG_TYPE||'—'}
                </td>
                <td style={{fontSize:'0.8rem',color:'var(--ink-60)',maxWidth:160}}>
                  <div style={{overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}} title={m.DESIG_ENG}>{m.DESIG_ENG||'—'}</div>
                </td>
                <td style={{textAlign:'center',fontVariantNumeric:'tabular-nums'}}>
                  {m[yearsField] ?? '—'}
                </td>
                <td><PctBar value={m.Pct_MHW}/></td>
                <td style={{textAlign:'center',fontVariantNumeric:'tabular-nums'}}>
                  {m.Max_intensity_ever != null ? <><strong>{m.Max_intensity_ever.toFixed(1)}</strong>°C</> : '—'}
                </td>
                <td><CatBadge cat={m.Max_category_ever}/></td>
                {hasTrend && (
                  <td style={{textAlign:'center',fontVariantNumeric:'tabular-nums',fontSize:'0.8rem'}}>
                    {m.Warming_trend_per_decade != null
                      ? <span style={{color: m.Warming_trend_per_decade > 0.3 ? '#d94f3d' : m.Warming_trend_per_decade > 0.15 ? '#e8934a' : '#4db8d8', fontWeight:600}}>
                          +{m.Warming_trend_per_decade.toFixed(2)}°C
                        </span>
                      : '—'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
