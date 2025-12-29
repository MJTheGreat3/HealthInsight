import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import LoginForm from "./components/auth/LoginForm";
import RegisterForm from "./components/auth/RegisterForm";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import Dashboard from "./components/Dashboard";
import UploadPage from "./components/UploadPage";
import ResultsPage from "./components/ResultsPage";
import ReportHistory from "./components/ReportHistory";
import ProfilePage from "./components/ProfilePage";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            {/* Patient-only routes */}
            <Route
              path="/patient/dashboard"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/upload"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <UploadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/results/:reportId"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <ResultsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/history"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <ReportHistory />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/profile"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/patient/*"
              element={
                <ProtectedRoute requiredUserType="patient">
                  <div className="p-8 text-center">
                    <h2 className="text-2xl font-bold">Patient Area</h2>
                    <p>Patient-specific features will be implemented here.</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Hospital-only routes */}
            <Route
              path="/hospital/*"
              element={
                <ProtectedRoute requiredUserType="institution">
                  <div className="p-8 text-center">
                    <h2 className="text-2xl font-bold">Hospital Area</h2>
                    <p>Hospital-specific features will be implemented here.</p>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Catch all route */}
            <Route
              path="*"
              element={
                <div className="min-h-screen flex items-center justify-center">
                  <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Page Not Found
                    </h2>
                    <p className="text-gray-600 mb-4">
                      The page you're looking for doesn't exist.
                    </p>
                    <a
                      href="/dashboard"
                      className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                    >
                      Go to Dashboard
                    </a>
                  </div>
                </div>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
