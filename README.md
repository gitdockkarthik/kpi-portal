# KPI Portal

Infrastructure & Operations KPI tracking portal. FastAPI backend, PostgreSQL database, vanilla HTML/CSS/JS frontend with Chart.js.

## Local development

### Prerequisites
- Docker & Docker Compose

### Start

```bash
cp .env.example .env
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000       |
| Backend  | http://localhost:8000       |
| API docs | http://localhost:8000/docs  |

The database is seeded automatically on first start via `db/init.sql`.

---

## Railway deployment

### Architecture on Railway
Railway runs each Docker Compose service as a separate Railway service within one project.

### Step-by-step

#### 1. Create a Railway project

```bash
railway login
railway init          # creates a new project
```

#### 2. Provision a PostgreSQL plugin

In the Railway dashboard → your project → **New** → **Database** → **PostgreSQL**.  
Railway injects `DATABASE_URL` automatically into services in the same project.

#### 3. Deploy the backend

```bash
cd backend
railway up --service backend
```

Set the environment variable in Railway dashboard → backend service → **Variables**:

```
DATABASE_URL=<copied from the PostgreSQL plugin's Connect tab>
```

> Railway's `DATABASE_URL` starts with `postgresql://` — the backend's `database.py` rewrites the scheme to `postgresql+asyncpg://` automatically.

Run the seed SQL once against the Railway Postgres instance:

```bash
railway run psql $DATABASE_URL -f db/init.sql
```

#### 4. Deploy the frontend

The frontend is static HTML — serve it from Railway using an nginx Dockerfile or any static hosting (Netlify, Vercel, GitHub Pages).

**One-line switch to Railway URL**: at the top of each HTML file, change the single `CONFIG` object:

```js
// index.html, input.html, dashboard.html, admin.html — each has this at the top of the <script>:
const CONFIG = { apiBase: 'https://your-backend-service.up.railway.app' };
```

Replace `http://localhost:8000` with your Railway backend public URL.

#### 5. Enable CORS (already configured)

The backend's `main.py` uses `allow_origins=["*"]`. For production, restrict this to your frontend domain:

```python
allow_origins=["https://your-frontend.up.railway.app"]
```

---

## Project structure

```
kpi-portal/
├── db/
│   └── init.sql          # Schema + full seed data
├── backend/
│   ├── main.py           # FastAPI app + all routes
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── database.py       # Async engine + session factory
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html        # Home / landing page
│   ├── input.html        # Add / Edit / Delete KPIs & Tasks
│   ├── dashboard.html    # 5-view dashboard
│   └── admin.html        # Manage teams, pillars, lookups
├── docker-compose.yml
├── .env.example
└── README.md
```

## RAG logic

RAG status is **always computed, never stored**:

| Range              | RAG    | Colour  |
|--------------------|--------|---------|
| pct_complete ≥ 0.75 | Green | #28a745 |
| pct_complete ≥ 0.40 | Amber | #ffc107 |
| pct_complete < 0.40 | Red   | #dc3545 |

- **KPI** pct = AVG(tasks.pct_complete) for that KPI  
- **Pillar** pct = AVG across all KPIs in the pillar  
- **Team** pct = AVG across all tasks for that team  

## API reference

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | /pillars | List pillars |
| GET | /teams | List teams |
| GET | /kpis | List KPIs (filter: team_id, pillar_id) |
| GET | /tasks | List tasks (filter: team_id, kpi_id, report_period_id) |
| GET | /dashboard/vp-summary | Overall + pillar + team RAG rollup |
| GET | /dashboard/kpi-progress | Per-KPI completion + RAG |
| GET | /dashboard/pillar-view | Pillar accordion with nested KPIs |
| GET | /dashboard/task-drill | Task-level drill (filter: team_id, kpi_id) |
| GET | /dashboard/blocked-at-risk | Blocked tasks + Amber-RAG tasks |
