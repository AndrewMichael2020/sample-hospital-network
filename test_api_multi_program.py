#!/usr/bin/env python3
"""
Test multi-program scenario computation.
"""
from fastapi.testclient import TestClient
from api.main import app
import api.main as api_main


class SimpleMockService:
    async def calculate_scenario(self, request):
        # request.program_ids should be present
        pids = getattr(request, 'program_ids', [getattr(request, 'program_id', None)])
        # create per-program results: for each program, one site with small numbers
        by_site = []
        total_required = 0
        total_staffed = 0
        total_adm = 0
        for i, pid in enumerate(pids, start=1):
            site_id = 1
            required = 2
            staffed = 10
            adm = 50
            total_required += required
            total_staffed += staffed
            total_adm += adm
            by_site.append({
                'site_id': site_id,
                'site_code': 'S1',
                'site_name': 'Site 1',
                'admissions_projected': adm,
                'los_effective': 5.0,
                'patient_days': adm * 5,
                'census_average': (adm * 5) / 365.0,
                'required_beds': required,
                'staffed_beds': staffed,
                'capacity_gap': required - staffed,
                'nursing_fte': 1.0
            })

        return {
            'kpis': {
                'total_required_beds': total_required,
                'total_staffed_beds': total_staffed,
                'total_capacity_gap': total_required - total_staffed,
                'total_nursing_fte': len(pids) * 1.0,
                'avg_occupancy': 0.02,
                'total_admissions': total_adm,
                'avg_los_effective': 5.0
            },
            'by_site': by_site,
            'metadata': {'request_params': getattr(request, 'model_dump', lambda: {})()}
        }


def test_multi_program_compute():
    # Monkeypatch the scenario service
    api_main.scenario_service = SimpleMockService()
    client = TestClient(app)

    payload = {
        'sites': [1],
        'program_ids': [1, 2, 3],
        'baseline_year': 2022,
        'horizon_years': 1,
        'params': {
            'occupancy_target': 0.90,
            'los_delta': 0.0,
            'alc_target': 0.12,
            'growth_pct': 0.0,
            'schedule_code': 'Sched-A',
            'seasonality': False
        }
    }

    resp = client.post('/scenarios/compute', json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Expect aggregation across 3 programs
    assert data['kpis']['total_required_beds'] == 2 * 3
    assert data['kpis']['total_staffed_beds'] == 10 * 3
    assert len(data['by_site']) >= 1

    print('Multi-program compute test passed')
