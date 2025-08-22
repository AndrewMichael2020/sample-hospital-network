import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSites, usePrograms, useCalculateScenario } from '../api/hooks';
import type { ScenarioPreset, ScenarioBuilderForm, ScenarioParams, ScenarioRequest } from '../api/types';
import { Loading } from '../components/Loading';
import { ErrorState } from '../components/ErrorState';
import { validateOccupancyTarget, validateLOSDelta, validateALCTarget, validateGrowthRate } from '../lib/format';
import './ScenarioBuilder.css';

const DEFAULT_PARAMS: ScenarioParams = {
  occupancy_target: 0.90,
  los_delta: -0.03,
  alc_target: 0.12,
  growth_pct: 0.02,
  schedule_code: 'Sched-A',
  seasonality: false,
};

const PRESET_PARAMS: Record<ScenarioPreset, Partial<ScenarioParams>> = {
  baseline: {
    occupancy_target: 0.85,
    los_delta: 0.0,
    alc_target: 0.14,
    growth_pct: 0.0,
  },
  target: {
    occupancy_target: 0.90,
    los_delta: -0.03,
    alc_target: 0.12,
    growth_pct: 0.02,
  },
  stress: {
    occupancy_target: 0.95,
    los_delta: 0.05,
    alc_target: 0.18,
    growth_pct: 0.04,
  },
  best: {
    occupancy_target: 0.80,
    los_delta: -0.05,
    alc_target: 0.08,
    growth_pct: 0.01,
  },
};

export const ScenarioBuilder: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<ScenarioBuilderForm>({
    name: '',
    preset: 'target',
    baseline_year: 2022,
    horizon_years: 3,
    selected_sites: [],
    program_id: 1,
    params: { ...DEFAULT_PARAMS, ...PRESET_PARAMS.target },
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const { data: sites, isLoading: sitesLoading, error: sitesError } = useSites();
  const { data: programs, isLoading: programsLoading, error: programsError } = usePrograms();
  const calculateScenario = useCalculateScenario({
    onSuccess: (data) => {
      // Navigate to results screen with the calculated data
      navigate('/results', { state: { scenarioData: data, scenarioForm: form } });
    },
  });

  const isLoading = sitesLoading || programsLoading || calculateScenario.isPending;
  const hasError = sitesError || programsError || calculateScenario.error;

  // Update form when preset changes
  useEffect(() => {
    const presetParams = PRESET_PARAMS[form.preset];
    setForm(prev => ({
      ...prev,
      params: { ...DEFAULT_PARAMS, ...presetParams }
    }));
  }, [form.preset]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!form.name.trim()) {
      errors.name = 'Scenario name is required';
    }

    if (form.selected_sites.length === 0) {
      errors.sites = 'At least one site must be selected';
    }

    const occError = validateOccupancyTarget(form.params.occupancy_target);
    if (occError) errors.occupancy = occError;

    const losError = validateLOSDelta(form.params.los_delta);
    if (losError) errors.los_delta = losError;

    const alcError = validateALCTarget(form.params.alc_target);
    if (alcError) errors.alc_target = alcError;

    const growthError = validateGrowthRate(form.params.growth_pct);
    if (growthError) errors.growth = growthError;

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSiteToggle = (siteId: number) => {
    setForm(prev => ({
      ...prev,
      selected_sites: prev.selected_sites.includes(siteId)
        ? prev.selected_sites.filter(id => id !== siteId)
        : [...prev.selected_sites, siteId]
    }));
  };

  const handleParamChange = (key: keyof ScenarioParams, value: any) => {
    setForm(prev => ({
      ...prev,
      params: { ...prev.params, [key]: value }
    }));
  };

  const handleCalculate = () => {
    if (!validateForm()) return;

    const request: ScenarioRequest = {
      sites: form.selected_sites,
      program_id: form.program_id,
      baseline_year: form.baseline_year,
      horizon_years: form.horizon_years,
      params: form.params,
    };

    calculateScenario.mutate(request);
  };

  if (hasError) {
    return (
      <ErrorState
        error={sitesError || programsError || calculateScenario.error || new Error('Unknown error')}
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="scenario-builder">
      <div className="scenario-header">
        <h2>Clinical Service Planning – Scenario Builder</h2>
      </div>

      <div className="scenario-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="scenario-name">Scenario Name:</label>
            <input
              id="scenario-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter scenario name"
              className={validationErrors.name ? 'error' : ''}
            />
            {validationErrors.name && <span className="error-text">{validationErrors.name}</span>}
          </div>

          <div className="form-group">
            <label>Preset:</label>
            <div className="radio-group">
              {(['baseline', 'target', 'stress', 'best'] as ScenarioPreset[]).map(preset => (
                <label key={preset} className="radio-option">
                  <input
                    type="radio"
                    value={preset}
                    checked={form.preset === preset}
                    onChange={(e) => setForm(prev => ({ ...prev, preset: e.target.value as ScenarioPreset }))}
                  />
                  {preset.charAt(0).toUpperCase() + preset.slice(1)}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="baseline-year">Baseline Year:</label>
            <select
              id="baseline-year"
              value={form.baseline_year}
              onChange={(e) => setForm(prev => ({ ...prev, baseline_year: parseInt(e.target.value) }))}
            >
              <option value={2022}>2022/23</option>
              <option value={2023}>2023/24</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="horizon">Horizon:</label>
            <select
              id="horizon"
              value={form.horizon_years}
              onChange={(e) => setForm(prev => ({ ...prev, horizon_years: parseInt(e.target.value) }))}
            >
              <option value={1}>1 yr</option>
              <option value={3}>3 yrs</option>
              <option value={5}>5 yrs</option>
            </select>
          </div>

          <div className="form-group">
            <label>Compute Mode:</label>
            <span className="static-value">On-demand</span>
          </div>
        </div>

        <div className="main-content-row">
          <div className="left-panel">
            <div className="sites-section">
              <h3>Sites (multi-select)</h3>
              {sitesLoading ? (
                <Loading size="small" message="Loading sites..." />
              ) : (
                <div className="sites-list">
                  {sites?.map(site => (
                    <label key={site.site_id} className="checkbox-option">
                      <input
                        type="checkbox"
                        checked={form.selected_sites.includes(site.site_id)}
                        onChange={() => handleSiteToggle(site.site_id)}
                      />
                      {site.site_name}
                    </label>
                  ))}
                </div>
              )}
              {validationErrors.sites && <span className="error-text">{validationErrors.sites}</span>}
            </div>

            <div className="programs-section">
              <h3>Programs (pick 1)</h3>
              {programsLoading ? (
                <Loading size="small" message="Loading programs..." />
              ) : (
                <div className="programs-list">
                  {programs?.map(program => (
                    <label key={program.program_id} className="radio-option">
                      <input
                        type="radio"
                        value={program.program_id}
                        checked={form.program_id === program.program_id}
                        onChange={(e) => setForm(prev => ({ ...prev, program_id: parseInt(e.target.value) }))}
                      />
                      {program.program_name}
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="right-panel">
            <div className="parameters-section">
              <h3>Parameters</h3>
              <div className="parameter-grid">
                <div className="param-group">
                  <label htmlFor="occupancy">Occupancy target:</label>
                  <input
                    id="occupancy"
                    type="number"
                    step="0.01"
                    min="0.80"
                    max="1.00"
                    value={form.params.occupancy_target}
                    onChange={(e) => handleParamChange('occupancy_target', parseFloat(e.target.value))}
                    className={validationErrors.occupancy ? 'error' : ''}
                  />
                  {validationErrors.occupancy && <span className="error-text">{validationErrors.occupancy}</span>}
                </div>

                <div className="param-group">
                  <label htmlFor="los-delta">LOS delta (%):</label>
                  <input
                    id="los-delta"
                    type="number"
                    step="0.01"
                    min="-0.50"
                    max="0.50"
                    value={form.params.los_delta}
                    onChange={(e) => handleParamChange('los_delta', parseFloat(e.target.value))}
                    className={validationErrors.los_delta ? 'error' : ''}
                  />
                  {validationErrors.los_delta && <span className="error-text">{validationErrors.los_delta}</span>}
                </div>

                <div className="param-group">
                  <label htmlFor="alc-target">ALC target (%):</label>
                  <input
                    id="alc-target"
                    type="number"
                    step="0.01"
                    min="0.00"
                    max="0.50"
                    value={form.params.alc_target}
                    onChange={(e) => handleParamChange('alc_target', parseFloat(e.target.value))}
                    className={validationErrors.alc_target ? 'error' : ''}
                  />
                  {validationErrors.alc_target && <span className="error-text">{validationErrors.alc_target}</span>}
                </div>

                <div className="param-group">
                  <label htmlFor="growth">Demand growth %:</label>
                  <input
                    id="growth"
                    type="number"
                    step="0.01"
                    min="-0.20"
                    max="0.20"
                    value={form.params.growth_pct}
                    onChange={(e) => handleParamChange('growth_pct', parseFloat(e.target.value))}
                    className={validationErrors.growth ? 'error' : ''}
                  />
                  <span className="param-note">(global)</span>
                  {validationErrors.growth && <span className="error-text">{validationErrors.growth}</span>}
                </div>

                <div className="param-group">
                  <label htmlFor="transfer">Transfer policy:</label>
                  <select id="transfer" defaultValue="ON">
                    <option value="ON">ON</option>
                    <option value="OFF">OFF</option>
                  </select>
                </div>

                <div className="param-group">
                  <label htmlFor="schedule">Capacity schedule:</label>
                  <select
                    id="schedule"
                    value={form.params.schedule_code}
                    onChange={(e) => handleParamChange('schedule_code', e.target.value)}
                  >
                    <option value="Sched-A">Sched-A</option>
                    <option value="Sched-B">Sched-B</option>
                  </select>
                </div>

                <div className="param-group">
                  <label htmlFor="seasonality">Seasonality:</label>
                  <select
                    id="seasonality"
                    value={form.params.seasonality ? 'ON' : 'OFF'}
                    onChange={(e) => handleParamChange('seasonality', e.target.value === 'ON')}
                  >
                    <option value="OFF">OFF</option>
                    <option value="ON">ON</option>
                  </select>
                </div>

                <div className="param-group">
                  <label htmlFor="ed-boarding">ED boarding model:</label>
                  <select id="ed-boarding" defaultValue="Lookup">
                    <option value="Lookup">Lookup</option>
                    <option value="Calculated">Calculated</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="validation-section">
              <h3>Validation</h3>
              <div className="validation-checks">
                <div className={`validation-check ${Object.keys(validationErrors).length === 0 ? 'valid' : 'invalid'}`}>
                  {Object.keys(validationErrors).length === 0 ? '✓' : '✗'} Parameters consistent
                </div>
                <div className={`validation-check ${sites && form.selected_sites.length > 0 ? 'valid' : 'invalid'}`}>
                  {sites && form.selected_sites.length > 0 ? '✓' : '✗'} Coverage matrix valid at selected sites
                </div>
                <div className="validation-check valid">
                  ✓ Bounds: occ ≥ 0.80; Eff LOS ≥ 0.25 d
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <button
            className="btn btn-primary"
            onClick={handleCalculate}
            disabled={isLoading || Object.keys(validationErrors).length > 0 || form.selected_sites.length === 0}
          >
            {calculateScenario.isPending ? (
              <>
                <span className="spinner"></span>
                Calculating...
              </>
            ) : (
              'Calculate'
            )}
          </button>
          <button className="btn btn-secondary" disabled>
            Save Scenario
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => {
              setForm({
                name: '',
                preset: 'target',
                baseline_year: 2022,
                horizon_years: 3,
                selected_sites: [],
                program_id: 1,
                params: { ...DEFAULT_PARAMS, ...PRESET_PARAMS.target },
              });
              setValidationErrors({});
            }}
          >
            Reset
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/results')} disabled>
            → Go to Results
          </button>
        </div>
      </div>
    </div>
  );
};