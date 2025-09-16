import React, { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { AuthService, EmployeeService } from "../api/services";
import type {
  IntentResponse,
  DelegationRequest,
  ActionRequest,
  User,
} from "../api/types";

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
      // Always set the intent to display details
      setIntent(intentResponse);

      // If not safe, also show the safety warning
      if (!intentResponse.is_safe) {
        setError(
          intentResponse.reasoning ||
            "The intent was flagged as unsafe. Please review carefully before proceeding."
        );
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
    // Prevent action if intent is not safe
    if (intent && !intent.is_safe) {
      setError(
        "Cannot proceed with unsafe intent. Please modify your request."
      );
      return;
    }

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
        axiosError.response?.data?.detail ||
          "Failed to perform the financial action."
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
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50 px-4">
        Loading user data...
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-50 p-4 sm:p-8">
      <div className="w-full max-w-sm sm:max-w-2xl lg:max-w-4xl p-6 sm:p-8 space-y-6 sm:space-y-8 bg-slate-900 shadow-xl rounded-lg border border-slate-800">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
          <h2 className="text-2xl sm:text-3xl font-bold">FinLLM Dashboard</h2>
          <button
            onClick={onLogout}
            className="w-full sm:w-auto px-4 py-2 text-sm font-medium bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors duration-200"
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
          <div className="p-3 sm:p-4 bg-red-900/50 text-red-400 rounded-lg text-sm sm:text-base">
            {error}
          </div>
        )}
        {message && (
          <div className="p-3 sm:p-4 bg-green-900/50 text-green-400 rounded-lg text-sm sm:text-base">
            {message}
          </div>
        )}

        {!intent ? (
          <form onSubmit={handlePromptSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Enter a financial request for the agent:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full p-3 rounded-md bg-slate-800 text-slate-50 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base resize-none"
                placeholder="e.g., 'Transfer $100 from my checking account to savings.'"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white font-medium py-3 sm:py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
              disabled={loading}
            >
              {loading ? "Analyzing Intent..." : "Analyze Intent"}
            </button>
          </form>
        ) : (
          <div className="space-y-4 sm:space-y-6">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg sm:text-xl font-semibold text-yellow-300">
                User Intent Analysis
              </h3>
              {!intent.is_safe && (
                <span className="px-2 py-1 text-xs bg-red-900/50 text-red-300 rounded-full border border-red-700">
                  ⚠️ Unsafe
                </span>
              )}
              {intent.is_safe && (
                <span className="px-2 py-1 text-xs bg-green-900/50 text-green-300 rounded-full border border-green-700">
                  ✓ Safe
                </span>
              )}
            </div>

            <p className="text-sm sm:text-base text-slate-400">
              The agent has parsed your request. Please review the details
              carefully
              {!intent.is_safe && " and note the safety concerns"} before
              proceeding.
            </p>

            <div className="p-4 bg-slate-800 rounded-md space-y-3 border border-slate-700">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm sm:text-base">
                <div>
                  <span className="text-slate-400">Action:</span>{" "}
                  <span className="text-blue-400 font-medium">
                    {intent.action}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Target:</span>{" "}
                  <span className="text-blue-400 font-medium">
                    {intent.target || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Amount:</span>{" "}
                  <span className="text-blue-400 font-medium">
                    {intent.amount || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Unit:</span>{" "}
                  <span className="text-blue-400 font-medium">
                    {intent.unit || "N/A"}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-700">
                <div className="mb-2">
                  <span className="text-slate-400">Confidence:</span>{" "}
                  <span
                    className={`font-medium ${
                      intent.confidence_score >= 0.8
                        ? "text-green-400"
                        : intent.confidence_score >= 0.6
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {(intent.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Analysis:</span>
                  <p className="text-slate-300 italic text-sm mt-1 leading-relaxed">
                    {intent.reasoning}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              <button
                onClick={handleConfirmAction}
                className={`flex-1 font-medium py-3 sm:py-2 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base ${
                  intent.is_safe
                    ? "bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                    : "bg-gray-600 text-gray-300 cursor-not-allowed"
                }`}
                disabled={loading || !intent.is_safe}
                title={
                  !intent.is_safe ? "Cannot proceed with unsafe intent" : ""
                }
              >
                {loading
                  ? "Processing..."
                  : intent.is_safe
                  ? "Confirm Action"
                  : "Action Blocked"}
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 bg-gray-600 text-white font-medium py-3 sm:py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-colors duration-200 disabled:opacity-50 text-sm sm:text-base"
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
