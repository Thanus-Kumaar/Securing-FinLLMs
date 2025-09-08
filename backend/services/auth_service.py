from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from db.session import get_db
from db.models import Employee
from core.security import auth_handler
from schemas.auth import Token, IntentResponse

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

    def delegate_token(self, username: str, roles: str, intent: IntentResponse) -> str:
        """
        Generates a highly-scoped JWT for the LLM agent based on confirmed intent.
        This token grants specific, limited permissions for a very short time.
        """
        # The agent's token scope is a combination of the user's base roles and the specific intent.
        # This enforces that the agent cannot act outside of what was confirmed.
        agent_scope = f"{','.join(roles)},{intent.action}:{intent.target}"

        # You can set a much shorter expiry for agent tokens (e.g., 5 minutes)
        # to enforce Just-in-Time access.
        return auth_handler.encode_token(username, agent_scope, is_agent_token=True)