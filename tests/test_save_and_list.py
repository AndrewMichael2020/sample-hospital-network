import subprocess
import os
import time
import requests
from pathlib import Path


def start_server():
    env = os.environ.copy()
    env['SKIP_DB_INIT'] = '1'
    # Ensure Python can import the `api` package regardless of cwd by setting PYTHONPATH
    repo_root = Path(__file__).resolve().parents[1]
    env['PYTHONPATH'] = str(repo_root)
    proc = subprocess.Popen([
        'python', '-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '8001'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

    base = 'http://127.0.0.1:8001'
    ready = False
    for _ in range(30):
        try:
            r = requests.get(f'{base}/health', timeout=0.5)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not ready:
        try:
            print(proc.stdout.read())
        except Exception:
            pass
        proc.terminate()
        proc.wait()
        raise RuntimeError('Server did not start')

    return proc, base


def test_save_and_list_flow(tmp_path):
    # prepare working directory and start server so saved files go to tmp_path
    sd = tmp_path / 'saved_scenarios'
    sd.mkdir()
    oldcwd = os.getcwd()
    os.chdir(tmp_path)
    proc, base = start_server()
    try:
        payload = {"foo": "bar"}
        r = requests.post(f'{base}/scenarios/save', json=payload, timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert 'data' in data and 'id' in data['data']
        save_id = data['data']['id']

        # List saved
        r2 = requests.get(f'{base}/scenarios/saved', timeout=5)
        assert r2.status_code == 200
        listing = r2.json()
        assert 'data' in listing
        ids = [e['id'] for e in listing['data']]
        assert save_id in ids

    finally:
        try:
            os.chdir(oldcwd)
        except Exception:
            pass
        if proc:
            proc.terminate()
            proc.wait()
