from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from backend.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthHandler:
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, username: str, roles: str) -> str:
        expire = datetime.now() + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
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
