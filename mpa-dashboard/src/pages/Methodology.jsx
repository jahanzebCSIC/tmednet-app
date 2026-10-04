const TEAL = 'var(--teal-700)'
const TEAL_LIGHT = 'var(--teal-50)'
const TEAL_BORDER = 'var(--teal-200)'
const INK = 'var(--ink)'
const INK60 = 'var(--ink-60)'
const WHITE = 'var(--white)'

const CAT_ROWS = [
  { cat: 'I – Moderate', mult: '1×',  range: 'δT < 2 × (p90 − p50)',  color: '#f0c040', ex: 'Estrés térmico leve, blanqueamiento coralino incipiente' },
  { cat: 'II – Strong',  mult: '2×',  range: '2× ≤ δT < 3×',          color: '#e8934a', ex: 'Blanqueamiento significativo, mortalidad de invertebrados bentónicos' },
  { cat: 'III – Severe', mult: '3×',  range: '3× ≤ δT < 4×',          color: '#d94f3d', ex: 'Mortalidad masiva de Posidonia, esponjas y corales gorgoniáceos' },
  { cat: 'IV – Extreme', mult: '4×',  range: 'δT ≥ 4×',               color: '#8b0000', ex: 'Eventos catastrófficos con mortandad multiespecífica regional' },
]

const METRICS = [
  { field: 'N_events',        label: 'Nº eventos MHW',          desc: 'Número de olas de calor marinas distintas detectadas en el período estival (jun–sep) del año.' },
  { field: 'Total_days',      label: 'Días en MHW',             desc: 'Suma de días en los que la SST supera el umbral p90 y se cumplen las condiciones de MHW.' },
  { field: 'Max_intensity',   label: 'Intensidad máxima (°C)',   desc: 'Máxima diferencia entre la SST diaria y el umbral p90 climatológico durante cualquier evento del año.' },
  { field: 'Cum_intensity',   label: 'Intensidad acumulada',     desc: 'Suma de las diferencias SST − p90 sobre todos los días en MHW. Proxy del "calor total" recibido.' },
  { field: 'Mean_intensity',  label: 'Intensidad media (°C)',    desc: 'Promedio de Max_intensity a lo largo de todos los eventos del año.' },
  { field: 'Max_category',    label: 'Categoría máxima',         desc: 'Categoría Hobday (I–IV) más alta alcanzada durante cualquier evento del año.' },
  { field: 'MHW_detected',    label: 'MHW detectada',           desc: 'Y = al menos un evento estival; N = sin evento; Sin_SST = sin datos satelitales disponibles.' },
  { field: 'Pct_MHW',        label: '% Co-ocurrencia MHW',      desc: 'Proporción de años con datos en que se detectó al menos un evento MHW estival. Métrica resumen de largo plazo por AMP.' },
  { field: 'Max_intensity_ever', label: 'Intensidad máx. histórica', desc: 'Mayor intensidad puntual registrada en cualquier año con datos.' },
  { field: 'Max_category_ever', label: 'Categoría máx. histórica',  desc: 'Categoría más alta jamás alcanzada en esa AMP.' },
  { field: 'Warming_trend_per_decade', label: 'Tendencia SST (°C/dec)', desc: 'Pendiente de la regresión lineal OLS de la SST media estival anual sobre el tiempo. Positivo = calentamiento.' },
]

function SectionTitle({ num, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.1rem', marginTop: '2.5rem' }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
        background: TEAL, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 700, fontSize: '0.8rem',
      }}>{num}</div>
      <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: '1.25rem', color: INK, lineHeight: 1.2 }}>{children}</h2>
    </div>
  )
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background: WHITE, borderRadius: 10, padding: '1.25rem 1.5rem',
      boxShadow: '0 1px 4px rgba(0,0,0,0.07)', marginBottom: '1rem', ...style,
    }}>
      {children}
    </div>
  )
}

function CodeBox({ children }) {
  return (
    <pre style={{
      background: '#f3f6f8', border: '1px solid #dde4ea', borderRadius: 8,
      padding: '0.9rem 1.1rem', fontSize: '0.8rem', lineHeight: 1.8,
      color: '#1a2e3b', fontFamily: "'Courier New', monospace",
      overflowX: 'auto', margin: '0.75rem 0 0',
    }}>{children}</pre>
  )
}

function Callout({ color = '#2589ad', children }) {
  return (
    <div style={{
      background: `${color}0f`, border: `1px solid ${color}35`,
      borderLeft: `3px solid ${color}`,
      borderRadius: '0 6px 6px 0', padding: '0.65rem 1rem', margin: '0.75rem 0',
      fontSize: '0.84rem', color: INK, lineHeight: 1.7,
    }}>
      {children}
    </div>
  )
}

// ── Inline SVG: MHW detection concept diagram ─────────────────────────────────
function MhwDiagram() {
  // Simplified SST time-series sketch showing p90 threshold, event, categories
  const W = 620, H = 160
  // A made-up SST curve that spikes above p90 twice
  const sst = [21.2,21.5,21.8,22.1,22.5,23.0,23.6,24.1,24.5,24.8,25.0,25.2,25.1,24.8,24.4,24.0,
               23.5,23.2,23.0,23.3,23.7,24.2,24.8,25.3,25.7,26.0,26.1,25.8,25.3,24.7,24.2,23.8]
  const p90 = 24.3
  const days = sst.length
  const padL = 42, padR = 12, padT = 16, padB = 30
  const innerW = W - padL - padR, innerH = H - padT - padB
  const minY = 20.5, maxY = 27.0
  const xOf = i => padL + (i / (days - 1)) * innerW
  const yOf = v => padT + innerH - ((v - minY) / (maxY - minY)) * innerH
  const path = sst.map((v, i) => `${i === 0 ? 'M' : 'L'}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`).join(' ')
  const p90y = yOf(p90)

  // fill areas above p90
  const fillPaths = []
  let inEvent = false, seg = []
  sst.forEach((v, i) => {
    if (v > p90) {
      if (!inEvent) { inEvent = true; seg = [] }
      seg.push(i)
    } else {
      if (inEvent) { fillPaths.push([...seg]); inEvent = false }
    }
    if (i === sst.length - 1 && inEvent) fillPaths.push([...seg])
  })

  const fillD = fillPaths.map(seg => {
    const top = seg.map((i, k) => `${k === 0 ? 'M' : 'L'}${xOf(i).toFixed(1)},${yOf(sst[i]).toFixed(1)}`).join(' ')
    const bottom = [...seg].reverse().map((i, k) => `${k === 0 ? 'L' : 'L'}${xOf(i).toFixed(1)},${p90y.toFixed(1)}`).join(' ')
    return top + ' ' + bottom + ' Z'
  }).join(' ')

  // Y axis ticks
  const yticks = [21, 22, 23, 24, 25, 26, 27]

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: W, display: 'block', margin: '0.5rem auto' }}>
      {/* Grid */}
      {yticks.map(v => (
        <line key={v} x1={padL} x2={W - padR} y1={yOf(v)} y2={yOf(v)} stroke="#e8edf0" strokeWidth="1" />
      ))}
      {/* P90 threshold line */}
      <line x1={padL} x2={W - padR} y1={p90y} y2={p90y} stroke="#d94f3d" strokeWidth="1.5" strokeDasharray="6 3" />
      <text x={W - padR - 2} y={p90y - 4} textAnchor="end" fontSize="9" fill="#d94f3d" fontWeight="700">p90 = 24.3°C</text>
      {/* Event fill */}
      <path d={fillD} fill="#d94f3d" fillOpacity="0.18" />
      {/* SST line */}
      <path d={path} fill="none" stroke="#2589ad" strokeWidth="2" strokeLinejoin="round" />
      {/* Y axis */}
      {yticks.map(v => (
        <text key={v} x={padL - 4} y={yOf(v) + 3} textAnchor="end" fontSize="8" fill="#6b8091">{v}</text>
      ))}
      {/* X label */}
      <text x={padL} y={H - 4} fontSize="8" fill="#6b8091">Jun</text>
      <text x={(padL + W - padR) / 2} y={H - 4} textAnchor="middle" fontSize="8" fill="#6b8091">Ago</text>
      <text x={W - padR} y={H - 4} textAnchor="end" fontSize="8" fill="#6b8091">Sep</text>
      {/* Axis labels */}
      <text x={8} y={H / 2} textAnchor="middle" fontSize="8" fill="#6b8091" transform={`rotate(-90, 8, ${H / 2})`}>SST (°C)</text>
      {/* Arrows / annotations for events */}
      {fillPaths.map((seg, fi) => {
        const midI = seg[Math.floor(seg.length / 2)]
        const topY = Math.min(...seg.map(i => yOf(sst[i])))
        return (
          <g key={fi}>
            <rect x={xOf(seg[0]) - 1} y={topY - 18} width={xOf(seg[seg.length - 1]) - xOf(seg[0]) + 2} height={14}
              rx="3" fill="#d94f3d" fillOpacity="0.85" />
            <text x={(xOf(seg[0]) + xOf(seg[seg.length - 1])) / 2} y={topY - 8}
              textAnchor="middle" fontSize="7.5" fill="#fff" fontWeight="700">
              MHW ({seg.length}d)
            </text>
          </g>
        )
      })}
    </svg>
  )
}

// ── Pipeline flow (no icons — professional) ────────────────────────────────────
function Pipeline() {
  const steps = [
    { num: '01', label: 'Datos SST',        sub: 'CMEMS · 0.05° · diario · 1982–presente' },
    { num: '02', label: 'Climatología p90', sub: 'Período 1993–2016 · ventana ±5 días' },
    { num: '03', label: 'Detección MHW',    sub: 'Hobday et al. 2016 · umbral ≥5 días consecutivos' },
    { num: '04', label: 'Métricas por AMP', sub: 'Anual · estival (jun–sep) · histórico' },
    { num: '05', label: 'Visualización',    sub: '1.050 AMPs · Mediterráneo' },
  ]
  return (
    <div style={{ margin: '1.5rem 0 0.25rem', overflowX: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'stretch', minWidth: 520 }}>
        {steps.map((s, i) => (
          <div key={s.label} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            <div style={{
              flex: 1, padding: '0.7rem 0.9rem',
              background: WHITE, border: `1px solid ${TEAL_BORDER}`,
              borderLeft: i === 0 ? `3px solid ${TEAL}` : `1px solid ${TEAL_BORDER}`,
              borderRadius: i === 0 ? '6px 0 0 6px' : i === steps.length - 1 ? '0 6px 6px 0' : 0,
              borderRight: i < steps.length - 1 ? 'none' : `1px solid ${TEAL_BORDER}`,
            }}>
              <div style={{ fontSize: '0.6rem', fontWeight: 700, color: TEAL, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.2rem' }}>{s.num}</div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: INK, lineHeight: 1.3 }}>{s.label}</div>
              <div style={{ fontSize: '0.62rem', color: INK60, marginTop: '0.2rem', lineHeight: 1.4 }}>{s.sub}</div>
            </div>
            {i < steps.length - 1 && (
              <svg width="20" height="36" viewBox="0 0 20 36" style={{ flexShrink: 0, zIndex: 1 }}>
                <polyline points="0,0 14,18 0,36" fill="none" stroke={TEAL_BORDER} strokeWidth="1.5" />
                <polyline points="1,0 15,18 1,36" fill={WHITE} stroke="none" />
              </svg>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Methodology() {
  return (
    <div className="page" style={{ maxWidth: 900 }}>

      {/* ── Título ── */}
      <div style={{ marginBottom: '0.5rem' }}>
        <h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: '2rem', marginBottom: '0.4rem' }}>
          Metodología
        </h1>
        <p style={{ color: INK60, fontSize: '0.95rem', maxWidth: 640 }}>
          Descripción completa del procesamiento de datos, detección de olas de calor marinas y
          cálculo de indicadores para las 1.050 AMPs del Mediterráneo del inventario MAPAMED.
        </p>
      </div>

      {/* ── Pipeline ── */}
      <Pipeline />

      {/* ══ 1. Fuentes de datos ════════════════════════════════════════════════ */}
      <SectionTitle num="01">Fuentes de datos</SectionTitle>

      <div className="method-data-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <Card>
          <div style={{ marginBottom: '0.65rem', paddingBottom: '0.5rem', borderBottom: `1px solid ${TEAL_BORDER}` }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: INK }}>SST — Copernicus Marine</div>
            <div style={{ fontSize: '0.7rem', color: INK60, marginTop: '0.1rem' }}>CMEMS · L4 · Mediterráneo</div>
          </div>
          <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
            {[
              ['Dataset ID', 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021'],
              ['Tipo', 'Análisis de fusión multisensor (L4)'],
              ['Resolución espacial', '0.05° ≈ 5 km'],
              ['Resolución temporal', 'Diaria'],
              ['Cobertura espacial', 'Mediterráneo completo (−6°E a 37°E, 30°N–46°N)'],
              ['Cobertura temporal', '1982–presente'],
              ['Variable', 'analysed_sst (K → °C)'],
            ].map(([k, v]) => (
              <tr key={k} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '0.3rem 0.5rem 0.3rem 0', color: INK60, fontWeight: 600, whiteSpace: 'nowrap' }}>{k}</td>
                <td style={{ padding: '0.3rem 0', color: INK }}>{v}</td>
              </tr>
            ))}
          </table>
        </Card>

        <Card>
          <div style={{ marginBottom: '0.65rem', paddingBottom: '0.5rem', borderBottom: `1px solid ${TEAL_BORDER}` }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: INK }}>Áreas Marinas Protegidas — MAPAMED</div>
            <div style={{ fontSize: '0.7rem', color: INK60, marginTop: '0.1rem' }}>Edición 2019 v2 · EPSG:3035</div>
          </div>
          <table style={{ width: '100%', fontSize: '0.78rem', borderCollapse: 'collapse' }}>
            {[
              ['Base', 'MAPAMED 2019 edition v2'],
              ['Formato fuente', 'GeoPackage (EPSG:3035 LAEA)'],
              ['Registros originales', '1.320 features'],
              ['Filtro aplicado', 'Excluye PARENT_TYPE_ENG = "Secondary" o "Zone"'],
              ['AMPs únicas', '1.050 (deduplicadas por MAPAMED_ID)'],
              ['Cobertura', 'Mediterráneo + Mar Negro'],
              ['Atributos clave', 'MAPAMED_ID, NAME, Country, GIS_M_AREA, DESIG_ENG'],
            ].map(([k, v]) => (
              <tr key={k} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '0.3rem 0.5rem 0.3rem 0', color: INK60, fontWeight: 600, whiteSpace: 'nowrap' }}>{k}</td>
                <td style={{ padding: '0.3rem 0', color: INK }}>{v}</td>
              </tr>
            ))}
          </table>
        </Card>
      </div>

      {/* ══ 2. Coordenadas representativas ════════════════════════════════════ */}
      <SectionTitle num="02">Coordenadas representativas de cada AMP</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '0.85rem' }}>
          Para extraer la serie temporal de SST de cada AMP se necesita un punto representativo que caiga
          en zona marina —no en tierra firme. El centroide geométrico del polígono es frecuentemente
          inadecuado (islas interiores, AMPs costeras estrechas, lagunas). El procedimiento implementado garantiza
          que el punto de muestreo cae siempre dentro de la porción marina del AMP.
        </p>
        <div className="method-centroid-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: TEAL, marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Algoritmo de centroide marino
            </div>
            <ol style={{ fontSize: '0.82rem', color: INK60, lineHeight: 1.9, paddingLeft: '1.2rem' }}>
              <li>Cargar el polígono del AMP en EPSG:3035 (LAEA)</li>
              <li>Cargar la máscara de tierra de Natural Earth 10m</li>
              <li>Calcular la <strong>porción marina</strong>: AMP ∖ unión(polígonos de tierra)</li>
              <li>Si la porción marina no está vacía, calcular su <em>representative_point()</em></li>
              <li>En caso contrario, usar el centroide del polígono completo</li>
              <li>Reproyectar el punto resultante a WGS84 (EPSG:4326)</li>
              <li>Ajustar al nodo de cuadrícula CMEMS más cercano a 0.05°</li>
            </ol>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: TEAL, marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Resultado
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              {[
                { v: '664', l: 'Coordenadas corregidas', c: TEAL },
                { v: '386', l: 'Ya correctas (sin cambio)', c: '#4db8d8' },
                { v: '1.050', l: 'AMPs procesadas total', c: '#e8934a' },
                { v: '0', l: 'Sin polígono válido', c: '#aaa' },
              ].map(({ v, l, c }) => (
                <div key={l} style={{ background: TEAL_LIGHT, borderRadius: 7, padding: '0.5rem 0.65rem', borderLeft: `3px solid ${c}` }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: c }}>{v}</div>
                  <div style={{ fontSize: '0.68rem', color: INK60 }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ══ 3. Detección de MHW ════════════════════════════════════════════════ */}
      <SectionTitle num="03">Detección de olas de calor marinas (MHW)</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '0.75rem' }}>
          La detección sigue el estándar internacional de <strong>Hobday et al. (2016)</strong>, ampliamente adoptado
          en la literatura científica y en los sistemas de monitoreo operacional de los principales servicios oceanográficos.
          El método define una MHW como un período de temperatura anómala significativa y estadísticamente robusta respecto
          a la variabilidad estacional del lugar.
        </p>

        <div className="method-detect-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '0.75rem' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: TEAL, marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Definición formal
            </div>
            <p style={{ fontSize: '0.83rem', color: INK60, lineHeight: 1.9 }}>
              Una <strong>ola de calor marina</strong> queda definida cuando la SST diaria supera el
              percentil 90 de la distribución climatológica de referencia durante <strong>≥ 5 días consecutivos</strong>.
              Si la temperatura cae por debajo del umbral durante <strong>≤ 2 días consecutivos</strong>,
              el evento se considera continuo (no se interrumpe).
            </p>
            <Callout color="#2589ad">
              Período climatológico de referencia: <strong>1993–2016</strong> (24 años), elegido por ser
              el período de máxima cobertura y calidad del producto CMEMS mediterráneo.
            </Callout>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: TEAL, marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Cálculo del umbral p90
            </div>
            <p style={{ fontSize: '0.83rem', color: INK60, lineHeight: 1.9 }}>
              Para cada día del año <em>d</em> y cada punto de cuadrícula, el umbral se calcula sobre
              una <strong>ventana centrada de 11 días</strong> (±5 días alrededor de <em>d</em>)
              repetida a lo largo de todos los años climatológicos:
            </p>
            <CodeBox>{`umbral(d) = percentil_90(
  SST[año, d±5 días]
  para año ∈ [1993, 2016]
)

→ 24 años × 11 días = 264 valores
→ resultado: curva suave de 365 valores`}</CodeBox>
          </div>
        </div>

        <div style={{ fontWeight: 700, fontSize: '0.82rem', color: TEAL, marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Diagrama conceptual — SST estival con evento MHW detectado
        </div>
        <div style={{ background: '#f8fbfd', borderRadius: 8, border: `1px solid ${TEAL_BORDER}`, padding: '0.5rem' }}>
          <MhwDiagram />
        </div>
        <div style={{ fontSize: '0.72rem', color: INK60, textAlign: 'center', marginTop: '0.4rem' }}>
          La zona sombreada en rojo indica los días en que SST &gt; p90 constituyendo un evento MHW.
          Las etiquetas muestran la duración de cada evento en días.
        </div>
      </Card>

      {/* ══ 4. Categorías MHW ═════════════════════════════════════════════════ */}
      <SectionTitle num="04">Categorías de intensidad MHW</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '1rem' }}>
          Una vez detectado un evento, su intensidad se categoriza siguiendo <strong>Hobday et al. (2018)</strong>.
          La categoría se determina por el cociente entre el exceso de temperatura observado (δT = SST − p90)
          y la diferencia entre el percentil 90 y la mediana climatológica (p90 − p50), que representa
          la variabilidad "normal" del lugar:
        </p>
        <CodeBox>{`Categoría = floor( δT / (p90 − p50) )

δT        = SST_diaria − umbral_p90(d)
(p90−p50) = diferencia climatológica local (magnitud de referencia)`}</CodeBox>
        <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: '#f0f4f6' }}>
                {['Categoría', 'Multiplicador', 'Condición δT', 'Color en el mapa', 'Impacto ecológico típico (Mediterráneo)'].map(h => (
                  <th key={h} style={{ padding: '0.55rem 0.75rem', textAlign: 'left', fontWeight: 700, color: INK, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CAT_ROWS.map((r, i) => (
                <tr key={r.cat} style={{ borderBottom: '1px solid #eef0f2', background: i % 2 === 0 ? '#fff' : '#fafbfc' }}>
                  <td style={{ padding: '0.6rem 0.75rem', fontWeight: 700, color: r.color }}>{r.cat}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: INK60, fontWeight: 600 }}>{r.mult}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: INK60, fontFamily: 'monospace', fontSize: '0.78rem' }}>{r.range}</td>
                  <td style={{ padding: '0.6rem 0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ width: 16, height: 16, borderRadius: 3, background: r.color, flexShrink: 0 }} />
                    </div>
                  </td>
                  <td style={{ padding: '0.6rem 0.75rem', color: INK60, fontSize: '0.78rem', lineHeight: 1.5 }}>{r.ex}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Callout color="#e8934a">
          En el Mediterráneo, el período <strong>1999–presente</strong> ha concentrado la mayoría de eventos de
          categoría III (Severe) y IV (Extreme), coincidiendo con los grandes episodios de mortalidad masiva
          documentados (1999, 2003, 2006, 2022, 2023).
        </Callout>
      </Card>

      {/* ══ 5. Período de análisis ════════════════════════════════════════════ */}
      <SectionTitle num="05">Foco en el período estival</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8 }}>
          Aunque el algoritmo detecta MHW durante todo el año, el análisis ecológico se centra en el
          período <strong>junio–septiembre</strong> (meses 6–9). Esta decisión responde a:
        </p>
        <ul style={{ fontSize: '0.85rem', color: INK60, lineHeight: 2, paddingLeft: '1.3rem', margin: '0.6rem 0' }}>
          <li><strong>Ecología bentónica:</strong> los invertebrados y algas del Mediterráneo son más vulnerables al estrés
            térmico en verano, cuando el agua está más estratificada y la temperatura basal ya es elevada.</li>
          <li><strong>Mortalidad masiva:</strong> prácticamente todos los eventos documentados de mortalidad masiva en el
            Mediterráneo han ocurrido entre julio y septiembre.</li>
          <li><strong>Señal SST:</strong> la termoclina estival amplifica el impacto de las anomalías superficiales sobre la
            comunidad bentónica poco profunda.</li>
        </ul>
        <p style={{ fontSize: '0.85rem', color: INK60, lineHeight: 1.8 }}>
          Las métricas de SST media (SST_summer_mean) también se calculan sobre este período. La tendencia de
          calentamiento se estima sobre esta media anual de jun–sep para capturar el calentamiento que más
          directamente afecta a los ecosistemas bentónicos.
        </p>
      </Card>

      {/* ══ 6. Métricas calculadas ════════════════════════════════════════════ */}
      <SectionTitle num="06">Métricas calculadas por AMP</SectionTitle>

      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.81rem' }}>
          <thead>
            <tr style={{ background: '#f0f4f6' }}>
              <th style={{ padding: '0.6rem 1rem', textAlign: 'left', fontWeight: 700, color: INK, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em', width: '22%' }}>Campo</th>
              <th style={{ padding: '0.6rem 1rem', textAlign: 'left', fontWeight: 700, color: INK, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em', width: '25%' }}>Nombre legible</th>
              <th style={{ padding: '0.6rem 1rem', textAlign: 'left', fontWeight: 700, color: INK, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Descripción</th>
            </tr>
          </thead>
          <tbody>
            {METRICS.map((m, i) => (
              <tr key={m.field} style={{ borderBottom: '1px solid #eef0f2', background: i % 2 === 0 ? '#fff' : '#fafbfc' }}>
                <td style={{ padding: '0.55rem 1rem', fontFamily: 'monospace', fontSize: '0.75rem', color: '#2589ad', fontWeight: 600 }}>{m.field}</td>
                <td style={{ padding: '0.55rem 1rem', fontWeight: 600, color: INK }}>{m.label}</td>
                <td style={{ padding: '0.55rem 1rem', color: INK60, lineHeight: 1.6 }}>{m.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* ══ 7. Co-ocurrencia MHW ══════════════════════════════════════════════ */}
      <SectionTitle num="07">Indicador de co-ocurrencia MHW (Pct_MHW)</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '0.75rem' }}>
          El indicador principal que resume la exposición de cada AMP a las olas de calor marinas es
          la <strong>co-ocurrencia MHW</strong>, expresada como porcentaje:
        </p>
        <CodeBox>{`Pct_MHW = (años con MHW estival detectada / total años con datos SST) × 100

Ejemplo:  AMP con 30 años de datos, 25 con MHW → Pct_MHW = 83.3%`}</CodeBox>
        <div style={{ margin: '0.85rem 0' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.75rem' }}>
            {[
              { range: '≥ 90%', color: '#d94f3d', label: 'Muy alta exposición' },
              { range: '70–90%', color: '#e8934a', label: 'Alta exposición' },
              { range: '40–70%', color: '#f0c040', label: 'Exposición moderada' },
              { range: '< 40%', color: '#4db8d8', label: 'Baja exposición' },
            ].map(({ range, color, label }) => (
              <div key={range} style={{ background: `${color}18`, border: `1px solid ${color}50`, borderRadius: 7, padding: '0.55rem 0.7rem' }}>
                <div style={{ fontWeight: 700, color, fontSize: '0.88rem' }}>{range}</div>
                <div style={{ fontSize: '0.68rem', color: INK60, marginTop: '0.15rem' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
        <Callout color="#d94f3d">
          <strong>Importante:</strong> Pct_MHW es una métrica de <em>co-ocurrencia</em>, no de causalidad.
          Indica qué fracción de los años con SST disponible presentaron al menos un evento MHW estival.
          A escala mediterránea, el valor promedio es <strong>≈ 75%</strong>, reflejando el fuerte calentamiento
          registrado desde mediados de los 90.
        </Callout>
      </Card>

      {/* ══ 8. Tendencia SST ══════════════════════════════════════════════════ */}
      <SectionTitle num="08">Tendencia de calentamiento de la SST</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '0.75rem' }}>
          Para cada AMP se estima la tendencia de calentamiento de la SST estival (jun–sep) mediante
          una regresión lineal por mínimos cuadrados ordinarios (OLS) sobre la serie anual de
          temperatura media estival:
        </p>
        <CodeBox>{`SST_media_estival(año) = media( SST_diaria[año, jun–sep] )

Regresión OLS:
  SST_media_estival = α + β × año + ε

Warming_trend_per_decade = β × 10  (°C por década)
Trend_R2  = coeficiente de determinación R²
Trend_p   = p-valor del test F (significación estadística)`}</CodeBox>
        <p style={{ fontSize: '0.85rem', color: INK60, lineHeight: 1.8, marginTop: '0.75rem' }}>
          Un valor positivo de <code style={{ background: '#f3f6f8', padding: '0 4px', borderRadius: 3, fontSize: '0.8rem' }}>Warming_trend_per_decade</code> indica calentamiento.
          La mayoría de las AMPs mediterráneas presentan tendencias de <strong>+0.2 a +0.5 °C/década</strong>,
          con valores máximos en el Mar de Alborán y el Mediterráneo noroccidental.
          La línea de tendencia naranja en las gráficas de SST del mapa representa visualmente esta regresión.
        </p>
      </Card>

      {/* ══ 9. Pipeline técnico ═══════════════════════════════════════════════ */}
      <SectionTitle num="09">Pipeline de procesamiento</SectionTitle>

      <Card>
        <p style={{ fontSize: '0.88rem', color: INK60, lineHeight: 1.8, marginBottom: '0.85rem' }}>
          Todo el procesamiento se implementa en Python. Los pasos principales son:
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {[
            {
              step: '1. Descarga SST',
              code: 'copernicusmarine.open_dataset(dataset_id, variables=["analysed_sst"], ...',
              desc: 'Conexión a CMEMS mediante la librería oficial copernicusmarine. Descarga incremental por año para gestionar el volumen de datos (~35 GB total).',
            },
            {
              step: '2. Extracción por AMP',
              code: 'sst_point = ds.sel(lat=lat, lon=lon, method="nearest").analysed_sst',
              desc: 'Selección del nodo de cuadrícula más cercano al centroide marino de cada AMP. La conversión K→°C se aplica automáticamente.',
            },
            {
              step: '3. Climatología p90',
              code: 'p90[d] = np.percentile(window_values, 90)  # ventana ±5 días × 24 años',
              desc: 'Para cada AMP y cada día del año (1–365) se calcula el p90 sobre la ventana de 11 días × 24 años del período 1993–2016.',
            },
            {
              step: '4. Detección eventos',
              code: 'exceed = sst > p90_interp  # booleano diario\nevents = detect_events(exceed, min_duration=5, max_gap=2)',
              desc: 'Identificación de rachas de exceso sobre p90, agrupando períodos separados por ≤2 días, con duración mínima de 5 días.',
            },
            {
              step: '5. Cálculo de métricas',
              code: 'intensity = sst - p90_interp  # exceso diario\ncategory  = floor(intensity / (p90 - p50))',
              desc: 'Para cada evento: intensidad máxima, acumulada, media y categoría. Agregación anual y acumulación histórica por AMP.',
            },
            {
              step: '6. Exportación',
              code: 'mpas.json         # métricas resumen por AMP\nmpa_years.json    # serie anual por AMP\nmpa_polygons.json # polígonos simplificados para el mapa',
              desc: 'Los resultados se exportan en JSON para consumo directo por la aplicación web React.',
            },
          ].map(({ step, code, desc }) => (
            <div key={step} style={{ display: 'flex', gap: '1rem', background: TEAL_LIGHT, border: `1px solid ${TEAL_BORDER}`, borderRadius: 8, padding: '0.75rem 1rem' }}>
              <div style={{ flexShrink: 0, fontWeight: 700, fontSize: '0.75rem', color: TEAL, width: 110, paddingTop: '0.1rem' }}>{step}</div>
              <div style={{ flex: 1 }}>
                <pre style={{ background: '#e8f5fa', border: 'none', padding: '0.35rem 0.6rem', borderRadius: 5, fontSize: '0.72rem', fontFamily: 'monospace', color: '#1a4f6e', margin: '0 0 0.4rem', overflowX: 'auto' }}>{code}</pre>
                <div style={{ fontSize: '0.78rem', color: INK60, lineHeight: 1.6 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ══ 10. Limitaciones ═══════════════════════════════════════════════════ */}
      <SectionTitle num="10">Limitaciones y consideraciones</SectionTitle>

      <Card>
        <ul style={{ fontSize: '0.85rem', color: INK60, lineHeight: 2, paddingLeft: '1.3rem' }}>
          <li><strong>Resolución espacial:</strong> el producto CMEMS a 0.05° (~5 km) puede no capturar
            variabilidad submesoscalar relevante en AMPs muy pequeñas o en zonas de upwelling costero intenso.</li>
          <li><strong>Zonas sin datos:</strong> algunas AMPs en zonas someras, lagunas costeras o estuarios
            no tienen cobertura del producto satelital. Aparecen como "Sin SST" en el mapa.</li>
          <li><strong>SST vs. temperatura bentónica:</strong> la SST satelital mide la capa superficial
            (~1 mm). La relación con la temperatura en el fondo (donde vive la fauna bentónica) depende
            de la profundidad, la estratificación y la circulación local.</li>
          <li><strong>Co-ocurrencia ≠ causalidad:</strong> el indicador Pct_MHW no implica que las MHW
            causaron mortalidad; sólo que ambos fenómenos coincidieron. La atribución requiere análisis adicionales.</li>
          <li><strong>Climatología fija:</strong> el período de referencia 1993–2016 no se actualiza
            automáticamente. A medida que el calentamiento avanza, los umbrales p90 podrían subestimar
            el nivel de anomalía respecto a la temperatura "esperada" en el futuro.</li>
        </ul>
      </Card>

      {/* ══ 11. Referencias ════════════════════════════════════════════════════ */}
      <SectionTitle num="11">Referencias</SectionTitle>

      <Card>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[
            {
              ref: 'Hobday, A.J. et al. (2016)',
              title: 'A hierarchical approach to defining marine heatwaves.',
              journal: 'Progress in Oceanography, 141, 227–238.',
              doi: 'https://doi.org/10.1016/j.pocean.2015.12.014',
            },
            {
              ref: 'Hobday, A.J. et al. (2018)',
              title: 'Categorizing and naming marine heatwaves.',
              journal: 'Oceanography, 31(2), 162–173.',
              doi: 'https://doi.org/10.5670/oceanog.2018.205',
            },
            {
              ref: 'Copernicus Marine Service (2024)',
              title: 'Mediterranean Sea SST L4 Reprocessed.',
              journal: 'Dataset: cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021.',
              doi: 'https://doi.org/10.48670/moi-00173',
            },
            {
              ref: 'MAPAMED (2023)',
              title: 'The database of Mediterranean Protected Areas.',
              journal: 'MedPAN & SPA/RAC. Edición 2019 v2.',
              doi: null,
            },
            {
              ref: 'Garrabou, J. et al. (2022)',
              title: 'Marine heatwaves drive recurrent mass mortalities in the Mediterranean Sea.',
              journal: 'Global Change Biology, 28(19), 5708–5725.',
              doi: 'https://doi.org/10.1111/gcb.16301',
            },
          ].map(({ ref, title, journal, doi }) => (
            <div key={ref} style={{ paddingLeft: '0.75rem', borderLeft: `3px solid ${TEAL_BORDER}`, fontSize: '0.83rem', lineHeight: 1.7 }}>
              <strong style={{ color: INK }}>{ref}.</strong>{' '}
              <em style={{ color: INK }}>{title}</em>{' '}
              <span style={{ color: INK60 }}>{journal}</span>
              {doi && (
                <span>
                  {' '}
                  <a href={doi} target="_blank" rel="noopener noreferrer"
                    style={{ color: TEAL, textDecoration: 'underline', fontSize: '0.78rem' }}>
                    {doi}
                  </a>
                </span>
              )}
            </div>
          ))}
        </div>
      </Card>

      <div style={{ height: '2rem' }} />
    </div>
  )
}
