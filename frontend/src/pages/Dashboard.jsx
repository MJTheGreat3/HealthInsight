import React, { useEffect, useState } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import ChartWidget from '../components/ChartWidget'
import { useAuth } from "../auth/useAuth"
import { useParams, useLocation, useNavigate } from "react-router-dom"
import { auth } from '../firebase/firebase'
import { Activity, TrendingUp, AlertCircle, CheckCircle2, ArrowRight, Plus, Sparkles, HeartPulse, FileText } from 'lucide-react'

export default function Dashboard({ readOnly: propReadOnly, hospitalView: propHospitalView, patientUid: propPatientUid }) {
    const { uid: urlPatientUid } = useParams()
    const location = useLocation()
    const navigate = useNavigate()
    const isHospitalView = propHospitalView || location.pathname.startsWith("/hospital/patient")
    const readOnly = propReadOnly || location.state?.readOnly === true
    const { user, loading: authLoading } = useAuth()
    const [userData, setUserData] = useState(null)
    const [actionableSuggestions, setActionableSuggestions] = useState([])
    const [loadingSuggestions, setLoadingSuggestions] = useState(true)
    const [concernedBiomarkers, setConcernedBiomarkers] = useState([])
    const [favoriteMarkers, setFavoriteMarkers] = useState([])
    const [latestAnalysis, setLatestAnalysis] = useState(null)
    const [loadingAnalysis, setLoadingAnalysis] = useState(true)
    const [loadingFavorites, setLoadingFavorites] = useState(true)

    // Determine which patient UID to use
    const targetUid = isHospitalView ? (propPatientUid || urlPatientUid) : user?.uid

    useEffect(() => {
        // Debug environment variable
        console.log('Backend URL:', import.meta.env.VITE_BACKEND_URL);
        
        // Wait for auth to load and targetUid to be available
        if (authLoading || !targetUid || (!user && !isHospitalView)) return

        const fetchDashboardData = async () => {
            try {
                const token = await user.getIdToken()

                // Fetch user data (different endpoints for hospital vs patient view)
                const url = isHospitalView
                    ? `${import.meta.env.VITE_BACKEND_URL}/api/hospital/patient/${targetUid}`
                    : `${import.meta.env.VITE_BACKEND_URL}/api/user/me`

                const userRes = await fetch(url, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (!userRes.ok) throw new Error("Failed to fetch user data")
                const userData = await userRes.json()
                setUserData(userData)

                // Set favorite markers from user data
                setFavoriteMarkers(userData.Favorites || [])
                setLoadingFavorites(false)

                // Fetch actionable suggestions (only for patient view)
                if (!isHospitalView) {
                    const suggestionsRes = await fetch(
                        `${import.meta.env.VITE_BACKEND_URL}/api/dashboard/actionable-suggestions`,
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                            },
                        }
                    )

                    if (suggestionsRes.ok) {
                        const suggestionsData = await suggestionsRes.json()
                        setActionableSuggestions(suggestionsData.actionable_suggestions || [])
                    } else {
                        console.error("Failed to fetch actionable suggestions")
                    }
                }

                // Fetch latest report and analysis
                const reportsRes = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/reports/patient/${targetUid}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (reportsRes.ok) {
                    const reportsData = await reportsRes.json()
                    const reports = reportsData.reports || []

                    if (reports.length > 0) {
                        // Get the most recent report
                        const latestReport = reports.sort((a, b) =>
                            new Date(b.Processed_at || 0) - new Date(a.Processed_at || 0)
                        )[0]

                        // Extract concerned biomarkers from the latest report
                        const attributes = latestReport.Attributes || {}
                        const concerned = []

                        for (const [key, test] of Object.entries(attributes)) {
                            if (test.name && test.value && test.remark && test.remark.toLowerCase().includes('abnormal')) {
                                concerned.push({
                                    name: test.name,
                                    value: test.value,
                                    unit: test.unit || ''
                                })
                            }
                        }

                        // If no abnormal markers, take first few tests
                        if (concerned.length === 0 && Object.keys(attributes).length > 0) {
                            const testEntries = Object.values(attributes).slice(0, 3)
                            testEntries.forEach(test => {
                                if (test.name && test.value) {
                                    concerned.push({
                                        name: test.name,
                                        value: test.value,
                                        unit: test.unit || ''
                                    })
                                }
                            })
                        }

                        setConcernedBiomarkers(concerned)

                        // Fetch LLM analysis for the latest report
                        if (latestReport.llm_report_id) {
                            try {
                                const analysisRes = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/LLMReport/${latestReport.llm_report_id}`, {
                                    headers: {
                                        Authorization: `Bearer ${token}`,
                                    },
                                })

                                if (analysisRes.ok) {
                                    const analysisData = await analysisRes.json()
                                    setLatestAnalysis(analysisData.output)
                                }
                            } catch (err) {
                                console.error("Failed to fetch analysis:", err)
                            }
                        }
                    }
                }

            } catch (err) {
                console.error("Dashboard data fetch failed:", err)
            } finally {
                setLoadingSuggestions(false)
                setLoadingAnalysis(false)
            }
        }

        fetchDashboardData()
    }, [user, targetUid, isHospitalView])

    async function addMarkerToFavorites(markerName) {
        try {
            const token = await user.getIdToken()

            console.log("Adding marker to favorites from dashboard:", markerName)

            const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/user/favorites`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ marker: markerName }),
            })

            console.log("Dashboard add response status:", res.status)

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                console.error("Error response:", errorData)
                throw new Error(errorData.detail || `Failed to add favorite marker (${res.status})`)
            }

            const data = await res.json()
            console.log("Dashboard add success:", data)
            setFavoriteMarkers(data.favorites || [])
            alert(`${markerName} added to favorites!`)
        } catch (err) {
            console.error("Failed to add favorite marker:", err)
            alert(`Failed to add marker to favorites: ${err.message}`)
        }
    }

    if (authLoading) {
        return <div className="card">Loading dashboard...</div>
    }

    return (
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            {/* Hero Section */}
            <div style={{ 
                background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)', 
                borderRadius: 16, 
                padding: '32px 40px', 
                color: 'white',
                marginBottom: 32,
                boxShadow: '0 10px 25px -5px rgba(13, 148, 136, 0.3)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ maxWidth: '65%' }}>
                        <h1 style={{ margin: '0 0 12px 0', fontSize: '2rem', fontWeight: 700 }}>
                            {isHospitalView
                                ? `Patient Dashboard${userData?.name ? ` — ${userData.name}` : ""}`
                                : `Welcome back${userData?.name ? `, ${userData.name}` : ""}!`}
                        </h1>
                        
                        <div style={{ 
                            background: 'rgba(255, 255, 255, 0.15)', 
                            backdropFilter: 'blur(8px)', 
                            padding: '16px 20px', 
                            borderRadius: 12,
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            marginTop: 16
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, opacity: 0.9, fontSize: 13, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                <Sparkles size={14} /> Latest Insight
                            </div>
                            <p style={{ margin: 0, lineHeight: 1.6, fontSize: '1.05rem', opacity: 0.95 }}>
                                {latestAnalysis?.interpretation
                                    ? latestAnalysis.interpretation.slice(0, 160) + (latestAnalysis.interpretation.length > 160 ? "..." : "")
                                    : "Upload your first medical report to see personalized insights and recommendations."
                                }
                            </p>
                        </div>
                    </div>

                    {!isHospitalView && (
                        <button 
                            onClick={() => navigate('/upload')}
                            style={{ 
                                background: 'white', 
                                color: '#0f766e', 
                                border: 'none', 
                                padding: '12px 24px', 
                                borderRadius: 50, 
                                fontSize: 15, 
                                fontWeight: 600, 
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                transition: 'transform 0.2s'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                        >
                            <Plus size={18} strokeWidth={2.5} />
                            Upload New Report
                        </button>
                    )}
                </div>
                
                {/* Decorative circles */}
                <div style={{ position: 'absolute', top: -20, right: -20, width: 200, height: 200, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
                <div style={{ position: 'absolute', bottom: -40, left: -40, width: 300, height: 300, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
            </div>

            {/* Main Grid Layout */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
                
                {/* Left Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                    
                    {/* Favorite Markers Section */}
                    <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8, fontSize: '1.25rem' }}>
                                <Activity size={20} color="#0d9488" />
                                Tracked Biomarkers
                            </h3>
                            {!isHospitalView && (
                                <button 
                                    onClick={() => navigate('/profile')}
                                    style={{ background: 'none', border: 'none', color: '#0d9488', fontSize: 14, cursor: 'pointer', fontWeight: 500 }}
                                >
                                    Manage Favorites →
                                </button>
                            )}
                        </div>

                        <div className="concern-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
                            {loadingFavorites ? (
                                <div className="card" style={{ gridColumn: '1/-1', padding: 32, textAlign: 'center', color: '#6b7280' }}>Loading favorite markers...</div>
                            ) : favoriteMarkers.length === 0 ? (
                                <div className="card" style={{ gridColumn: '1/-1', padding: 40, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                                    <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#f0fdfa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <HeartPulse size={24} color="#0d9488" />
                                    </div>
                                    <h4 style={{ margin: 0 }}>No markers tracked yet</h4>
                                    <p className="small-muted" style={{ margin: 0, maxWidth: 300 }}>Add biomarkers from your profile or reports to track their trends over time.</p>
                                    {!isHospitalView && (
                                        <button 
                                            onClick={() => navigate('/profile')}
                                            className="btn-secondary"
                                            style={{ marginTop: 8 }}
                                        >
                                            Add Markers
                                        </button>
                                    )}
                                </div>
                            ) : (
                                favoriteMarkers.map((marker) => (
                                    <div key={marker} className="card" style={{ padding: 20, border: '1px solid #f1f5f9', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                            <div>
                                                <strong style={{ fontSize: 16, color: '#1e293b' }}>{marker}</strong>
                                                <div className="small-muted">Historical Trend</div>
                                            </div>
                                            <div style={{ width: 32, height: 32, borderRadius: 8, background: '#f0fdfa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                <TrendingUp size={16} color="#0d9488" />
                                            </div>
                                        </div>
                                        <div style={{ marginTop: 8 }}>
                                            <ChartWidget biomarker={marker} patientUid={targetUid} />
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Detailed Analysis Section */}
                    <div>
                        <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, fontSize: '1.25rem' }}>
                            <FileText size={20} color="#0d9488" />
                            Latest Report Analysis
                        </h3>
                        
                        {loadingAnalysis ? (
                            <div className="card" style={{ padding: 32, textAlign: 'center', color: '#6b7280' }}>Loading latest analysis...</div>
                        ) : latestAnalysis ? (
                            <AnalysisCard analysis={latestAnalysis} />
                        ) : (
                            <div className="card" style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                                No analysis available. Upload a report to get started.
                            </div>
                        )}
                    </div>

                </div>

                {/* Right Column - Suggestions & Quick Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                    
                    {/* Actionable Suggestions */}
                    {!isHospitalView && (
                        <div>
                            <h3 style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, fontSize: '1.25rem' }}>
                                <Sparkles size={20} color="#0d9488" />
                                Recommended Actions
                            </h3>
                            <div className="card" style={{ padding: 0, overflow: 'hidden', border: '1px solid #f1f5f9' }}>
                                {loadingSuggestions ? (
                                    <div style={{ padding: 24, textAlign: 'center', color: '#6b7280' }}>Generating suggestions...</div>
                                ) : actionableSuggestions.length === 0 ? (
                                    <div style={{ padding: 24, textAlign: 'center', color: '#6b7280' }}>No suggestions available yet.</div>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        {actionableSuggestions.map((s, idx) => (
                                            <div key={idx} style={{ 
                                                padding: '16px 20px', 
                                                borderBottom: idx !== actionableSuggestions.length - 1 ? '1px solid #f1f5f9' : 'none',
                                                display: 'flex',
                                                gap: 12,
                                                alignItems: 'flex-start'
                                            }}>
                                                <div style={{ 
                                                    minWidth: 24, 
                                                    height: 24, 
                                                    borderRadius: '50%', 
                                                    background: '#f0fdfa', 
                                                    display: 'flex', 
                                                    alignItems: 'center', 
                                                    justifyContent: 'center',
                                                    marginTop: 2
                                                }}>
                                                    <CheckCircle2 size={14} color="#0d9488" />
                                                </div>
                                                <span style={{ fontSize: 14, lineHeight: 1.5, color: '#334155' }}>{s}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Quick Links / Info */}
                    <div className="card" style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                        <h4 style={{ margin: '0 0 12px 0', color: '#475569' }}>Health Summary</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                                <span style={{ color: '#64748b' }}>Profile Completion</span>
                                <span style={{ fontWeight: 600, color: '#0f172a' }}>
                                    {userData?.BioData ? '88%' : '20%'}
                                </span>
                            </div>
                            <div style={{ width: '100%', height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                                <div style={{ width: userData?.BioData ? '88%' : '20%', height: '100%', background: '#0d9488', borderRadius: 3 }}></div>
                            </div>
                            <div style={{ marginTop: 8 }}>
                                <button 
                                    onClick={() => navigate('/profile')}
                                    style={{ width: '100%', padding: '8px', background: 'white', border: '1px solid #cbd5e1', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 500, color: '#334155' }}
                                >
                                    Update Profile
                                </button>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    )
}
