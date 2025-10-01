import axios from "axios";
import API, { BASE_URL } from "./index";
import type {
  Token,
  IntentRequest,
  IntentResponse,
  DelegationRequest,
  DelegationResponse,
  User,
  ActionRequest,
} from "./types";
import type { AxiosResponse } from "axios";

interface ExecutionResponse {
    response: string; 
    event_id: number; 
    status: string; 
}

// --- Authentication Service ---
export const AuthService = {
  // POST to /auth/login
  login: async (formData: FormData): Promise<Token> => {
    const response: AxiosResponse<Token> = await API.post(
      "/auth/login",
      formData,
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    );
    return response.data;
  },

  // POST to /auth/intent
  getIntent: async (prompt: string): Promise<IntentResponse> => {
    const response: AxiosResponse<IntentResponse> = await API.post(
      "/auth/intent",
      { prompt }
    );
    return response.data;
  },

  // POST to /auth/delegate
  delegateToken: async (
    request: DelegationRequest
  ): Promise<DelegationResponse> => {
    const response: AxiosResponse<DelegationResponse> = await API.post(
      "/auth/delegate",
      request
    );
    return response.data;
  },
};

// --- Employee & Financial Service ---
export const EmployeeService = {
  // GET to /employee/me
  getCurrentUser: async (): Promise<User> => {
    const response: AxiosResponse<User> = await API.get("/employee/me");
    return response.data;
  },

  // POST to /agent/execute (Uses agentToken directly in header)
  performAction: async (
        agentToken: string, 
        request: ActionRequest
    ): Promise<ExecutionResponse> => {
        
        // FIX: Create a clean, temporary Axios instance that does NOT rely on the 
        // global interceptor's token, ensuring only the agentToken is sent.
        const agentAPI = axios.create({ baseURL: BASE_URL });

        const response: AxiosResponse<ExecutionResponse> = 
            await agentAPI.post(
                '/agent/execute', 
                request, 
                {
                    // Explicitly set the Authorization header with the agentToken
                    headers: { 
                        Authorization: `Bearer ${agentToken}`,
                        'Content-Type': 'application/json' 
                    },
                }
            );
        return response.data;
    },
};
