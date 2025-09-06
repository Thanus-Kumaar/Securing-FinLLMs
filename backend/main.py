from fastapi import FastAPI
from backend.db.base import Base
from backend.db.session import engine
from backend.routers import auth, employee

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinLLM Authorization Framework")

# Include routers
app.include_router(auth.router)
app.include_router(employee.router)
