## Online Proctoring System (Full Stack)

### Tech stack
- **Frontend**: React (Vite), Custom CSS, Axios, React Router
- **Backend**: FastAPI, MongoDB (Motor), JWT Auth

---

## Folder structure
```
ProctoringSystem2/
  backend/
    app/
      core/
      db/
      models/
      routes/
      main.py
    requirements.txt
    .env.example
  frontend/
    src/
      api/
      components/
      pages/
      App.jsx
      main.jsx
      index.css
    index.html
    package.json
    vite.config.js
    .env.example
```

---

## Backend setup (FastAPI)

### 1) Create and activate a virtualenv
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
```bash
cp .env.example .env
```

Edit `.env`:
- `MONGODB_URI`: your MongoDB connection string
- `MONGODB_DB`: database name
- `JWT_SECRET_KEY`: set a strong secret

### 4) Run the backend
```bash
uvicorn app.main:app --reload --port 8000
```

API base URL: `http://localhost:8000`

Useful endpoints:
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

---

## Frontend setup (React)

### 1) Install dependencies
```bash
cd frontend
npm install
```

### 2) Configure environment variables
```bash
cp .env.example .env
```

Set:
- `VITE_API_BASE_URL=http://localhost:8000`

### 3) Run the frontend
```bash
npm run dev
```

Frontend URL (Vite): `http://localhost:5173`

---

## Default roles
- **student**
- **proctor**

Role is chosen during registration and returned in `/auth/me`.

