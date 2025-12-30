import React from 'react'
import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { Home, FilePlus, Archive, User, LogOut, Users, FileText } from 'lucide-react'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import UploadReport from './pages/UploadReport'
import PreviousReports from './pages/PreviousReports'
import ChatButton from './components/ChatButton'
import HospitalDashboard from "./pages/HospitalDashboard"
import HospitalPatientDashboard from './pages/PatientDashboard'
import HospitalPatientProfile from './pages/PatientProfile'
import HospitalPatientReports from './pages/PatientReports'
import HospitalPatientLayout from "./pages/HospitalPatientLayout"
import AccessRequests from "./pages/AccessRequests"
import { signOut } from "firebase/auth"
import { auth } from "./firebase/firebase"
import { useNavigate } from "react-router-dom"


//Patient Pages
function PatientLayout() {
    return (
        <div className="app-shell">
            <aside className="app-sidebar" style={{ 
                background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
                borderRight: '1px solid #e2e8f0'
            }}>
                <div className="logo" style={{ paddingBottom: 24, borderBottom: '1px solid #f1f5f9', marginBottom: 24 }}>
                    <div style={{ 
                        width: 36, 
                        height: 36, 
                        borderRadius: 10, 
                        background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        boxShadow: '0 4px 12px rgba(13, 148, 136, 0.2)'
                    }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                        </svg>
                    </div>
                    <span style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', letterSpacing: '-0.5px' }}>HealthInsight</span>
                </div>

                <nav style={{ gap: 10 }}>
                    <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <Home size={18} /> Dashboard
                    </NavLink>

                    <NavLink to="/upload" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <FilePlus size={18} /> Upload Report
                    </NavLink>

                    <NavLink to="/previous" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <Archive size={18} /> Reports History
                    </NavLink>

                    <NavLink to="/profile" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <User size={18} /> My Profile
                    </NavLink>

                    <NavLink to="/access-requests" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
                        <Users size={18} /> Access Requests
                    </NavLink>
                </nav>

                <div className="logout" style={{ marginTop: 'auto', paddingTop: 24, borderTop: '1px solid #f1f5f9' }}>
                    <button
                        className="logout-btn"
                        style={{ 
                            width: '100%', 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 10, 
                            padding: '12px 16px', 
                            borderRadius: 12, 
                            border: '1px solid #e2e8f0', 
                            background: 'white', 
                            color: '#64748b', 
                            cursor: 'pointer', 
                            fontWeight: 500,
                            transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.borderColor = '#cbd5e1'
                            e.currentTarget.style.color = '#0f172a'
                            e.currentTarget.style.background = '#f8fafc'
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.borderColor = '#e2e8f0'
                            e.currentTarget.style.color = '#64748b'
                            e.currentTarget.style.background = 'white'
                        }}
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
                        <LogOut size={16} /> Sign Out
                    </button>
                </div>
            </aside>

            <main className="app-main" style={{ background: '#f8fafc' }}>
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
                <Route path="/access-requests" element={<AccessRequests />} />
            </Route>

            <Route element={<HospitalLayout />}>
                <Route path="/hospital" element={<HospitalDashboard />} />

                <Route path="/hospital/patient/:uid" element={<HospitalPatientLayout />}>
                    <Route path="dashboard" element={<HospitalPatientDashboard />} />
                    <Route path="profile" element={<HospitalPatientProfile />} />
                    <Route path="reports" element={<HospitalPatientReports />} />
                </Route>
            </Route>


        </Routes>
    )
}