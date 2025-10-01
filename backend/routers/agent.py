from fastapi import APIRouter, Depends, HTTPException, status, Header
from services.execution_service import ExecutionService
from schemas.employee import ActionRequest
from typing import Annotated, Dict, Any

# NOTE: The prefix is intentionally different from /employee to signify 
# that this endpoint is only for machine/agent-to-machine communication, 
# relying on the delegation token.
router = APIRouter(prefix="/agent", tags=["Secured Agent Execution"])

# Dependency to extract the Agent Token from the Authorization header
def get_agent_token(authorization: Annotated[str, Header()]):
    """
    Extracts the Agent Token (Delegation Token) from the Authorization header.
    It expects the format: Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (Expected: Bearer <token>)"
        )
    return authorization.split(" ")[1]


@router.post("/execute")
def execute_agent_action(
    request: ActionRequest,
    agent_token: str = Depends(get_agent_token),
    execution_service: ExecutionService = Depends()
) -> Dict[str, Any]:
    """
    Endpoint that receives the delegated request and runs the full security pipeline.

    This endpoint enforces:
    1. Agent Token validation (Is it valid, is it expired?).
    2. Input Sanitization (LDG).
    3. Prompt Injection Check.
    4. Cryptographic Message Signing (ATV).
    5. Output Sanitization (LDG).
    6. Event Logging (ACL).
    """
    
    # The ActionRequest schema already performs Pydantic validation on the request body.

    try:
        result = execution_service.execute_secured_query(
            agent_token=agent_token,
            request=request
        )
        return result
    except HTTPException as e:
        # Re-raise explicit HTTP exceptions from the service layer
        raise e
    except RuntimeError as e:
        # Catch unexpected runtime errors (e.g., failed key loading)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution Failed: {e}"
        )