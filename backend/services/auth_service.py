from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.db.session import get_db
from backend.db.models import Employee
from backend.core.security import auth_handler
from backend.schemas.auth import Token

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        # Expects the frontend to send password without hashing - I know this is a security concern, but jsut a small project, so =)
        employee = self.db.query(Employee).filter(Employee.username == form_data.username).first()
        if not employee or not auth_handler.verify_password(form_data.password, employee.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth_handler.encode_token(employee.username, employee.roles)
        return Token(access_token=token, token_type="bearer")
