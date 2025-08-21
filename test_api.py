#!/usr/bin/env python3
"""
API test script for the synthetic healthcare API.
"""

import requests
import time
import subprocess
import sys

def test_api():
    """Test the API endpoints."""
    # Start server in background
    print("Starting API server...")
    server_process = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8001'], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    time.sleep(3)
    
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
        return True
        
    except Exception as e:
        print(f'\n❌ API test failed: {e}')
        return False
        
    finally:
        # Stop server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)