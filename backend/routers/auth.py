from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import AuthService
from services.intent_service import IntentService
from schemas.auth import Token, IntentRequest, IntentResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends()):
    return auth_service.login(form_data)

@router.post("/intent", response_model=IntentResponse)
def get_user_intent(request: IntentRequest, intent_service: IntentService = Depends()):
    """
    Analyzes a user's prompt using an external LLM to extract a structured intent.
    This serves as the User Intent Confirmation (UIC) component.
    """
    return intent_service.get_intent_from_prompt(request.prompt)