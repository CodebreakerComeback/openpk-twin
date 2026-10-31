import { useCallback, useEffect, useMemo, useState } from 'react'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'https://openpk-twin-api.onrender.com').replace(/\/$/, '')

const initialForm = {
  dose: '100',
  vd: '10',
  clearance: '1',
  vc: '10',
  vp: '20',
  q: '2',
  cvClearance: '30',
  cvVolume: '20',
  cvCentral: '20',
  cvPeripheral: '20',
  patients: '1000',
  duration: '24',
  points: '25',
  seed: '42',
}

function NumberField({ label, value, onChange, unit, min = '0', step = 'any', hint, disabled = false }) {
  return (
    <label className={`field ${disabled ? 'field-disabled' : ''}`}>
      <span className="field-label">{label}</span>
      <span className="input-wrap">
        <input
          type="number"
          value={value}
          min={min}
          step={step}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
        />
        {unit && <span className="input-unit">{unit}</span>}
      </span>
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}

function formatNumber(value, digits = 3) {
  if (!Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(value)
}

function PopulationChart({ result }) {
  const chart = useMemo(() => {
    if (!result) return null
    const times = result.times_h
    const median = result.median_mg_per_L
    const lower = result.percentile_05_mg_per_L
    const upper = result.percentile_95_mg_per_L
    const profiles = result.representative_profiles_mg_per_L || []
    if (!times?.length || !median?.length || times.length !== median.length) return null

    const width = 940
    const height = 390
    const left = 76
    const right = 24
    const top = 22
    const bottom = 62
    const plotWidth = width - left - right
    const plotHeight = height - top - bottom
    const maxTime = Math.max(...times, 1)
    const maxConcentration = Math.max(...upper, ...median, 0.001) * 1.12
    const x = (value) => left + (value / maxTime) * plotWidth
    const y = (value) => top + plotHeight - (value / maxConcentration) * plotHeight
    const linePath = (values) => values.map((value, index) => `${index === 0 ? 'M' : 'L'} ${x(times[index]).toFixed(2)} ${y(value).toFixed(2)}`).join(' ')
    const bandPath = [
      ...upper.map((value, index) => `${index === 0 ? 'M' : 'L'} ${x(times[index]).toFixed(2)} ${y(value).toFixed(2)}`),
      ...lower.map((value, index) => `L ${x(times[lower.length - 1 - index]).toFixed(2)} ${y(lower[lower.length - 1 - index]).toFixed(2)}`),
      'Z',
    ].join(' ')
    const yTicks = Array.from({ length: 5 }, (_, index) => (maxConcentration * index) / 4)
    const xTicks = Array.from({ length: 5 }, (_, index) => (maxTime * index) / 4)
    const sampledProfiles = profiles.filter((_, index) => index % Math.max(1, Math.ceil(profiles.length / 12)) === 0)
    return { width, height, left, right, top, bottom, plotWidth, plotHeight, x, y, linePath, bandPath, yTicks, xTicks, sampledProfiles, maxConcentration, maxTime }
  }, [result])

  if (!chart || !result) return null
  const { width, height, left, right, top, bottom, plotWidth, plotHeight, x, y, linePath, bandPath, yTicks, xTicks, sampledProfiles, maxConcentration } = chart

  return (
    <div className="chart-shell">
      <div className="chart-topline">
        <div>
          <div className="chart-kicker">SIMULATED PLASMA EXPOSURE</div>
          <h3>Concentration–time profile</h3>
        </div>
        <span className="chart-unit">mg/L · hours</span>
      </div>
      <div className="chart-svg-wrap">
        <svg className="population-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Population pharmacokinetic concentration-time chart">
          <defs>
            <linearGradient id="predictionBand" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#7d9cff" stopOpacity="0.30" />
              <stop offset="100%" stopColor="#7d9cff" stopOpacity="0.08" />
            </linearGradient>
          </defs>
          {yTicks.map((tick, index) => (
            <g key={`y-${index}`}>
              <line x1={left} y1={y(tick)} x2={width - right} y2={y(tick)} className="chart-gridline" />
              <text x={left - 14} y={y(tick) + 4} textAnchor="end" className="chart-tick">{formatNumber(tick, 2)}</text>
            </g>
          ))}
          {xTicks.map((tick, index) => (
            <g key={`x-${index}`}>
              <line x1={x(tick)} y1={top} x2={x(tick)} y2={top + plotHeight} className="chart-gridline chart-gridline-vertical" />
              <text x={x(tick)} y={height - 31} textAnchor="middle" className="chart-tick">{formatNumber(tick, 1)}</text>
            </g>
          ))}
          <path d={bandPath} fill="url(#predictionBand)" stroke="none" />
          {sampledProfiles.map((profile, index) => (
            <path key={`patient-${index}`} d={linePath(profile)} className="patient-line">
              <title>{`Representative virtual patient ${index + 1}`}</title>
            </path>
          ))}
          <path d={linePath(result.median_mg_per_L)} className="median-line">
            <title>Median population concentration</title>
          </path>
          <line x1={left} y1={top + plotHeight} x2={width - right} y2={top + plotHeight} className="chart-axis" />
          <line x1={left} y1={top} x2={left} y2={top + plotHeight} className="chart-axis" />
          <text x={left + plotWidth / 2} y={height - 4} textAnchor="middle" className="chart-axis-label">Time after dose (hours)</text>
          <text x="18" y={top + plotHeight / 2} textAnchor="middle" className="chart-axis-label" transform={`rotate(-90 18 ${top + plotHeight / 2})`}>Concentration (mg/L)</text>
        </svg>
      </div>
      <div className="chart-legend">
        <span><i className="legend-swatch legend-median" /> Median</span>
        <span><i className="legend-swatch legend-band" /> 5th–95th percentile</span>
        <span><i className="legend-swatch legend-patient" /> Representative patients</span>
      </div>
      <p className="chart-note">The shaded region is the simulated 5th–95th percentile range at each sampling time; it is not a confidence interval or validated therapeutic range.</p>
    </div>
  )
}

function App() {
  const [model, setModel] = useState('one')
  const [form, setForm] = useState(initialForm)
  const [apiStatus, setApiStatus] = useState('checking')
  const [result, setResult] = useState(null)
  const [runError, setRunError] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastRun, setLastRun] = useState('')

  const update = (key) => (value) => setForm((current) => ({ ...current, [key]: value }))

  const checkApi = useCallback(async () => {
    setApiStatus('checking')
    try {
      const response = await fetch(`${API_BASE}/health`)
      if (!response.ok) throw new Error(`API returned ${response.status}`)
      const health = await response.json()
      setApiStatus(health.status === 'ok' ? 'online' : 'offline')
    } catch {
      setApiStatus('offline')
    }
  }, [])

  useEffect(() => {
    checkApi()
  }, [checkApi])

  const requestBody = () => {
    const dose = Number(form.dose)
    const patients = Number(form.patients)
    const duration = Number(form.duration)
    const points = Number(form.points)
    const seed = Number(form.seed)
    if (![dose, patients, duration, points, seed].every(Number.isFinite)) {
      throw new Error('Please enter valid numeric values in all required fields.')
    }
    if (dose <= 0 || patients < 1 || patients > 10000 || duration <= 0 || points < 2 || points > 500 || !Number.isInteger(patients) || !Number.isInteger(points) || !Number.isInteger(seed) || seed < 0 || seed > 4294967295) {
      throw new Error('Check dose, patient count (1–10,000), duration, time points (2–500), and seed (non-negative integer).')
    }
    if (patients * points > 1_000_000) {
      throw new Error('The selected patient count × time points exceeds the API workload limit of 1,000,000.')
    }
    const times_h = Array.from({ length: points }, (_, index) => Number(((duration * index) / (points - 1)).toFixed(6)))
    if (model === 'one') {
      const vd = Number(form.vd)
      const clearance = Number(form.clearance)
      const cvClearance = Number(form.cvClearance)
      const cvVolume = Number(form.cvVolume)
      if (![vd, clearance, cvClearance, cvVolume].every(Number.isFinite) || vd <= 0 || clearance <= 0 || cvClearance < 0 || cvVolume < 0 || cvClearance > 200 || cvVolume > 200) {
        throw new Error('Enter positive Vd and clearance values, and variability between 0% and 200%.')
      }
      return {
        dose_mg: dose,
        typical_volume_of_distribution_L: vd,
        typical_clearance_L_per_h: clearance,
        times_h,
        n_patients: patients,
        cv_clearance: cvClearance / 100,
        cv_volume: cvVolume / 100,
        seed,
      }
    }
    const vc = Number(form.vc)
    const vp = Number(form.vp)
    const clearance = Number(form.clearance)
    const q = Number(form.q)
    const cvClearance = Number(form.cvClearance)
    const cvCentral = Number(form.cvCentral)
    const cvPeripheral = Number(form.cvPeripheral)
    if (![vc, vp, clearance, q, cvClearance, cvCentral, cvPeripheral].every(Number.isFinite) || [vc, vp, clearance, q].some((value) => value <= 0) || [cvClearance, cvCentral, cvPeripheral].some((value) => value < 0 || value > 200)) {
      throw new Error('Enter positive Vc, Vp, CL and Q values, and variability between 0% and 200%.')
    }
    return {
      dose_mg: dose,
      typical_central_volume_L: vc,
      typical_peripheral_volume_L: vp,
      typical_clearance_L_per_h: clearance,
      intercompartmental_clearance_L_per_h: q,
      times_h,
      n_patients: patients,
      cv_clearance: cvClearance / 100,
      cv_central_volume: cvCentral / 100,
      cv_peripheral_volume: cvPeripheral / 100,
      seed,
    }
  }

  const runSimulation = async (event) => {
    event.preventDefault()
    setRunError('')
    setLoading(true)
    try {
      const body = requestBody()
      const endpoint = model === 'one'
        ? '/api/v1/population/iv-bolus'
        : '/api/v1/population/two-compartment/iv-bolus'
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(body),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        const detail = Array.isArray(payload.detail)
          ? payload.detail.map((item) => `${item.loc?.slice(-1)[0] || 'input'}: ${item.msg}`).join('; ')
          : payload.detail || `Request failed with status ${response.status}`
        throw new Error(detail)
      }
      setResult(payload)
      setLastRun(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch (error) {
      setRunError(error.message || 'The simulation could not be completed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const downloadCsv = () => {
    if (!result) return
    const profiles = result.representative_profiles_mg_per_L || []
    const header = ['time_h', 'percentile_05_mg_per_L', 'median_mg_per_L', 'percentile_95_mg_per_L', ...profiles.map((_, index) => `representative_patient_${result.representative_patient_ids?.[index] ?? index + 1}_mg_per_L`)]
    const rows = result.times_h.map((time, index) => [
      time,
      result.percentile_05_mg_per_L[index],
      result.median_mg_per_L[index],
      result.percentile_95_mg_per_L[index],
      ...profiles.map((profile) => profile[index]),
    ])
    const csv = [header, ...rows].map((row) => row.map((cell) => {
      const value = String(cell ?? '')
      return /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value
    }).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `openpk-twin-${model}-population-results.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  const switchModel = (nextModel) => {
    setModel(nextModel)
    setResult(null)
    setRunError('')
  }

  const medianPeak = result ? Math.max(...result.median_mg_per_L) : null
  const endMedian = result ? result.median_mg_per_L[result.median_mg_per_L.length - 1] : null

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="OpenPK-Twin home">
          <span className="brand-mark"><span /></span>
          <span className="brand-name">OpenPK<span>-Twin</span></span>
        </a>
        <div className="topbar-right">
          <div className={`api-pill api-${apiStatus}`}>
            <span className="status-dot" />
            {apiStatus === 'online' ? 'API connected' : apiStatus === 'checking' ? 'Checking API' : 'API unavailable'}
          </div>
          <a className="top-link" href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API docs <span aria-hidden="true">↗</span></a>
          <a className="github-link" href="https://github.com/CodebreakerComeback/openpk-twin" target="_blank" rel="noreferrer" aria-label="Open GitHub repository">GH</a>
        </div>
      </header>

      <main className="main-content" id="top">
        <section className="intro-row">
          <div>
            <div className="eyebrow"><span className="eyebrow-line" /> OPEN-SOURCE PHARMACOMETRICS WORKSPACE</div>
            <h1>Explore drug behaviour.<br /><span>Simulate virtual populations.</span></h1>
            <p className="intro-copy">A research-focused workspace for reproducible pharmacokinetic modelling and population simulation.</p>
          </div>
          <div className="release-card">
            <span className="release-label">PLATFORM RELEASE</span>
            <strong>v0.1.0</strong>
            <span className="release-caption">Early access · Research use</span>
          </div>
        </section>

        <div className="workspace-heading">
          <div>
            <span className="section-index">01 / SIMULATION WORKSPACE</span>
            <h2>Configure a simulation</h2>
          </div>
          <span className="workspace-caption">Deterministic seed · Reproducible output</span>
        </div>

        <div className="workspace-grid">
          <section className="panel config-panel">
            <div className="panel-heading">
              <div className="panel-icon">01</div>
              <div><h3>Model parameters</h3><p>Choose a model and define the inputs.</p></div>
            </div>

            <div className="model-switch" role="tablist" aria-label="Pharmacokinetic model">
              <button type="button" role="tab" aria-selected={model === 'one'} className={model === 'one' ? 'model-tab active' : 'model-tab'} onClick={() => switchModel('one')}>
                <span className="model-tab-number">01</span><span><strong>One-compartment</strong><small>IV bolus</small></span>
              </button>
              <button type="button" role="tab" aria-selected={model === 'two'} className={model === 'two' ? 'model-tab active' : 'model-tab'} onClick={() => switchModel('two')}>
                <span className="model-tab-number">02</span><span><strong>Two-compartment</strong><small>IV bolus</small></span>
              </button>
            </div>

            <form onSubmit={runSimulation}>
              <div className="form-section">
                <div className="form-section-title"><span>01</span> ADMINISTRATION</div>
                <div className="field-grid">
                  <NumberField label="Dose" value={form.dose} onChange={update('dose')} unit="mg" min="0.000001" />
                  <NumberField label="Virtual patients" value={form.patients} onChange={update('patients')} unit="n" min="1" step="1" hint="1–10,000 patients" />
                </div>
              </div>

              <div className="form-section">
                <div className="form-section-title"><span>02</span> PHARMACOKINETIC PARAMETERS</div>
                {model === 'one' ? (
                  <div className="field-grid">
                    <NumberField label="Volume of distribution (Vd)" value={form.vd} onChange={update('vd')} unit="L" />
                    <NumberField label="Clearance (CL)" value={form.clearance} onChange={update('clearance')} unit="L/h" />
                  </div>
                ) : (
                  <div className="field-grid">
                    <NumberField label="Central volume (Vc)" value={form.vc} onChange={update('vc')} unit="L" />
                    <NumberField label="Peripheral volume (Vp)" value={form.vp} onChange={update('vp')} unit="L" />
                    <NumberField label="Clearance (CL)" value={form.clearance} onChange={update('clearance')} unit="L/h" />
                    <NumberField label="Intercompartmental CL (Q)" value={form.q} onChange={update('q')} unit="L/h" />
                  </div>
                )}
              </div>

              <div className="form-section">
                <div className="form-section-title"><span>03</span> INTER-INDIVIDUAL VARIABILITY</div>
                <div className="field-grid">
                  <NumberField label="Clearance CV" value={form.cvClearance} onChange={update('cvClearance')} unit="%" min="0" step="1" />
                  {model === 'one' ? (
                    <NumberField label="Volume CV" value={form.cvVolume} onChange={update('cvVolume')} unit="%" min="0" step="1" />
                  ) : (
                    <>
                      <NumberField label="Central volume CV" value={form.cvCentral} onChange={update('cvCentral')} unit="%" min="0" step="1" />
                      <NumberField label="Peripheral volume CV" value={form.cvPeripheral} onChange={update('cvPeripheral')} unit="%" min="0" step="1" />
                    </>
                  )}
                </div>
                <p className="helper-text">CV is entered as a percentage and converted to a fraction for the simulation.</p>
              </div>

              <div className="form-section last-form-section">
                <div className="form-section-title"><span>04</span> SAMPLING DESIGN</div>
                <div className="field-grid three-fields">
                  <NumberField label="Duration" value={form.duration} onChange={update('duration')} unit="h" min="0.001" />
                  <NumberField label="Time points" value={form.points} onChange={update('points')} unit="n" min="2" max="500" step="1" />
                  <NumberField label="Random seed" value={form.seed} onChange={update('seed')} unit="#" min="0" step="1" />
                </div>
                <p className="helper-text">Sampling times are evenly spaced from 0 to the selected duration.</p>
              </div>

              {runError && <div className="error-banner" role="alert"><strong>Simulation could not run</strong><span>{runError}</span></div>}

              <button className="run-button" type="submit" disabled={loading}>
                {loading ? <><span className="spinner" /> Running simulation…</> : <>Run population simulation <span aria-hidden="true">↗</span></>}
              </button>
              <p className="button-footnote">Requests are processed by the OpenPK-Twin API. No patient data is requested.</p>
            </form>
          </section>

          <section className="results-column">
            <div className="panel result-panel">
              <div className="panel-heading result-heading">
                <div className="panel-icon panel-icon-blue">02</div>
                <div><h3>Simulation results</h3><p>{result ? `Completed at ${lastRun}` : 'Your population analysis will appear here.'}</p></div>
                {result && <button className="export-button" type="button" onClick={downloadCsv}>↓ <span>Export CSV</span></button>}
              </div>

              {!result ? (
                <div className="empty-state">
                  <div className="empty-illustration"><span className="empty-axis" /><span className="empty-wave wave-one" /><span className="empty-wave wave-two" /><span className="empty-wave wave-three" /><span className="empty-point point-one" /><span className="empty-point point-two" /><span className="empty-point point-three" /></div>
                  <h3>Ready when you are</h3>
                  <p>Configure the model parameters, then run a simulation to generate population concentration profiles.</p>
                  <div className="empty-meta"><span>● Two PK models</span><span>● Reproducible seed</span><span>● CSV export</span></div>
                </div>
              ) : (
                <>
                  <div className="result-summary">
                    <div className="summary-item"><span>MODEL</span><strong>{model === 'one' ? '1-CPT' : '2-CPT'}</strong><small>IV bolus</small></div>
                    <div className="summary-item"><span>VIRTUAL PATIENTS</span><strong>{formatNumber(result.n_patients, 0)}</strong><small>Simulated individuals</small></div>
                    <div className="summary-item"><span>MEDIAN PEAK</span><strong>{formatNumber(medianPeak)}</strong><small>mg/L</small></div>
                    <div className="summary-item"><span>FINAL MEDIAN</span><strong>{formatNumber(endMedian)}</strong><small>mg/L</small></div>
                  </div>
                  <PopulationChart result={result} />
                  <div className="result-details">
                    <div><span>Mean simulated clearance</span><strong>{formatNumber(result.mean_clearance_L_per_h)} L/h</strong></div>
                    {model === 'one'
                      ? <div><span>Mean simulated volume</span><strong>{formatNumber(result.mean_volume_of_distribution_L)} L</strong></div>
                      : <><div><span>Mean central volume</span><strong>{formatNumber(result.mean_central_volume_L)} L</strong></div><div><span>Mean peripheral volume</span><strong>{formatNumber(result.mean_peripheral_volume_L)} L</strong></div></>}
                    <div><span>Random seed</span><strong>{result.seed ?? 'Not fixed'}</strong></div>
                  </div>
                </>
              )}
            </div>

            <div className="panel method-panel">
              <div className="method-heading"><span className="method-symbol">i</span><div><h3>Model assumptions & interpretation</h3><p>Read before interpreting simulated outputs.</p></div></div>
              {result ? (
                <ul className="assumption-list">{result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul>
              ) : (
                <div className="assumption-preview"><span>01</span> Linear pharmacokinetics and first-order elimination are assumed.<span>02</span> Independent lognormal variability is used for the selected PK parameters.<span>03</span> Population percentiles describe simulated variability, not clinical reference limits.</div>
              )}
            </div>
          </section>
        </div>

        <section className="bottom-strip">
          <div><span className="bottom-mark">O</span><div><strong>OpenPK-Twin</strong><span>Open science for pharmacokinetic modelling</span></div></div>
          <p>Built for education and research · Version 0.1.0</p>
          <a href="https://github.com/CodebreakerComeback/openpk-twin" target="_blank" rel="noreferrer">View source on GitHub ↗</a>
        </section>
        <footer className="disclaimer">RESEARCH & EDUCATIONAL SOFTWARE ONLY <span>·</span> NOT VALIDATED FOR CLINICAL DOSING OR MEDICAL DECISION-MAKING</footer>
      </main>
    </div>
  )
}

export default App
