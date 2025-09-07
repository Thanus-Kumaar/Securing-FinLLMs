from fastapi import APIRouter, Depends, HTTPException, status
from schemas.employee import User, ActionRequest
from schemas.auth import TokenData
from core.security import auth_handler
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/employee", tags=["Protected"])

# Dependency function to get the current authenticated employee
def get_current_employee(token: str = Depends(oauth2_scheme)) -> TokenData:
    payload = auth_handler.decode_token(token)
    return TokenData(username=payload.get("sub"), roles=payload.get("roles"))

# Dependency function for role-based access control
def role_required(required_roles: List[str]):
    def wrapper(current_employee: TokenData = Depends(get_current_employee)):
        if not any(role in current_employee.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_employee
    return wrapper

@router.get("/me", response_model=User)
def read_current_user(current_employee: TokenData = Depends(get_current_employee)):
    return {"username": current_employee.username}

@router.post("/financial-action")
def perform_financial_action(
    request: ActionRequest,
    current_employee: TokenData = Depends(role_required(["teller"]))
):
    if request.action == "transfer":
        return {"message": f"Transfer initiated by {current_employee.username}."}
    return {"message": f"Action '{request.action}' is not supported."}