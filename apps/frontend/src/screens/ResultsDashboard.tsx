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

  // Get the scenario data passed from the builder
  let scenarioData = location.state?.scenarioData as ScenarioResponse | undefined;
  let scenarioForm = location.state?.scenarioForm as ScenarioBuilderForm | undefined;

  // Fallback: load lastScenario from sessionStorage if navigation state was lost (page reloads etc)
  if (!scenarioData || !scenarioForm) {
    try {
      const s = sessionStorage.getItem('lastScenario');
      if (s) {
        const parsed = JSON.parse(s);
        scenarioData = parsed.scenarioData;
        scenarioForm = parsed.scenarioForm;
      }
    } catch (e) {
      // ignore
    }
  }

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
    } catch (err) {
      console.error('Save failed', err);
      const msg = (err && (err as any).message) ? (err as any).message : JSON.stringify(err);
      alert('Save failed: ' + (msg || 'unknown'));
    }
  };

  return (
    <div className="results-dashboard">
      <div className="results-header">
        <h2>Results — Scenario: "{scenarioForm.name || 'Untitled'}"</h2>
        <span className="baseline-info">(Baseline: {scenarioForm.baseline_year}/{(scenarioForm.baseline_year + 1) % 100})</span>
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
        <button className="btn btn-secondary" disabled>Export to Power BI</button>
      </div>

      <div className="saved-panel">
        <h3>Saved Scenarios</h3>
        <SavedList />
      </div>
    </div>
  );
};


const SavedList: React.FC = () => {
  const [saved, setSaved] = useState<any[] | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await apiClientFunctions.getSavedScenarios();
        const entries = res && (res as any).data ? (res as any).data : res;
        if (mounted) setSaved(entries);
      } catch (err) {
        console.error('Saved scenarios load error', err);
        if (mounted) setSaved([]);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  const onLoadSaved = (entry: any) => {
    console.log('Load saved payload', entry);
    alert(`Loaded saved scenario ${entry.id} (check console for payload)`);
  };

  if (saved === null) return <div>Loading...</div>;
  if (saved.length === 0) return <div>No saved scenarios</div>;

  return (
    <ul>
      {saved.map((s: any) => (
        <li key={s.id}>
          <strong>{s.id}</strong> — {s.saved_at} <button onClick={() => onLoadSaved(s)}>Load</button>
        </li>
      ))}
    </ul>
  );
};