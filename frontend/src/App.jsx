import React, { useEffect } from 'react'
import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { Home, FilePlus, Archive, User, LogOut, Users, FileText, MessageCircle } from 'lucide-react'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import UploadReport from './pages/UploadReport'
import PreviousReports from './pages/PreviousReports'
import ReportVisualization from './pages/ReportVisualization'
import AIChatbot from './pages/AIChatbot'
import ChatButton from './components/ChatButton'
import HospitalDashboard from "./pages/HospitalDashboard"
import HospitalPatientDashboard from './pages/PatientDashboard'
import HospitalPatientProfile from './pages/PatientProfile'
import HospitalPatientReports from './pages/PatientReports'
import HospitalPatientLayout from "./pages/HospitalPatientLayout"
import { } from "module";
import AccessRequests from "./pages/AccessRequests"
import ProtectedRoute from "./auth/ProtectedRoute"
import { useAuthRedirect } from "./hooks/useAuthRedirect"
import { signOut } from "firebase/auth"
import { auth } from "./firebase/firebase"
import { useNavigate } from "react-router-dom"


//Patient Pages
function PatientLayout() {
    return (
        <div className="app-shell">
            <aside className="app-sidebar">
                <div className="logo">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" fill="#0ea5a4" />
                        <path d="M8 12h8" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                    <span>HealthInsight</span>
                </div>

                <nav>
                    <NavLink to="/dashboard" className={({ isActive }) => isActive ? "active" : ""}>
                        <Home size={16} style={{ marginRight: 8 }} /> Dashboard
                    </NavLink>

                    <NavLink to="/upload">
                        <FilePlus size={16} style={{ marginRight: 8 }} /> Upload Report
                    </NavLink>

                    <NavLink to="/previous">
                        <Archive size={16} style={{ marginRight: 8 }} /> Reports
                    </NavLink>

                    <NavLink to="/ai-chat">
                        <MessageCircle size={16} style={{ marginRight: 8 }} /> AI Assistant
                    </NavLink>

                    <NavLink to="/profile">
                        <User size={16} style={{ marginRight: 8 }} /> Profile
                    </NavLink>

                    <NavLink to="/access-requests">
                        <FileText size={16} style={{ marginRight: 8 }} /> Manage Access
                    </NavLink>
                </nav>

                <div className="logout">
                    <button
                        className="logout-btn"
                        onClick={async () => {
                            try {
                                await signOut(auth)
                                localStorage.clear()
                                window.location.href = "/login"
                            } catch {
                                alert("Logout failed")
                            }
                        }}
                    >
                        <LogOut size={14} /> Logout
                    </button>
                </div>
            </aside>

            <main className="app-main">
                <Outlet />
            </main>

            <ChatButton />
        </div>
    )
}

// Hospital Layouts
function HospitalLayout() {
    return (
        <div style={{ padding: 28 }}>
            <Outlet />
        </div>
    )
}

//Routes
export default function App() {
    // Global 401 redirect handling
    useAuthRedirect()

    // Set favicon dynamically to match app logo
    useEffect(() => {
        // Create SVG favicon matching the app logo
        const svgFavicon = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                <rect width="32" height="32" rx="6" fill="none"/>
                <circle cx="16" cy="16" r="15" fill="#0ea5a4"/>
                <path d="M10 16h12" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
            </svg>
        `;

        // Convert SVG to data URL
        const svgBlob = new Blob([svgFavicon], { type: 'image/svg+xml' });
        const svgUrl = URL.createObjectURL(svgBlob);

        // Update favicon
        let link = document.querySelector("link[rel*='icon']") || document.createElement('link');
        link.type = 'image/svg+xml';
        link.rel = 'shortcut icon';
        link.href = svgUrl;

        if (!document.querySelector("link[rel*='icon']")) {
            document.head.appendChild(link);
        }

        // Cleanup function
        return () => {
            URL.revokeObjectURL(svgUrl);
        };
    }, []);
    return (
        <Routes>
            <Route path="/" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<PatientLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/upload" element={<UploadReport />} />
                <Route path="/previous" element={<PreviousReports />} />
                <Route path="/report/:report_id" element={<ReportVisualization />} />
                <Route path="/ai-chat" element={<AIChatbot />} />
                <Route path="/access-requests" element={<AccessRequests />} />
            </Route >

            <Route element={<HospitalLayout />}>
                <Route path="/hospital" element={<HospitalDashboard />} />

                <Route path="/hospital/patient/:uid" element={<HospitalPatientLayout />}>
                    <Route path="dashboard" element={<HospitalPatientDashboard />} />
                    <Route path="profile" element={<HospitalPatientProfile />} />
                    <Route path="reports" element={<HospitalPatientReports />} />
                </Route>
            </Route>


        </Routes >
    )
}
