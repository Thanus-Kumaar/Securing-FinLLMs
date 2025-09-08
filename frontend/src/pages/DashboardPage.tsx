// src/pages/DashboardPage.tsx
import React from "react";

const DashboardPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto mt-12">
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
      <p className="text-slate-400">
        This is a placeholder dashboard. Once authenticated, you can add
        employee or financial features here.
      </p>
    </div>
  );
};

export default DashboardPage;
