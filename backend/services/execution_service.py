import os
import time
import base64
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

# --- Initialization of Cryptographic Keys and State (UNCHANGED) ---
try:
    # NOTE: The keys must be generated and stored in a 'keys/' directory
    PRIVATE_KEY: RSAPrivateKey = load_private_key("keys/private_key.pem", passphrase=os.getenv("KEY_PASSPHRASE"))
    PUBLIC_KEY: RSAPublicKey = load_public_key("keys/public_key.pem")
    print("ATV: RSA keys loaded successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to load cryptographic keys (ATV): {e}")

# Simple structure to store required claims for agent token validation
class AgentTokenClaims(BaseModel):
    sub: str
    roles: List[str]
    action: str
    target: str

class ExecutionService:
    def __init__(self):
        pass

    def _validate_agent_token(self, agent_token: str) -> AgentTokenClaims:
        """
        Validates the agent's restricted JWT and extracts key delegation claims.
        """
        try:
            payload = jwt.decode(
                agent_token, 
                os.getenv("JWT_SECRET_KEY"), 
                algorithms=["HS256"]
            )
            
            roles: List[str] = payload.get("roles", [])
            scope_claim = next((r for r in roles if r.startswith("scope_data=")), None)
            
            if not scope_claim:
                raise ValueError("Delegated scope data ('scope_data=...') not found in token.")
            
            encoded_value = scope_claim.split("=", 1)[1]
            padding_needed = 4 - (len(encoded_value) % 4)
            padded_value = encoded_value + ('=' * padding_needed)
            
            decoded_scope_data = base64.urlsafe_b64decode(padded_value).decode('utf-8')
            parts = decoded_scope_data.split(":", 1)
            
            if len(parts) != 2:
                 raise ValueError("Decoded scope data is malformed (expected action:target).")

            action = parts[0]
            target = parts[1]

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
        except (ValueError, IndexError, TypeError, base64.binascii.Error):
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
        Runs the full security and execution pipeline (LDG, ATV, ACL) with server-side transparency.
        """
        
        # 1. Validate Agent Token and Delegation Scope
        claims = self._validate_agent_token(agent_token)
        
        # Construct the user_input from the validated claims (the true intent)
        amount_str = str(request.amount) if request.amount is not None else "N/A"
        user_input = f"Action:{claims.action} Target:{claims.target} Amount:{amount_str}"

        # --- SERVER CONSOLE TRACE START ---
        print("\n--- SECURE EXECUTION TRACE ---")
        print(f"[{time.strftime('%H:%M:%S')}] User: {claims.sub} | Action: {claims.action} | Target: {claims.target}")
        print(f"ATV: Agent Token Decoded & Validated.")
        # --- END TRACE ---

        # --- SECURITY GATEWAY (LDG - Input) ---
        # 2. Input Sanitize (PII Masking, Entity Recognition)
        input_result = ldg_input_check(user_input)
        
        # 3. Prompt Injection Detection (Pre-Filter Check)
        inj_result = detect_prompt_injection(user_input)
        
        # --- SECURITY DECISION ---
        if input_result["status"] == "blocked":
            print(f"SDG: Input Blocked! Reason: {input_result['reason']}")
            log_event("query_blocked", {"reason": input_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=input_result["reason"])
        
        if inj_result["status"] == "blocked":
            print(f"SDG: PI Blocked! Reason: {inj_result['reason']}")
            log_event("query_blocked", {"reason": inj_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=inj_result["reason"])

        masked_input = input_result.get("masked_input", user_input)
        
        # --- MESSAGE INTEGRITY (ATV - Signing) ---
        try:
            signature = sign_request(masked_input, PRIVATE_KEY)
            valid = verify_signature(masked_input, signature, PUBLIC_KEY)
            
            print(f"SDG: PII Masked Query: '{masked_input}'")
            print(f"ATV: Signature Generated. Verification Status: {valid}")
            
        except Exception as e:
            print(f"ATV: Cryptographic Signing Failed! Error: {e}")
            log_event("security_fail", {"error": str(e), "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cryptographic signing failed.")

        # --- FCA (Simulated LLM Agent Execution) ---
        agent_response = f"FCA: Successfully executed '{claims.action}' for user {claims.sub} on target '{claims.target}'. Signed message verified: {valid}"

        # --- SECURITY GATEWAY (LDG - Output) ---
        output_result = ldg_output_check(agent_response)
        if output_result["status"] == "blocked":
            print(f"SDG: Output Blocked! Reason: {output_result['reason']}")
            log_event("output_blocked", {"reason": output_result["reason"], "user_sub": claims.sub})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=output_result["reason"])

        # --- AUDIT (ACL) ---
        event_id = log_event("query_success", {
            "user_sub": claims.sub,
            "delegated_action": claims.action,
            "input_original": user_input,
            "input_masked": masked_input,
            "signature_hex": signature.hex() if isinstance(signature, bytes) else "N/A",
            "atv_verified": valid,
            "agent_response": agent_response
        })
        
        print(f"ACL: Event Logged Successfully. ID: {event_id}")
        print("-----------------------------\n")

        return {
            "response": agent_response,
            "event_id": event_id,
            "status": "Transaction executed and logged successfully."
        }