import base64 # NEW IMPORT
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from db.session import get_db
from db.models import Employee
from core.security import auth_handler
from schemas.auth import Token, IntentResponse
from typing import List

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        employee = self.db.query(Employee).filter(Employee.username == form_data.username).first()
        if not employee or not auth_handler.verify_password(form_data.password, employee.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth_handler.encode_token(employee.username, employee.roles)
        return Token(access_token=token, token_type="bearer")

    def delegate_token(self, username: str, roles: List[str], intent: IntentResponse) -> str:
        """
        Generates a highly-scoped JWT for the LLM agent based on confirmed intent.
        FIX: Base64-encodes the specific delegation target to prevent delimiter conflicts.
        """
        full_scope_data = f"{intent.action}:{intent.target}"
        encoded_scope = base64.urlsafe_b64encode(full_scope_data.encode('utf-8')).decode('utf-8').rstrip('=')
        roles_list = roles + [f"scope_data={encoded_scope}"]
        agent_roles_str = ",".join(roles_list)

        return auth_handler.encode_token(username, agent_roles_str, is_agent_token=True)
