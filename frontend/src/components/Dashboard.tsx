import React from "react";
import { useAuth } from "../hooks/useAuth";
import PatientDashboard from "./PatientDashboard";
import HospitalDashboard from "./HospitalDashboard";

const Dashboard: React.FC = () => {
  const { appUser } = useAuth();

  // Route to appropriate dashboard based on user type
  if (appUser?.userType === "patient") {
    return <PatientDashboard />;
  }

  if (appUser?.userType === "institution") {
    return <HospitalDashboard />;
  }

  // Fallback for unknown user types
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Unknown User Type
        </h2>
        <p className="text-gray-600">
          Unable to determine the appropriate dashboard for your account.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
