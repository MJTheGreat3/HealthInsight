import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { RealtimeProvider } from "./contexts/RealtimeContext";
import LoginForm from "./components/auth/LoginForm";
import RegisterForm from "./components/auth/RegisterForm";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import Dashboard from "./components/Dashboard";
import UploadPage from "./components/UploadPage";
import ResultsPage from "./components/ResultsPage";
import ReportHistory from "./components/ReportHistory";
import ProfilePage from "./components/ProfilePage";
import ChatPage from "./components/ChatPage";
import ChatButton from "./components/ChatButton";
import NotificationSystem from "./components/NotificationSystem";
import ErrorBoundary from "./components/ErrorBoundary";
import "./App.css";

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <RealtimeProvider>
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
                  path="/patient/chat"
                  element={
                    <ProtectedRoute requiredUserType="patient">
                      <ChatPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/patient/*"
                  element={
                    <ProtectedRoute requiredUserType="patient">
                      <div className="p-8 text-center">
                        <h2 className="text-2xl font-bold">Patient Area</h2>
                        <p>
                          Patient-specific features will be implemented here.
                        </p>
                      </div>
                    </ProtectedRoute>
                  }
                />

                {/* Hospital-only routes */}
                <Route
                  path="/hospital"
                  element={
                    <ProtectedRoute requiredUserType="institution">
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/hospital/patient/:patientId"
                  element={
                    <ProtectedRoute requiredUserType="institution">
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/hospital/patient/:patientId/reports"
                  element={
                    <ProtectedRoute requiredUserType="institution">
                      <div className="p-8 text-center">
                        <h2 className="text-2xl font-bold">Patient Reports</h2>
                        <p>Patient report history will be implemented here.</p>
                      </div>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/hospital/patient/:patientId/profile"
                  element={
                    <ProtectedRoute requiredUserType="institution">
                      <div className="p-8 text-center">
                        <h2 className="text-2xl font-bold">Patient Profile</h2>
                        <p>Patient profile details will be implemented here.</p>
                      </div>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/hospital/*"
                  element={
                    <ProtectedRoute requiredUserType="institution">
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />

                {/* Default redirect */}
                <Route
                  path="/"
                  element={<Navigate to="/dashboard" replace />}
                />

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

              {/* Global Chat Button - Available on all protected routes */}
              <ChatButton />

              {/* Global Notification System */}
              <NotificationSystem />
            </div>
          </Router>
        </RealtimeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
