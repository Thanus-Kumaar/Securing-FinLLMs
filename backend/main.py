import hashlib
from datetime import datetime, timedelta
from typing import List
import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# --- Configuration and Setup ---

# This simulates an HSM (Hardware Security Module) for the JWT secret key.
# Will migrate this to env.
JWT_SECRET_KEY = "your-super-secret-key-that-should-be-kept-safe"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer for getting the JWT from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- Database Setup (Simulating MySQL with SQLite for a self-contained app) ---

SQLALCHEMY_DATABASE_URL = "sqlite:///./financial_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model for an Employee, representing the employee directory
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    roles = Column(String)  # Storing a comma-separated string of roles

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hardcoded data for a simple prototype.
# In a real system, these would be managed in the database.
mock_employees = [
    {"username": "teller1", "password": "password1", "roles": "teller,customer_service"},
    {"username": "advisor1", "password": "password2", "roles": "advisor,audit:log:read"},
    {"username": "manager1", "password": "password3", "roles": "manager,teller,transaction:approve:override"}
]

# Populate the database with mock employees (if it's empty)
def populate_db(db: Session):
    if db.query(Employee).count() == 0:
        for emp in mock_employees:
            hashed_pass = pwd_context.hash(emp["password"])
            db_employee = Employee(username=emp["username"], hashed_password=hashed_pass, roles=emp["roles"])
            db.add(db_employee)
        db.commit()

# --- Pydantic Models for Data Validation ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    roles: List[str]

class User(BaseModel):
    username: str

class AuthHandler:
    """
    Handles all authentication logic including password hashing and JWT encoding/decoding.
    """
    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, username, roles):
        """Generates a new JWT with user roles and expiration time."""
        payload = {
            "exp": datetime.now(tz=datetime.now().astimezone().tzinfo) + timedelta(minutes=JWT_EXPIRY_MINUTES),
            "iat": datetime.now(tz=datetime.now().astimezone().tzinfo),
            "sub": username,
            "roles": roles.split(',')
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def decode_token(self, token):
        """Decodes and validates a JWT."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

auth_handler = AuthHandler()

# --- FastAPI App and Routes ---

app = FastAPI(title="FinLLM Authorization Framework")

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    populate_db(db)
    db.close()

@app.post("/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticates an employee and returns a JWT with their roles.
    This simulates a successful MFA login and token issuance.
    """
    employee = db.query(Employee).filter(Employee.username == form_data.username).first()
    if not employee or not auth_handler.verify_password(form_data.password, employee.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_handler.encode_token(employee.username, employee.roles)
    return {"access_token": token, "token_type": "bearer"}

# Dependency function to get the current authenticated employee
def get_current_employee(token: str = Depends(oauth2_scheme)):
    payload = auth_handler.decode_token(token)
    return TokenData(username=payload.get("sub"), roles=payload.get("roles"))

# Dependency function for role-based access control
def role_required(required_roles: List[str]):
    def wrapper(current_employee: TokenData = Depends(get_current_employee)):
        for role in required_roles:
            if role in current_employee.roles:
                return current_employee
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to perform this action"
        )
    return wrapper

@app.get("/me", response_model=User, tags=["Protected"])
async def read_current_user(current_employee: TokenData = Depends(get_current_employee)):
    """
    An example of a protected endpoint that requires a valid JWT.
    """
    return {"username": current_employee.username}

@app.post("/financial-action", tags=["Protected"])
async def perform_financial_action(action: str, current_employee: TokenData = Depends(role_required(["teller"]))):
    """
    Performs a financial action, but only if the user has the 'teller' role.
    This demonstrates Role-Based Access Control (RBAC).
    """
    if action == "transfer":
        return {"message": f"Transfer initiated successfully by {current_employee.username}."}
    else:
        return {"message": f"Action '{action}' is not supported."}
