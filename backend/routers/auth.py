from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import AuthService
from services.intent_service import IntentService
from schemas.auth import Token, IntentRequest, IntentResponse, DelegationRequest, DelegationResponse
from core.security import get_current_employee, auth_handler

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

@router.post("/delegate", response_model=DelegationResponse)
def create_agent_token(
    request: DelegationRequest,
    auth_service: AuthService = Depends(),
    # The primary user token is used for authentication here
    current_employee_payload: dict = Depends(get_current_employee)
):
    """
    Creates a highly-scoped, short-lived JWT for the LLM agent.
    This is the Delegation Authority Module (DAM).
    """
    # The intent is already confirmed from a prior step in the frontend
    # and is part of the request body.
    if not request.intent.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delegate token for an unsafe intent."
        )
    
    # Generate the agent token with restricted scope
    agent_token = auth_service.delegate_token(
        username=current_employee_payload.get("sub"),
        roles=current_employee_payload.get("roles"),
        intent=request.intent
    )

    return DelegationResponse(agent_token=agent_token)