import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { KpiCard } from '../components/KpiCard';
import { formatNumber, formatGap } from '../lib/format';
import type { ScenarioResponse, ScenarioBuilderForm } from '../api/types';
import { apiClientFunctions } from '../api/client';
import './ResultsDashboard.css';

export const ResultsDashboard: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Initialize scenario data/form state from navigation state or sessionStorage
  const initialScenario = (() => {
    try {
      if (location.state?.scenarioData && location.state?.scenarioForm) {
        return { data: location.state.scenarioData as ScenarioResponse, form: location.state.scenarioForm as ScenarioBuilderForm };
      }
      const s = sessionStorage.getItem('lastScenario');
      if (s) {
        const parsed = JSON.parse(s);
        return { data: parsed.scenarioData as ScenarioResponse, form: parsed.scenarioForm as ScenarioBuilderForm };
      }
    } catch (e) {
      // ignore parse errors
    }
    return { data: undefined as ScenarioResponse | undefined, form: undefined as ScenarioBuilderForm | undefined };
  })();

  const [scenarioData, setScenarioData] = useState<ScenarioResponse | undefined>(initialScenario.data);
  const [scenarioForm, setScenarioForm] = useState<ScenarioBuilderForm | undefined>(initialScenario.form);
  const [labeledSaves, setLabeledSaves] = useState<Record<string, any> | null>(null);
  const [loadingLabel, setLoadingLabel] = useState(false);

  if (!scenarioData || !scenarioForm) {
    return (
      <div className="results-dashboard">
        <div className="no-data-message">
          <h2>No scenario data available</h2>
          <p>Please run a scenario calculation first.</p>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/scenario-builder')}
          >
            ← Back to Scenario Builder
          </button>
        </div>
      </div>
    );
  }

  const { kpis, by_site } = scenarioData;
  const maxGap = Math.max(...by_site.map(site => Math.abs(site.capacity_gap)));

  const onSave = async () => {
    try {
      const payload = { scenarioForm, scenarioData };
      const res = await apiClientFunctions.saveScenario(payload);
      alert(`Scenario saved: ${res.id}`);

      // If the current scenario has a label A/B/C, also save it as a labeled scenario
      try {
        const name = (scenarioForm && (scenarioForm as any).name) ? (scenarioForm as any).name : '';
        if (name === 'A' || name === 'B' || name === 'C') {
          await apiClientFunctions.saveScenarioLabel(name as 'A' | 'B' | 'C', { scenarioForm, scenarioData });
          // refresh labeled saves so selector reflects new entry
          try {
            const lbls = await apiClientFunctions.getLabeledScenarios();
            setLabeledSaves(lbls || {});
          } catch (e) {
            // ignore
          }
        }
      } catch (e) {
        console.error('Save label failed', e);
      }
    } catch (err) {
      console.error('Save failed', err);
      const msg = (err && (err as any).message) ? (err as any).message : JSON.stringify(err);
      alert('Save failed: ' + (msg || 'unknown'));
    }
  };

  // Load labeled saves (A/B/C) on mount so the selector can show available entries
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await apiClientFunctions.getLabeledScenarios();
        // res is a mapping { A: payload|null, B: payload|null, C: payload|null }
        if (mounted) setLabeledSaves(res || {});
      } catch (err) {
        console.error('Failed to load labeled saves', err);
        if (mounted) setLabeledSaves({});
      }
    })();
    return () => { mounted = false; };
  }, []);

  // Handler to load a labeled scenario
  const loadLabeledScenario = async (label: string) => {
    if (!label) return;
    if (!labeledSaves) {
      alert('No labeled saves available');
      return;
    }
    const payload = labeledSaves[label];
    if (!payload) {
      alert(`No saved scenario for label ${label}`);
      return;
    }

    setLoadingLabel(true);
    try {
      // payload shape may be { form: { ... } } or { scenarioForm, scenarioData }
      if (payload.scenarioData && payload.scenarioForm) {
        setScenarioForm(payload.scenarioForm);
        setScenarioData(payload.scenarioData);
        // persist to sessionStorage
        try { sessionStorage.setItem('lastScenario', JSON.stringify({ scenarioData: payload.scenarioData, scenarioForm: payload.scenarioForm })); } catch(e) {}
        return;
      }

      // payload could be { form: { ... } } from builder saves; only recompute if it includes selected sites
      const form = payload.form || payload.scenarioForm || null;
      if (form) {
        const selectedSites = (form as any).selected_sites || [];
        if (!selectedSites || selectedSites.length === 0) {
          // Inform user that labeled form lacks site selection and cannot be recomputed here
          alert(`Label ${label} contains a saved form but no selected sites. To load this label here, open the builder, select sites, compute, then save as ${label}.`);
          return;
        }

        // Recompute and update only on success
        try {
          const request = {
            sites: selectedSites,
            program_id: (form as any).program_id || 1,
            baseline_year: (form as any).baseline_year || 2022,
            horizon_years: (form as any).horizon_years || 3,
            params: (form as any).params || {},
          };
          const result = await apiClientFunctions.calculateScenario(request as any);
          setScenarioForm(form as ScenarioBuilderForm);
          setScenarioData(result as ScenarioResponse);
          try { sessionStorage.setItem('lastScenario', JSON.stringify({ scenarioData: result, scenarioForm: form })); } catch(e) {}
        } catch (err) {
          console.error('Recompute failed for labeled scenario', err);
          alert('Failed to recompute labeled scenario');
        }
        return;
      }

      alert('Unknown labeled payload format');
    } finally {
      setLoadingLabel(false);
    }
  };

  return (
    <div className="results-dashboard">
      <div className="results-header">
        <div className="results-header-left">
          <h2>Results — Scenario: "{scenarioForm.name || 'Untitled'}"</h2>
          <span className="baseline-info">(Baseline: {scenarioForm.baseline_year}/{(scenarioForm.baseline_year + 1) % 100})</span>
        </div>
        <div className="results-header-right">
          <span className="scenario-label">Saved:</span>
          <label htmlFor="scenario-select" className="sr-only">Select scenario</label>
          <select id="scenario-select" className="scenario-select" value={scenarioForm?.name || ''} onChange={(e) => loadLabeledScenario(e.target.value)} disabled={loadingLabel}>
            <option value="">Select saved</option>
            <option value="A">A</option>
            <option value="B">B</option>
            <option value="C">C</option>
          </select>
        </div>
      </div>

      <div className="kpi-cards-section">
        <h3>KPI Cards (aggregate of current filters)</h3>
        <div className="kpi-cards-grid">
          <KpiCard title="Required Beds" value={kpis.total_required_beds} format="number" />
          <KpiCard title="Staffed Beds" value={kpis.total_staffed_beds} format="number" />
          <KpiCard
            title="Capacity Gap"
            value={kpis.total_capacity_gap}
            format="gap"
            trend={kpis.total_capacity_gap > 0 ? 'up' : kpis.total_capacity_gap < 0 ? 'down' : 'neutral'}
          />
          <KpiCard title="Nursing FTE" value={kpis.total_nursing_fte} format="fte" />
        </div>

        <div className="filters-info">
          Filters: Sites[{by_site.length}] Program[Selected Program] Subprogram[All]
        </div>
      </div>

      <div className="by-site-section">
        <h3>By-Site Table (sorted by gap)</h3>
        <div className="table-container">
          <table className="results-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Site</th>
                <th>Req Beds</th>
                <th>Staffed</th>
                <th>Gap</th>
                <th>Gap Bar</th>
              </tr>
            </thead>
            <tbody>
              {by_site
                .sort((a, b) => b.capacity_gap - a.capacity_gap)
                .map((site, index) => (
                  <tr key={site.site_id}>
                    <td>{index + 1}</td>
                    <td className="site-name">{site.site_name}</td>
                    <td>{formatNumber(site.required_beds, { maximumFractionDigits: 0 })}</td>
                    <td>{formatNumber(site.staffed_beds, { maximumFractionDigits: 0 })}</td>
                    <td className={`gap-value ${site.capacity_gap > 0 ? 'positive' : site.capacity_gap < 0 ? 'negative' : ''}`}>
                      {formatGap(site.capacity_gap)}
                    </td>
                    <td className="gap-bar">
                      <div className="bar-container">
                        <span
                          className="bar-fill"
                          style={{
                            width: `${Math.abs(site.capacity_gap) / (maxGap || 1) * 100}%`,
                            backgroundColor: site.capacity_gap > 0 ? '#ef4444' : '#10b981',
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="ed-metrics-section">
        <h3>ED Metrics (informing inpatient flow)</h3>
        <div className="ed-metrics-box">
          <div className="ed-metric">Adult ED arrivals: <span className="metric-value positive">+3.1%</span></div>
          <div className="ed-metric">Pediatric: <span className="metric-value positive">+0.8%</span></div>
          <div className="ed-metric">UCC: <span className="metric-value positive">+1.2%</span></div>
          <div className="ed-metric">Estimated boarding hours (95th): <span className="metric-value warning">↑ 6%</span>
            (occ @ {(scenarioForm.params.occupancy_target * 100).toFixed(0)}%; LOS∆ {scenarioForm.params.los_delta >= 0 ? '+' : ''}{(scenarioForm.params.los_delta * 100).toFixed(0)}%; ALC {(scenarioForm.params.alc_target * 100).toFixed(0)}%)
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button className="btn btn-secondary" onClick={() => navigate('/scenario-builder', { state: { formData: scenarioForm } })}>← Adjust Parameters</button>
        <button className="btn btn-secondary" onClick={onSave}>Save Scenario</button>
  <button className="btn btn-secondary" onClick={() => navigate('/compare')}>Compare results</button>
      </div>

  {/* Saved scenarios panel removed per UX request */}
    </div>
  );
};


// SavedList removed