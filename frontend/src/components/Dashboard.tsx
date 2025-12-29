import React from "react";
import { useAuth } from "../hooks/useAuth";
import PatientDashboard from "./PatientDashboard";

const Dashboard: React.FC = () => {
  const { appUser, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  // Route to appropriate dashboard based on user type
  if (appUser?.userType === "patient") {
    return <PatientDashboard />;
  }

  // Hospital dashboard (placeholder for now)
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              HealthInsight Dashboard
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">
                Welcome, {appUser?.name || "User"}
              </span>
              <span className="px-2 py-1 text-xs font-semibold bg-primary-100 text-primary-800 rounded-full">
                {appUser?.userType}
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Hospital Dashboard Coming Soon
              </h2>
              <p className="text-gray-600">
                Hospital dashboard features will be implemented here.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
