import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCompare.css';
import { useEffect, useState } from 'react';
import { apiClientFunctions } from '../api/client';

export const ScenarioCompare: React.FC = () => {
  const navigate = useNavigate();
  const [labels, setLabels] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await apiClientFunctions.getLabeledScenarios();
        if (mounted) setLabels(data);
      } catch (e) {
        if (mounted) setLabels({ A: null, B: null, C: null });
      }
    })();
    return () => { mounted = false };
  }, []);

  return (
    <div className="scenario-compare">
      <div className="compare-header">
        <h2>Compare Scenarios</h2>
      </div>

      <div className="compare-content">
        <div className="scenario-labels">
          <div className="scenario-label">A: {labels ? (labels.A ? JSON.stringify(labels.A).slice(0,120) : '--- empty ---') : 'Loading...'}</div>
          <div className="vs-divider">vs</div>
          <div className="scenario-label">B: {labels ? (labels.B ? JSON.stringify(labels.B).slice(0,120) : '--- empty ---') : 'Loading...'}</div>
          <div className="vs-divider">vs</div>
          <div className="scenario-label">C: {labels ? (labels.C ? JSON.stringify(labels.C).slice(0,120) : '--- empty ---') : 'Loading...'}</div>
        </div>

        <div className="global-kpis-section">
          <h3>Global KPIs</h3>
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Scenario A</th>
                  <th>Δ(A-B)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Required Beds (all sites)</td>
                  <td>842</td>
                  <td className="delta positive">+36</td>
                </tr>
                <tr>
                  <td>Staffed Beds (sched-A)</td>
                  <td>790</td>
                  <td className="delta neutral">0</td>
                </tr>
                <tr>
                  <td>Capacity Gap</td>
                  <td>+52</td>
                  <td className="delta positive">+36</td>
                </tr>
                <tr>
                  <td>Nursing FTE</td>
                  <td>126.4</td>
                  <td className="delta positive">+5.7</td>
                </tr>
                <tr>
                  <td>ED Boarding (95th, hours)</td>
                  <td>+6%</td>
                  <td className="delta positive">+9 pp</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="by-site-section">
          <h3>By-Site Snapshot (top 5 by absolute gap delta)</h3>
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Site</th>
                  <th>Gap A</th>
                  <th>Gap B</th>
                  <th>Δ(A-B)</th>
                  <th>ASCII Bars</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>1</td>
                  <td>Sunrise Coast Hosp</td>
                  <td className="gap positive">+18</td>
                  <td className="gap positive">+9</td>
                  <td className="delta positive">+9</td>
                  <td className="ascii-bars">
                    <div className="bar-row">A: ████████</div>
                    <div className="bar-row">B: ████▌</div>
                  </td>
                </tr>
                <tr>
                  <td>2</td>
                  <td>Grouse Ridge Medical</td>
                  <td className="gap positive">+12</td>
                  <td className="gap positive">+6</td>
                  <td className="delta positive">+6</td>
                  <td className="ascii-bars">
                    <div className="bar-row">A: █████▌</div>
                    <div className="bar-row">B: ███</div>
                  </td>
                </tr>
                <tr>
                  <td>3</td>
                  <td>Driftwood Regional</td>
                  <td className="gap positive">+4</td>
                  <td className="gap positive">+1</td>
                  <td className="delta positive">+3</td>
                  <td className="ascii-bars">
                    <div className="bar-row">A: ██▌</div>
                    <div className="bar-row">B: ▌</div>
                  </td>
                </tr>
                <tr>
                  <td>4</td>
                  <td>Blue Heron Medical</td>
                  <td className="gap positive">+3</td>
                  <td className="gap positive">+2</td>
                  <td className="delta positive">+1</td>
                  <td className="ascii-bars">
                    <div className="bar-row">A: ██</div>
                    <div className="bar-row">B: █▌</div>
                  </td>
                </tr>
                <tr>
                  <td>5</td>
                  <td>Snowberry General</td>
                  <td className="gap positive">+1</td>
                  <td className="gap neutral">+0</td>
                  <td className="delta positive">+1</td>
                  <td className="ascii-bars">
                    <div className="bar-row">A: ▌</div>
                    <div className="bar-row">B: </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="placeholder-notice">
          <p>🚧 This is a placeholder implementation. In a complete version, this screen would:</p>
          <ul>
            <li>Allow selection of two scenarios to compare</li>
            <li>Show real calculated data from the API</li>
            <li>Provide interactive delta visualizations</li>
            <li>Support export and saving functionality</li>
          </ul>
        </div>

        <div className="action-buttons">
          <button 
            className="btn btn-secondary"
            onClick={() => navigate('/results')}
          >
            ← Back to Results
          </button>
          <button className="btn btn-secondary" disabled>
            Duplicate A→New
          </button>
          <button className="btn btn-secondary" disabled>
            Export Comparison CSV
          </button>
        </div>
      </div>
    </div>
  );
};