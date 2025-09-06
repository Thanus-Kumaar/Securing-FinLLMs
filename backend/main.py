from fastapi import FastAPI
from db.base import Base
from db.session import engine
from routers import auth, employee

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinLLM Authorization Framework")

# Include routers
app.include_router(auth.router)
app.include_router(employee.router)
