import axios, { AxiosError } from 'axios';
import type { Token } from './types';

export const BASE_URL = 'http://127.0.0.1:8000'; 

// Create a reusable Axios instance with a base URL
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000', // Update this to your backend URL
});

// Request Interceptor to add the JWT to every outgoing request
API.interceptors.request.use(
  (config) => {
    // Get the access token from local storage or wherever you store it
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response Interceptor to handle errors centrally
API.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle specific errors like 401 Unauthorized globally
    if (error.response?.status === 401) {
      console.error('Authentication error: Token is invalid or expired.');
      // You can add logic here to redirect to the login page or refresh the token
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default API;