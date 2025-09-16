import React, { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { AuthService, EmployeeService } from "../api/services";
import type { IntentResponse, DelegationRequest, ActionRequest, User } from "../api/types";

// Explicitly define the component's props with a type
interface DashboardProps {
  onLogout: () => void;
}

interface ApiErrorResponse {
  detail: string;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  // Use TypeScript to define the state types
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>("");
  const [intent, setIntent] = useState<IntentResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  // Fetch user details on component mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const currentUser = await EmployeeService.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        onLogout();
      }
    };
    fetchUser();
  }, [onLogout]);

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const intentResponse = await AuthService.getIntent(prompt);
      if (intentResponse.is_safe) {
        setIntent(intentResponse);
      } else {
        setError(
          intentResponse.reasoning ||
          "The intent was flagged as unsafe and cannot be processed."
        );
        setIntent(null);
      }
    } catch (err) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      setError(
        axiosError.response?.data?.detail || "Failed to get intent from prompt."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAction = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const userToken = localStorage.getItem("access_token");
      if (!userToken) {
        throw new Error("No user token found. Please log in again.");
      }

      if (!intent) {
        throw new Error("No intent to confirm.");
      }

      // Step 1: Delegate a token for the LLM agent using the confirmed intent
      const delegateRequest: DelegationRequest = {
        user_token: userToken,
        intent: intent,
      };
      const delegateResponse = await AuthService.delegateToken(delegateRequest);
      const agentToken = delegateResponse.agent_token;

      // Step 2: Use the agent's token to perform the final action
      const actionRequest: ActionRequest = {
        action: intent.action,
        amount: intent.amount,
        account_id: intent.target,
      };
      const actionResponse = await EmployeeService.performAction(actionRequest);

      setMessage(actionResponse.message);
      setIntent(null); // Reset intent after action
    } catch (err) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      setError(
        axiosError.response?.data?.detail || "Failed to perform the financial action."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIntent(null);
    setPrompt("");
    setError("");
    setMessage("Action cancelled. Ready for a new prompt.");
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50">
        Loading user data...
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-50 p-4 sm:p-8">
      <div className="w-full max-w-2xl p-8 space-y-8 bg-slate-900 shadow-xl rounded-lg border border-slate-800">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold">FinLLM Dashboard</h2>
          <button
            onClick={onLogout}
            className="px-4 py-2 text-sm font-medium bg-red-600 rounded-md hover:bg-red-700 transition-colors duration-200"
          >
            Logout
          </button>
        </div>

        <div className="text-sm text-slate-400">
          Welcome back,{" "}
          <span className="font-semibold text-white">{user.username}</span>.
          <br />
          Your role gives you access to specific financial actions.
        </div>

        {error && (
          <div className="p-4 bg-red-900/50 text-red-400 rounded-lg">
            {error}
          </div>
        )}
        {message && (
          <div className="p-4 bg-green-900/50 text-green-400 rounded-lg">
            {message}
          </div>
        )}

        {!intent ? (
          <form onSubmit={handlePromptSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-300">
                Enter a financial request for the agent:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full p-3 mt-1 rounded-md bg-slate-800 text-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 'Transfer $100 from my checking account to savings.'"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-medium py-2 rounded-md hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? "Analyzing Intent..." : "Analyze Intent"}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-yellow-300">
              User Intent Confirmation
            </h3>
            <p className="text-slate-400">
              The agent has parsed your request. Please confirm the details
              before proceeding.
            </p>
            <div className="p-4 bg-slate-800 rounded-md space-y-2">
              <p>
                <strong>Action:</strong>{" "}
                <span className="text-blue-400">{intent.action}</span>
              </p>
              <p>
                <strong>Target:</strong>{" "}
                <span className="text-blue-400">{intent.target || "N/A"}</span>
              </p>
              <p>
                <strong>Amount:</strong>{" "}
                <span className="text-blue-400">{intent.amount || "N/A"}</span>
              </p>
              <p>
                <strong>Unit:</strong>{" "}
                <span className="text-blue-400">{intent.unit || "N/A"}</span>
              </p>
              <p>
                <strong>Confidence:</strong>{" "}
                <span className="text-blue-400">
                  {(intent.confidence_score * 100).toFixed(2)}%
                </span>
              </p>
              <p>
                <strong>Reasoning:</strong>{" "}
                <span className="text-slate-300 italic">
                  {intent.reasoning}
                </span>
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={handleConfirmAction}
                className="flex-1 bg-green-600 text-white font-medium py-2 rounded-md hover:bg-green-700 transition-colors duration-200 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? "Confirming..." : "Confirm Action"}
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 bg-gray-600 text-white font-medium py-2 rounded-md hover:bg-gray-700 transition-colors duration-200"
                disabled={loading}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
