# Frontend Development Guide

## Quick Start

### Start the API Server
```bash
cd /path/to/project
python3 mock_api.py
```
The API will be available at http://localhost:8080

### Start the Frontend Development Server
```bash
cd apps/frontend
npm install
npm run dev
```
The frontend will be available at http://localhost:5173

## Environment Configuration

The frontend can be configured using environment variables in `apps/frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_TITLE="Clinical Service Planning - Healthcare Scenario Builder"
```

## API Endpoints

The mock API provides the following endpoints:
- `GET /reference/sites` - Hospital sites
- `GET /reference/programs` - Healthcare programs
- `GET /reference/subprograms` - Healthcare subprograms
- `POST /scenarios/compute` - Calculate scenario results

## Troubleshooting

### "Something went wrong - Network Error"
This error occurs when the frontend cannot connect to the API server. Make sure:
1. The API server is running: `python3 mock_api.py`
2. The API is accessible at http://localhost:8080
3. No firewall is blocking the connection

### Compare Scenarios Page
The Compare page can be accessed in two ways:
- `/compare` - Shows placeholder comparison data
- `/compare/1/2` - Shows comparison between specific scenarios (when implemented)