# MedTrack

Medication tracking and scheduling for nursing staff: a FastAPI backend (Python) and a React + Vite frontend (TypeScript).

## Requirements

- Python 3.10+
- Node.js 18+ and npm

## 1. Run the backend (FastAPI)

In a terminal, from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn med_tracker.api.app:app --reload
```

The API runs at http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs.

Keep this terminal running.

## 2. Run the frontend (React)

In a second terminal, from the project root:

```bash
cd medtrack-frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser. The frontend forwards `/api` requests to the backend on port 8000, so the backend must be running.

## Running the tests

With the virtual environment active, from the project root:

```bash
pytest
```
