# Event-ticketing
A Private event ticketing + smart guest list + check-in system

## Frontend (Vite + React)
The frontend lives in `frontend/` and connects to the Django REST API.

### Run locally
```bash
cd frontend
npm install
npm run dev
```

To override the API base URL, create `frontend/.env` with:
```
VITE_API_BASE_URL=http://localhost:8000/api/
```
