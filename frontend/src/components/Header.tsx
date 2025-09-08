// src/components/Header.tsx
import { Link } from "react-router-dom";

const Header: React.FC = () => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 shadow-md">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <Link to="/dashboard" className="text-xl font-bold text-blue-400">
          FinLLM
        </Link>
        <nav className="flex gap-6 text-slate-300">
          <Link
            to="/dashboard"
            className="hover:text-blue-400 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            to="/login"
            className="hover:text-blue-400 transition-colors"
          >
            Login
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
