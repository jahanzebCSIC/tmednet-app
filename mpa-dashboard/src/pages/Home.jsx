import { Link } from 'react-router-dom'
import { useMemo } from 'react'
import mpas from '../data/mpas.json'
import tmednetLogo from '../assets/tmednet-logo.png'

const COUNTRY_FLAGS = {
  Spain:'🇪🇸', Italy:'🇮🇹', France:'🇫🇷', Greece:'🇬🇷',
  Croatia:'🇭🇷', Tunisia:'🇹🇳', Algeria:'🇩🇿', Cyprus:'🇨🇾',
  Israel:'🇮🇱', Morocco:'🇲🇦', Malta:'🇲🇹', Turkey:'🇹🇷',
}

function catBadge(maxCat) {
  if (!maxCat) return <span className="badge badge-none">—</span>
  const c = Math.round(maxCat)
  if (c >= 3) return <span className="badge badge-severe">Severe</span>
  if (c === 2) return <span className="badge badge-strong">Strong</span>
  return <span className="badge badge-moderate">Moderate</span>
}

function TrendBadge({ trend }) {
  if (trend === null || trend === undefined) return <span style={{color:'var(--ink-60)'}}>—</span>
  const color = trend > 0.3 ? '#d94f3d' : trend > 0.15 ? '#e8934a' : '#4db8d8'
  const arrow = trend > 0 ? '↑' : '↓'
  return (
    <span style={{fontWeight:700, color, fontVariantNumeric:'tabular-nums'}}>
      {arrow} {Math.abs(trend).toFixed(2)} °C/dec
    </span>
  )
}

export default function Home() {
  const withData = useMemo(() => mpas.filter(m => m.Pct_MHW !== null), [])
  const totalMPA = mpas.length
  const avgPct   = Math.round(withData.reduce((s,m) => s + m.Pct_MHW, 0) / withData.length)
  const maxInt   = Math.max(...withData.filter(m=>m.Max_intensity_ever).map(m=>m.Max_intensity_ever)).toFixed(1)
  const severe   = withData.filter(m => (m.Max_category_ever||0) >= 3).length
  const countries = [...new Set(mpas.map(m=>m.Country))].length

  // Warming trend stats — field may not exist in old JSON (graceful fallback)
  const withTrend = mpas.filter(m => m.Warming_trend_per_decade !== null && m.Warming_trend_per_decade !== undefined)
  const avgTrend  = withTrend.length ? (withTrend.reduce((s,m)=>s+m.Warming_trend_per_decade,0)/withTrend.length).toFixed(2) : null

  // Years with data — new field, fallback to Years_recorded
  const avgYears = useMemo(() => {
    const field = mpas[0]?.Years_with_data !== undefined ? 'Years_with_data' : 'Years_recorded'
    const vals = mpas.filter(m=>m[field]).map(m=>m[field])
    return vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1) : '—'
  }, [])

  const top5 = useMemo(() => {
    const seen = new Set()
    return [...withData]
      .filter(m => { const k = m.NAME; if (seen.has(k)) return false; seen.add(k); return true })
      .sort((a,b)=>b.Pct_MHW-a.Pct_MHW).slice(0,5)
  }, [withData])
  const byCountry = Object.entries(
    mpas.reduce((acc,m)=>{ acc[m.Country]=(acc[m.Country]||0)+1; return acc },{})
  ).sort((a,b)=>b[1]-a[1])

  // Top warming AMPs — deduplicate by MAPAMED_ID (or NAME fallback)
  const topWarming = useMemo(() => {
    const seen = new Set()
    return mpas
      .filter(m => m.Warming_trend_per_decade !== null && m.Warming_trend_per_decade !== undefined)
      .filter(m => { const k = m.NAME; if (seen.has(k)) return false; seen.add(k); return true })
      .sort((a,b)=>b.Warming_trend_per_decade-a.Warming_trend_per_decade).slice(0,5)
  }, [])

  return (
    <div>
      <div className="page-hero">
        {/* MHW category colour bar — echoes the T-MEDNet logo palette */}
        <div className="hero-cat-bar">
          {['#4db8d8','#f0c040','#e8934a','#d94f3d','#8b0000'].map(c => (
            <span key={c} style={{ background: c }} />
          ))}
        </div>

        <div className="page-hero-inner">
          <div className="hero-top-row">
            <img src={tmednetLogo} alt="T-MEDNet" className="hero-logo" />
            <span className="hero-divider" />
            <span className="hero-eyebrow">Olas de calor marinas · Mediterráneo</span>
          </div>

          <h1 className="hero-title">
            {totalMPA} áreas marinas protegidas<br/>
            <span className="hero-title-accent">bajo el foco del calentamiento oceánico</span>
          </h1>

          <div className="hero-meta-row">
            <span>1993 – 2024</span>
            <span className="hero-meta-dot"/>
            <span>{countries} países</span>
            <span className="hero-meta-dot"/>
            <span>Copernicus SST L4 · 0.05°</span>
            <span className="hero-meta-dot"/>
            <span>Hobday et al. 2016</span>
          </div>

          <div className="hero-ctas">
            <Link to="/map" className="hero-cta-primary">Ver mapa interactivo →</Link>
            <Link to="/mpas" className="hero-cta-ghost">Explorar todas las AMPs</Link>
          </div>
        </div>
      </div>

      <div className="page">
        {/* Stat tiles */}
        <div className="stat-grid" style={{gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))'}}>
          <div className="stat-tile">
            <div className="stat-num">{totalMPA}</div>
            <div className="stat-label">AMPs analizadas</div>
          </div>
          <div className="stat-tile">
            <div className="stat-num">{countries}</div>
            <div className="stat-label">Países mediterráneos</div>
          </div>
          <div className="stat-tile">
            <div className="stat-num">{avgYears}</div>
            <div className="stat-label">Años de datos / AMP</div>
          </div>
          <div className="stat-tile warm">
            <div className="stat-num">{avgPct}%</div>
            <div className="stat-label">Co-ocurrencia MHW media</div>
          </div>
          <div className="stat-tile warm">
            <div className="stat-num">{maxInt}°C</div>
            <div className="stat-label">Intensidad máxima (sobre p90)</div>
          </div>
          <div className="stat-tile alert">
            <div className="stat-num">{severe}</div>
            <div className="stat-label">AMPs con evento Severe+</div>
          </div>
          {avgTrend !== null && (
            <div className="stat-tile alert">
              <div className="stat-num">+{avgTrend}°C</div>
              <div className="stat-label">Calentamiento medio / década</div>
            </div>
          )}
        </div>

        {/* Main tables grid */}
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'2rem',marginTop:'1rem'}}>
          <div>
            <h2 className="section-title">AMPs con mayor co-ocurrencia MHW</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>AMP</th><th>País</th><th>% MHW</th><th>Cat. máx.</th></tr>
                </thead>
                <tbody>
                  {top5.map(m=>(
                    <tr key={m.MAPAMED_ID ?? m.NAME}>
                      <td style={{fontWeight:500,maxWidth:180,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}
                          title={m.NAME}>{m.NAME}</td>
                      <td>{COUNTRY_FLAGS[m.Country]||''} {m.Country}</td>
                      <td><strong>{m.Pct_MHW}%</strong></td>
                      <td>{catBadge(m.Max_category_ever)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h2 className="section-title">AMPs por país</h2>
            <div className="table-wrap">
              <table>
                <thead><tr><th>País</th><th>N AMPs</th><th>% MHW medio</th></tr></thead>
                <tbody>
                  {byCountry.map(([c,n])=>{
                    const cmpas = mpas.filter(m=>m.Country===c && m.Pct_MHW!==null)
                    const avg = cmpas.length ? Math.round(cmpas.reduce((s,m)=>s+m.Pct_MHW,0)/cmpas.length) : null
                    return (
                      <tr key={c}>
                        <td>{COUNTRY_FLAGS[c]||''} {c}</td>
                        <td>
                          <div style={{display:'flex',alignItems:'center',gap:'0.5rem'}}>
                            <div style={{height:8,width:Math.min(n*5,80),background:'var(--teal-600)',borderRadius:3}}/>
                            <span>{n}</span>
                          </div>
                        </td>
                        <td>{avg !== null ? <span style={{fontWeight:600}}>{avg}%</span> : '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Warming trend table — only shown if data available */}
        {topWarming.length > 0 && (
          <div style={{marginTop:'2rem'}}>
            <h2 className="section-title">AMPs con mayor calentamiento SST (tendencia lineal 1993–2024)</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>AMP</th><th>País</th>
                    <th>Trend (°C/dec)</th>
                    <th>R²</th>
                    <th>% con MHW</th>
                  </tr>
                </thead>
                <tbody>
                  {topWarming.map(m=>(
                    <tr key={m.MAPAMED_ID ?? m.NAME}>
                      <td style={{fontWeight:500,maxWidth:200,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}
                          title={m.NAME}>{m.NAME}</td>
                      <td>{COUNTRY_FLAGS[m.Country]||''} {m.Country}</td>
                      <td><TrendBadge trend={m.Warming_trend_per_decade}/></td>
                      <td style={{fontVariantNumeric:'tabular-nums',color:'var(--ink-60)'}}>
                        {m.Trend_R2 !== null ? m.Trend_R2.toFixed(2) : '—'}
                      </td>
                      <td><strong>{m.Pct_MHW ?? '—'}{m.Pct_MHW !== null ? '%' : ''}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MHW explainer */}
        <div style={{marginTop:'2rem',background:'var(--white)',borderRadius:10,padding:'1.5rem',boxShadow:'0 1px 3px rgba(0,0,0,0.06)'}}>
          <h2 className="section-title" style={{marginTop:0}}>¿Qué es una ola de calor marina?</h2>
          <p style={{color:'var(--ink-60)',lineHeight:1.8,maxWidth:800}}>
            Una ola de calor marina (MHW) se define como cualquier período en el que la temperatura
            superficial del mar supera el <strong>percentil 90 de la climatología de referencia</strong> durante
            al menos 5 días consecutivos (Hobday et al., 2016). Las MHW se clasifican en cuatro
            categorías según la intensidad del exceso de temperatura: <strong>Moderate, Strong, Severe y Extreme</strong>.
            Los datos SST provienen del producto satelital diario de Copernicus Marine Service
            (<em>cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021</em>) a resolución 0.05° (~5 km).
          </p>
        </div>
      </div>
    </div>
  )
}
