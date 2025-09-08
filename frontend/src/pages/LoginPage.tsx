// src/pages/LoginPage.tsx
import React, { useState, useEffect } from 'react';
import { AuthService, EmployeeService } from '../api/services';
import type { User } from '../api/types';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // On mount, check for an existing token
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const currentUser = await EmployeeService.getCurrentUser();
          setUser(currentUser);
          setIsLoggedIn(true);
        } catch (err) {
          console.error('Failed to re-authenticate:', err);
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const token = await AuthService.login(formData);
      localStorage.setItem('access_token', token.access_token);
      setMessage('Login successful!');
      const currentUser = await EmployeeService.getCurrentUser();
      setUser(currentUser);
      setIsLoggedIn(true);
    } catch (err: any) {
      setError(err?.detail || 'Login failed. Please check your credentials.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsLoggedIn(false);
    setUser(null);
    setMessage('Logged out successfully.');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-50">
        <div className="w-full max-w-md p-8 space-y-6 bg-slate-900 shadow-xl rounded-lg">
          <h2 className="text-3xl font-bold text-center">
            Welcome, {user?.username}!
          </h2>
          <p className="text-center text-slate-400">
            You are successfully authenticated. Your session is active.
          </p>
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 text-white font-medium py-2 rounded-md hover:bg-red-700 transition-colors duration-200"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50">
      <div className="w-full max-w-md p-8 space-y-6 bg-slate-900 shadow-xl rounded-lg border border-slate-800">
        <div className="flex flex-col items-center">
          <h2 className="text-3xl font-bold text-center">Login</h2>
          <p className="text-center text-slate-400">
            Enter your credentials to access the FinLLM Framework.
          </p>
        </div>

        {error && <div className="text-red-400 text-sm text-center">{error}</div>}
        {message && (
          <div className="text-green-400 text-sm text-center">{message}</div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-2 mt-1 rounded-md bg-slate-800 text-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 mt-1 rounded-md bg-slate-800 text-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white font-medium py-2 rounded-md hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="text-sm text-center text-slate-500">
          Not authorized? Please contact your administrator.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
