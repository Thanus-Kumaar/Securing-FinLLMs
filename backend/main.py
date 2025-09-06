from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.routers import auth, employee

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinLLM Authorization Framework")

# Include routers
app.include_router(auth.router)
app.include_router(employee.router)
