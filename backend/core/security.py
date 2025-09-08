from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from core.config import settings
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthHandler:
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, username: str, roles: str, is_agent_token: bool = False) -> str:
        expiry_minutes = 2 if is_agent_token else settings.JWT_EXPIRY_MINUTES
        expire = datetime.now() + timedelta(minutes=expiry_minutes)

        payload = {
            "sub": username,
            "roles": roles.split(","),
            "exp": expire,
            "iat": datetime.now(),
            "auth": settings.SERVER_ID,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

auth_handler = AuthHandler()

def get_current_employee(token: str = Depends(oauth2_scheme)):
    """
    Dependency that decodes and validates a JWT from the request header.
    Raises a 401 if the token is invalid or missing.
    """
    payload = auth_handler.decode_token(token)
    return payload

def role_required(required_roles: List[str]):
    """
    Dependency that ensures the authenticated user has one of the required roles.
    Raises a 403 if permissions are insufficient.
    """
    def wrapper(current_employee: dict = Depends(get_current_employee)):
        user_roles = current_employee.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_employee
    return wrapper