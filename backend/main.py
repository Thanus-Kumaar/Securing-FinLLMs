from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.base import Base
from db.session import engine, get_db
from routers import auth, employee, agent
from db.models import Employee
from core.security import auth_handler
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# NEW: Import ACL initialization function
from core.acl import init_db # Assuming acl.py is accessible in the Python path

# Hardcoded data for a simple prototype.
mock_employees = [
    {"username": "teller1", "password": "password1", "roles": "teller,customer_service"},
    {"username": "advisor1", "password": "password2", "roles": "advisor,audit_reader"},
    {"username": "manager1", "password": "password3", "roles": "manager,teller,transaction_override"}
]

# Function to create initial users
def create_initial_users(db: Session):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if db.query(Employee).count() == 0:
        for emp in mock_employees:
            hashed_pass = pwd_context.hash(emp["password"])
            db_employee = Employee(username=emp["username"], hashed_password=hashed_pass, roles=emp["roles"])
            db.add(db_employee)
        db.commit()
        print("Database populated with initial users.")

# The new lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # 1. Initialize the Encrypted Audit Ledger DB (acl.db)
    init_db()
    
    # 2. Initialize the main application DB (SQLAlchemy)
    Base.metadata.create_all(bind=engine)
    
    # 3. Create initial users if DB is empty
    db = next(get_db())
    try:
        create_initial_users(db)
    finally:
        db.close()
    
    yield
    # --- SHUTDOWN LOGIC (None currently) ---

app = FastAPI(title="FinLLM Authorization Framework", lifespan=lifespan)

# For development only - allows all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins (development only!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(agent.router)
