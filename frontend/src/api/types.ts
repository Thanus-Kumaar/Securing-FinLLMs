// Corresponds to backend's schemas/auth.py
export interface Token {
  access_token: string;
  token_type: string;
}

export interface TokenData {
  username: string;
  roles: string[];
}

export interface IntentRequest {
  prompt: string;
}

export interface IntentResponse {
  action: string;
  target: string | null;
  amount: number | null;
  unit: string | null;
  is_safe: boolean;
  confidence_score: number;
  reasoning: string | null;
}

export interface DelegationRequest {
  user_token: string;
  intent: IntentResponse;
}

export interface DelegationResponse {
  agent_token: string;
}

// Corresponds to backend's schemas/employee.py
export interface User {
  username: string;
}

export interface ActionRequest {
  action: string;
  amount: number;
  account_id: string;
  description?: string | null;
}