#!/usr/bin/env python3
"""
API test script for the synthetic healthcare API.
"""

import requests
import time
import subprocess
import os
import sys

def test_api():
    """Test the API endpoints."""
    # Start server in background, capture output
    print("Starting API server...")
    env = os.environ.copy()
    env['SKIP_DB_INIT'] = '1'
    server_process = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'main_api:app', '--host', '127.0.0.1', '--port', '8001'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )

    # Poll for server readiness (max 15s)
    import requests
    base_url = 'http://127.0.0.1:8001'
    ready = False
    for _ in range(30):
        try:
            r = requests.get(f'{base_url}/health', timeout=0.5)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
    if not ready:
        print("\n❌ API server did not start in time. Captured logs:")
        try:
            logs = server_process.stdout.read()
            print(logs)
        except Exception:
            print("(Could not read server logs)")
        server_process.terminate()
        server_process.wait()
        assert False, 'API server did not start in time.'
    
    try:
        base_url = 'http://127.0.0.1:8001'
        
        # Test root endpoint
        r = requests.get(f'{base_url}/')
        assert r.status_code == 200, f'Root endpoint failed: {r.status_code}'
        print('✓ Root endpoint OK')
        
        # Test health endpoint
        r = requests.get(f'{base_url}/health')
        assert r.status_code == 200, f'Health endpoint failed: {r.status_code}'
        print('✓ Health endpoint OK')
        
        # Test dimension endpoints
        for endpoint in ['sites', 'programs', 'lhas']:
            r = requests.get(f'{base_url}/api/v1/dimensions/{endpoint}')
            assert r.status_code == 200, f'{endpoint} endpoint failed: {r.status_code}'
            print(f'✓ {endpoint} endpoint OK')
        
        # Test patient endpoint
        r = requests.get(f'{base_url}/api/v1/patients?page=1&size=10')
        assert r.status_code == 200, f'Patients endpoint failed: {r.status_code}'
        print('✓ Patients endpoint OK')
        
        # Test population endpoint
        r = requests.get(f'{base_url}/api/v1/population/projections?page=1&size=5')
        assert r.status_code == 200, f'Population endpoint failed: {r.status_code}'
        print('✓ Population endpoint OK')
        
        # Test validation endpoint
        r = requests.get(f'{base_url}/api/v1/validation/summary')
        assert r.status_code == 200, f'Validation endpoint failed: {r.status_code}'
        print('✓ Validation endpoint OK')

        print('\nAll API tests passed! 🎉')
        assert True

    except Exception as e:
        print(f'\n❌ API test failed: {e}')
        assert False, f'API test failed: {e}'

    finally:
        # Stop server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_api()
    sys.exit(0)