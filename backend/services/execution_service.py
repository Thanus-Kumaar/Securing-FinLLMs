import os
import time
from typing import Dict, Any, List
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from jose import jwt, JWTError
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

# Import core security and audit components
from core.acl import log_event
from core.atv import load_private_key, load_public_key, sign_request, verify_signature
from core.ldg import ldg_input_check, detect_prompt_injection, ldg_output_check
from schemas.employee import ActionRequest # Used for input validation

# --- Initialization of Cryptographic Keys and State ---
# This mirrors the setup logic from your friend's original app.py, 
# ensuring keys are loaded only once.
try:
    # NOTE: The keys must be generated and stored in a 'keys/' directory
    # The passphrase and encryption key are assumed to be loaded via dotenv in main.py
    PRIVATE_KEY: RSAPrivateKey = load_private_key("keys/private_key.pem", passphrase=os.getenv("KEY_PASSPHRASE"))
    PUBLIC_KEY: RSAPublicKey = load_public_key("keys/public_key.pem")
    print("ATV: RSA keys loaded successfully.")
except Exception as e:
    # Fail fast if keys are missing or invalid
    raise RuntimeError(f"Failed to load cryptographic keys (ATV): {e}")

# Simple structure to store required claims for agent token validation
class AgentTokenClaims(BaseModel):
    sub: str  # Subject (username)
    roles: List[str]
    action: str
    target: str

class ExecutionService:
    def __init__(self):
        # We don't use FastAPI Depends here, as this service is instantiated
        # directly in the router and uses globally loaded keys/logging functions.
        pass

    def _validate_agent_token(self, agent_token: str) -> AgentTokenClaims:
        """
        Validates the agent's restricted JWT and extracts key delegation claims.
        """
        try:
            # 1. Decode and verify the token signature
            payload = jwt.decode(
                agent_token, 
                os.getenv("JWT_SECRET_KEY"), # Assuming JWT secret is available in environment 
                algorithms=["HS256"]
            )
            
            # 2. Extract the specific delegated scope (action:target)
            roles: List[str] = payload.get("roles", [])
            
            # The last element of roles contains the specific action scope (e.g., 'teller,transfer:savings_account')
            # Find the most specific scope claim
            specific_scope = next((r for r in roles if ":" in r), None)
            
            if not specific_scope:
                raise ValueError("Delegated scope not found in token.")
            
            action, target = specific_scope.split(":", 1)

            return AgentTokenClaims(
                sub=payload.get("sub"),
                roles=roles,
                action=action,
                target=target
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Agent Delegation Token."
            )
        except (ValueError, IndexError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed Agent Token. Delegation scope is unreadable."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token validation failed: {e}"
            )

    def execute_secured_query(self, agent_token: str, request: ActionRequest) -> Dict[str, Any]:
        """
        Runs the full security and execution pipeline (LDG, ATV, ACL).
        """
        
        # 1. Validate Agent Token and Delegation Scope
        claims = self._validate_agent_token(agent_token)
        
        # The agent's token is built on the confirmed intent, so we treat the action request 
        # as the input provided by the agent to the system.
        user_input = f"{claims.action} {claims.target} for {request.amount}" 

        # --- SECURITY GATEWAY (LDG - Input) ---
        # 2. Input Sanitize (PII Masking, Entity Recognition)
        input_result = ldg_input_check(user_input)
        if input_result["status"] == "blocked":
            log_event("query_blocked", {"reason": input_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=input_result["reason"])
        
        masked_input = input_result.get("masked_input", user_input)
        
        # 3. Prompt Injection Detection (Pre-Filter Check)
        inj_result = detect_prompt_injection(user_input)
        if inj_result["status"] == "blocked":
            log_event("query_blocked", {"reason": inj_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=inj_result["reason"])

        # --- MESSAGE INTEGRITY (ATV - Signing) ---
        # 4. Sign the Sanitized Message (Proof of execution environment integrity)
        try:
            signature = sign_request(masked_input, PRIVATE_KEY)
            
            # 5. Self-Verification (Check integrity before proceeding)
            valid = verify_signature(masked_input, signature, PUBLIC_KEY)
        except Exception as e:
            log_event("security_fail", {"error": str(e), "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cryptographic signing failed.")

        # --- FCA (Simulated LLM Agent Execution) ---
        # In a real system, this would be the call to the actual LLM API.
        agent_response = f"FCA: Successfully executed '{claims.action}' for user {claims.sub}. Signed message verified: {valid}"

        # --- SECURITY GATEWAY (LDG - Output) ---
        # 6. Output Sanitization Check
        output_result = ldg_output_check(agent_response)
        if output_result["status"] == "blocked":
            log_event("output_blocked", {"reason": output_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=output_result["reason"])

        # --- AUDIT (ACL) ---
        # 7. Log the complete, successful event (payload is encrypted by ACL)
        event_id = log_event("query_success", {
            "user_sub": claims.sub,
            "delegated_action": claims.action,
            "input_original": user_input,
            "input_masked": masked_input,
            "signature_hex": signature.hex() if isinstance(signature, bytes) else "N/A",
            "atv_verified": valid,
            "agent_response": agent_response
        })

        return {
            "response": agent_response,
            "event_id": event_id,
            "status": "Transaction executed and logged successfully."
        }
