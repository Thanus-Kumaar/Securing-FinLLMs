# 🏦 FinLLM Authorization Framework

This project is a **FastAPI + Python backend** with a **frontend** (likely JS/React/etc.).  
It demonstrates secure authentication, role-based access control (RBAC), and database integration.

---

## 📂 Repository Structure

.
├── backend/                 # Python FastAPI backend
│   ├── main.py              # Entry point (creates FastAPI app, includes routers)
│   │
│   ├── core/                # Core settings and security
│   │   ├── config.py        # App settings (env vars, secrets, DB URL, JWT config)
│   │   └── security.py      # Password hashing, JWT encode/decode utilities
│   │
│   ├── db/                  # Database setup (SQLAlchemy)
│   │   ├── base.py          # Declarative Base class for ORM models
│   │   ├── models.py        # Database models (e.g., Employee)
│   │   └── session.py       # DB engine + session dependency
│   │
│   ├── routers/             # API route handlers (split by feature)
│   │   ├── auth.py          # Authentication endpoints (/auth/login)
│   │   └── employee.py      # Employee endpoints (/employee/me, /financial-action)
│   │
│   ├── schemas/             # Pydantic models (request/response validation)
│   │   ├── auth.py          # Token, TokenData
│   │   └── employee.py      # User, ActionRequest
│   │
│   └── services/            # Business logic (separate from routes)
│       └── auth_service.py  # Login/authentication logic
│
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Example environment variables (copy to `.env`)
│
├── frontend/                # Frontend app (JS/React/Vue/etc.)
│   └── ...                  # Frontend source code lives here
│
├── .gitignore               # Files and folders Git should ignore
└── README.md                # Project documentation (this file)

---

## ⚙️ Setup Instructions

### Backend

1. Navigate into backend folder:
   cd backend

2. Create & activate virtual environment:
   python -m venv .venv
   source .venv/bin/activate     # Linux/macOS
   .venv\\Scripts\\Activate        # Windows PowerShell

3. Install dependencies:
   pip install -r requirements.txt

4. Run the app with Uvicorn:
   uvicorn app.main:app --reload

5. Visit:
   - API: http://127.0.0.1:8000
   - Swagger UI Docs: http://127.0.0.1:8000/docs
   - ReDoc Docs: http://127.0.0.1:8000/redoc

---

### Frontend

Go into the `frontend/` folder and follow the framework-specific setup (React, Vue, etc.).  
Typically:

cd frontend
npm install
npm run dev

---

## 🧩 Why This Structure?

- core/ → app-wide settings & security (like config in Go or `.env` + utils in JS)  
- db/ → database setup (keeps models & session separate)  
- routers/ → organizes routes per feature (like Express routers or Go handlers)  
- schemas/ → Pydantic models for validation (like TypeScript interfaces + Joi validation in JS)  
- services/ → business logic layer (keeps routers thin)  
- main.py → app entrypoint, only responsible for creating FastAPI app and including routers  

This separation makes the project:
- Easier to scale (just add new router/service/schema)  
- Easier to test (unit test services without touching routes)  
- Easier for teams (clear ownership of features/modules)  

---

## 📌 Next Steps
- Add architecture diagram here (system components, auth flow, DB interactions).  
- Expand documentation (e.g., role hierarchy, API usage examples).  
- Add Alembic migrations for DB schema changes.  
- Write tests using pytest + FastAPI TestClient.  

---

## 🧑‍💻 Developer Notes
- Always create a new virtual environment (`.venv`) per project.  
- Never commit `.venv` or `.env` files (use `.gitignore`).  
- Document any new APIs by tagging routers and using response models.  
- Keep secrets out of source code — store them in `.env` instead.  