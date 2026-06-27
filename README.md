# 🔍 Deepfake Detective

> **UNESCO Youth Hackathon 2026 · Media & Information Literacy**  
> A two-mode web app teaching people to spot AI-generated media through gamified case investigations and live file scanning.

---

## Features

| Mode | What it does |
|------|-------------|
| **The Academy** | Work through pre-built deepfake cases (audio, video, image). Use forensic tools to uncover clues, make your verdict, earn points. |
| **The Scanner** | Upload any real-world file. Get an AI confidence score from Sightengine's deepfake detection API. |

---

## Repo structure

```
/
├── backend/
│   ├── main.py          # FastAPI app, CORS, lifespan startup
│   ├── models.py        # SQLModel DB models + Pydantic response schemas
│   ├── database.py      # Engine, session, seed data (4 cases + clues)
│   ├── routers/
│   │   ├── cases.py     # GET /api/cases, /cases/{id}, /cases/{id}/tools/{tool}, POST /cases/{id}/verify
│   │   └── detect.py    # POST /api/detect-upload → Sightengine
│   ├── requirements.txt
│   ├── .env.example
│   └── start.sh
└── frontend/
    ├── src/
    │   ├── App.js        # Full React dashboard (Academy + Scanner)
    │   ├── App.css       # Dark forensics theme, mobile-first
    │   ├── api.js        # Centralised API client
    │   └── index.js
    ├── public/index.html
    ├── package.json
    └── .env.example
```

---

## Local development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

The database auto-creates and seeds 4 cases + clues on first startup.  
SQLite is used locally (no Supabase needed for dev); PostgreSQL in production.

### Frontend

```bash
cd frontend
cp .env.example .env.local
# set REACT_APP_API_URL=http://localhost:8000
npm install
npm start
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cases` | List all Academy cases |
| GET | `/api/cases/{id}` | Case detail (story, media URL) |
| GET | `/api/cases/{id}/tools/{tool_type}` | Reveal a forensic clue |
| POST | `/api/cases/{id}/verify` | Check guess → score + explanation |
| GET | `/api/leaderboard` | Top 10 scores |
| POST | `/api/detect-upload` | Upload file → Sightengine confidence % |

**Tool types:** `lighting` · `metadata` · `reverse_image` · `voice_artifacts`

---

## Environment variables

### Backend (Render dashboard)

| Variable | Where to get it |
|----------|----------------|
| `DATABASE_URL` | Supabase → Settings → Database → Connection string (Transaction pooler) |
| `SIGHTENGINE_API_USER` | [sightengine.com](https://sightengine.com) → Dashboard → API credentials |
| `SIGHTENGINE_API_SECRET` | Same as above |

### Frontend (Vercel dashboard)

| Variable | Value |
|----------|-------|
| `REACT_APP_API_URL` | Your Render backend URL, e.g. `https://deepfake-detective-api.onrender.com` |

---

## Deployment

### 1 · Supabase (database)

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **Settings → Database → Connection string**
3. Copy the **Transaction pooler** URL (port 6543, includes `?pgbouncer=true`)
4. This becomes your `DATABASE_URL`

Tables are created automatically by FastAPI on startup via `SQLModel.metadata.create_all()`.

### 2 · Render (backend)

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo, set **Root directory** to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `DATABASE_URL`, `SIGHTENGINE_API_USER`, `SIGHTENGINE_API_SECRET`
6. Deploy

### 3 · Vercel (frontend)

1. Import your GitHub repo at [vercel.com](https://vercel.com)
2. Set **Root directory** to `frontend`
3. Framework preset: **Create React App**
4. Add environment variable: `REACT_APP_API_URL` = your Render URL
5. Deploy

### 4 · Tighten CORS (before submission)

In `backend/main.py`, update the CORS origins:
```python
allow_origins=["https://your-app.vercel.app"],
```

---

## Adding more cases

Add entries to `SEED_CASES` and `SEED_CLUES` in `backend/database.py`.  
For a fresh seed, delete the `cases` table in Supabase and redeploy — the app will re-create and re-seed.

---

## Tech stack

- **Frontend:** React 18, deployed on Vercel
- **Backend:** FastAPI + Python, deployed on Render
- **Database:** PostgreSQL via Supabase, SQLModel ORM
- **Deepfake API:** [Sightengine](https://sightengine.com) (image, video, audio)
- **Async HTTP:** httpx
- **File uploads:** python-multipart

---

*Built for the UNESCO Youth Hackathon 2026 · Theme: Media & Information Literacy*
