// Simple integration test that calls the frontend dev server (which proxies to the API)
// Uses global fetch (Node 18+). Run with: node scripts/run_frontend_integration_test.mjs

const BASE = process.env.BASE_URL || 'http://localhost:5176';

async function call(path, opts) {
  const url = `${BASE}${path}`;
  try {
    const res = await fetch(url, opts);
    const text = await res.text();
    let parsed = text;
    try { parsed = JSON.parse(text); } catch(e) {}
    console.log(`\n[OK] ${opts?.method || 'GET'} ${path} -> ${res.status}`);
    console.log(JSON.stringify(parsed, null, 2).slice(0, 2000));
  } catch (err) {
    console.error(`\n[ERR] ${opts?.method || 'GET'} ${path} -> ${err.message}`);
  }
}

async function run() {
  console.log(`Running frontend-proxy integration test against ${BASE}`);

  await call('/reference/sites');
  await call('/reference/programs');
  await call('/reference/seasonality');
  await call('/reference/staffing-factors');
  await call('/reference/staffed-beds?schedule=Sched-A');

  const payload = {
    sites: [1,2],
    program_id: 1,
    baseline_year: 2022,
    horizon_years: 1,
    params: {
      occupancy_target: 0.9,
      los_delta: 0.0,
      alc_target: 0.12,
      growth_pct: 0.0,
      schedule_code: 'Sched-A',
      seasonality: false
    }
  };

  await call('/scenarios/compute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  console.log('\nIntegration test complete');
}

run();
