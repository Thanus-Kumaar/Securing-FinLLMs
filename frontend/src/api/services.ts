import API from './index';
import type {
  Token,
  IntentRequest,
  IntentResponse,
  DelegationRequest,
  DelegationResponse,
  User,
  ActionRequest
} from './types';
import type { AxiosResponse } from 'axios';

// --- Authentication Service ---
export const AuthService = {
  // POST to /auth/login
  login: async (formData: FormData): Promise<Token> => {
    const response: AxiosResponse<Token> = await API.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  // POST to /auth/intent
  getIntent: async (prompt: string): Promise<IntentResponse> => {
    const response: AxiosResponse<IntentResponse> = await API.post('/auth/intent', { prompt });
    return response.data;
  },

  // POST to /auth/delegate
  delegateToken: async (request: DelegationRequest): Promise<DelegationResponse> => {
    const response: AxiosResponse<DelegationResponse> = await API.post('/auth/delegate', request);
    return response.data;
  },
};

// --- Employee & Financial Service ---
export const EmployeeService = {
  // GET to /employee/me
  getCurrentUser: async (): Promise<User> => {
    const response: AxiosResponse<User> = await API.get('/employee/me');
    return response.data;
  },

  // POST to /employee/financial-action
  performAction: async (request: ActionRequest): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await API.post('/employee/financial-action', request);
    return response.data;
  },
};