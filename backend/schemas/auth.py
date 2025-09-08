from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    roles: List[str]

class IntentRequest(BaseModel):
    prompt: str

class IntentResponse(BaseModel):
    action: str
    target: Optional[str]
    amount: Optional[float]
    unit: Optional[str]
    is_safe: bool
    confidence_score: float
    reasoning: Optional[str]

class DelegationRequest(BaseModel):
    user_token: str
    intent: IntentResponse

class DelegationResponse(BaseModel):
    agent_token: str