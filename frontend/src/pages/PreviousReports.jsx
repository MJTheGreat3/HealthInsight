import React, { useState, useEffect } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import { useAuth } from "../auth/useAuth"
import { useParams, useLocation, useNavigate } from "react-router-dom"
import ReportTile from '../components/ReportTile'
import { Edit2, FileText, Calendar, ChevronRight, Search, Filter, Clock, ArrowUpRight } from 'lucide-react'

export default function PreviousReports({ readOnly, hospitalView, patientUid: propPatientUid }) {
    const { user, loading: authLoading } = useAuth()
    const { uid: urlPatientUid } = useParams()
    const location = useLocation()
    const navigate = useNavigate()

    const isHospitalView = hospitalView || location.pathname.startsWith("/hospital/patient")
    const readOnlyMode = readOnly || location.state?.readOnly === true

    const [reports, setReports] = useState([])
    const [filteredReports, setFilteredReports] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")
    const [favoriteMarkers, setFavoriteMarkers] = useState([])
    const [openReport, setOpenReport] = useState(null)
    const [searchTerm, setSearchTerm] = useState("")

    // Determine which patient UID to use
    const targetUid = isHospitalView ? (propPatientUid || urlPatientUid) : user?.uid

    useEffect(() => {
        // Wait for auth to load and targetUid to be available
        if (authLoading || !targetUid || (!user && !isHospitalView)) return

        const fetchData = async () => {
            // Fetch favorite markers
            if (user) {
                try {
                    const token = await user.getIdToken()

                    // If hospital view, get favorites from patient profile
                    const favUrl = isHospitalView
                        ? `/api/hospital/patient/${targetUid}`
                        : `/api/user/me`

                    const favoritesRes = await fetch(favUrl, {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    })

                    if (favoritesRes.ok) {
                        const favoritesData = await favoritesRes.json()
                        setFavoriteMarkers(favoritesData.Favorites || favoritesData.favorites || [])
                    }
                } catch (err) {
                    console.error("Failed to fetch favorite markers:", err)
                }
            }

            // Then fetch reports
            await fetchReports()
        }

        const fetchReports = async () => {
            try {
                if (!user) {
                    throw new Error("User not authenticated")
                }
                const token = await user.getIdToken()

                // Fetch top 10 latest LLM reports list
                const listResponse = await fetch(`/api/LLMReportsPatientList/${targetUid}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (!listResponse.ok) {
                    throw new Error("Failed to fetch reports list")
                }

                const reportsList = await listResponse.json()

                // Fetch full details for each LLM report
                const reportsWithDetails = await Promise.all(
                    reportsList.map(async (reportItem) => {
                        const reportId = reportItem._id.$oid || reportItem._id

                        try {
                            const detailResponse = await fetch(`/api/LLMReport/${reportId}`, {
                                headers: {
                                    Authorization: `Bearer ${token}`,
                                },
                            })

                            if (detailResponse.ok) {
                                const fullReport = await detailResponse.json()

                                // Extract biomarkers from input field (matches MetricData schema)
                                const inputData = fullReport.input || {}
                                const biomarkers = Object.entries(inputData).map(([key, test]) => ({
                                    name: test.name || key,
                                    value: test.value || '',
                                    unit: test.unit || '',
                                    range: test.range || '',
                                    remark: test.remark || '',
                                    verdict: test.verdict || ''
                                }))

                                // Parse date from time field (ISO string format)
                                const reportTime = fullReport.time || reportItem.time
                                const reportDate = reportTime
                                    ? new Date(reportTime).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                                    : 'Unknown date'
                                const rawDate = reportTime ? new Date(reportTime) : new Date(0)

                                return {
                                    _id: reportId,
                                    Report_id: fullReport.report_id,
                                    patient_id: fullReport.patient_id,
                                    llm_report_id: reportId,
                                    date: reportDate,
                                    rawDate: rawDate,
                                    Processed_at: reportTime,
                                    analysis: fullReport.output,
                                    Attributes: inputData,
                                    biomarkers: biomarkers
                                }
                            }
                        } catch (err) {
                            console.error("Failed to fetch LLM report details:", reportId, err)
                        }

                        // Return partial data if full fetch fails
                        const reportTime = reportItem.time
                        return {
                            _id: reportId,
                            Report_id: reportItem.report_id,
                            llm_report_id: reportId,
                            date: reportTime
                                ? new Date(reportTime).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                                : 'Unknown date',
                            rawDate: reportTime ? new Date(reportTime) : new Date(0),
                            Processed_at: reportTime,
                            analysis: null,
                            Attributes: {},
                            biomarkers: []
                        }
                    })
                )

                // Sort by date (newest first)
                reportsWithDetails.sort((a, b) => b.rawDate - a.rawDate)

                setReports(reportsWithDetails)
                setFilteredReports(reportsWithDetails)

            } catch (err) {
                console.error("Failed to fetch reports:", err)
                setError(err.message || "Failed to load reports")
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [user, targetUid, isHospitalView])

    useEffect(() => {
        if (searchTerm.trim() === "") {
            setFilteredReports(reports)
        } else {
            const lowerTerm = searchTerm.toLowerCase()
            const filtered = reports.filter(r =>
                r.date.toLowerCase().includes(lowerTerm) ||
                (r.analysis?.interpretation && r.analysis.interpretation.toLowerCase().includes(lowerTerm))
            )
            setFilteredReports(filtered)
        }
    }, [searchTerm, reports])

    async function addMarkerToFavorites(markerName) {
        if (isHospitalView) return // Don't allow in hospital view

        try {
            const token = await user.getIdToken()

            console.log("Adding marker to favorites from reports:", markerName)

            const res = await fetch(`/api/user/favorites`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ marker: markerName }),
            })

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                throw new Error(errorData.detail || `Failed to add favorite marker (${res.status})`)
            }

            const data = await res.json()
            setFavoriteMarkers(data.favorites || [])
            alert(`${markerName} added to favorites!`)
        } catch (err) {
            console.error("Failed to add favorite marker:", err)
            alert(`Failed to add marker to favorites: ${err.message}`)
        }
    }

    if (loading) {
        return (
            <div style={{ maxWidth: 1000, margin: '0 auto' }}>
                <div className="card" style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                    Loading reports history...
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div style={{ maxWidth: 1000, margin: '0 auto' }}>
                <div className="card" style={{ padding: 40, textAlign: 'center', color: '#ef4444' }}>
                    <div style={{ marginBottom: 12, fontWeight: 600 }}>Error loading reports</div>
                    {error}
                </div>
            </div>
        )
    }

    return (
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
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
                <div style={{ position: 'relative', zIndex: 1 }}>
                    <h1 style={{ margin: '0 0 8px 0', fontSize: '2rem', fontWeight: 700 }}>
                        Medical Reports History
                    </h1>
                    <p style={{ margin: 0, opacity: 0.9, fontSize: '1.1rem', maxWidth: '600px' }}>
                        Access and analyze your past medical records. Track your health journey over time with detailed AI insights.
                    </p>
                </div>

                {/* Decorative circles */}
                <div style={{ position: 'absolute', top: -40, right: -40, width: 240, height: 240, borderRadius: '50%', background: 'rgba(255,255,255,0.1)' }} />
                <div style={{ position: 'absolute', bottom: -20, left: 100, width: 120, height: 120, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
            </div>

            {/* Search and Filter Bar */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
                <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                    <input
                        type="text"
                        placeholder="Search reports by date or content..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '12px 12px 12px 44px',
                            borderRadius: 12,
                            border: '1px solid #e2e8f0',
                            fontSize: 15,
                            outline: 'none',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                        }}
                    />
                </div>
                <button style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '0 20px',
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: 12,
                    color: '#475569',
                    fontWeight: 500,
                    cursor: 'pointer'
                }}>
                    <Filter size={18} /> Filter
                </button>
            </div>

            {/* Reports List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {filteredReports.length === 0 ? (
                    <div className="card" style={{ padding: 60, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                        <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <FileText size={32} color="#94a3b8" />
                        </div>
                        <div>
                            <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>No reports found</h3>
                            <p className="small-muted" style={{ margin: 0 }}>
                                {searchTerm ? "Try adjusting your search terms." : "Upload your first medical report to get started."}
                            </p>
                        </div>
                        {!searchTerm && !isHospitalView && (
                            <button
                                onClick={() => navigate('/upload')}
                                className="btn-primary"
                                style={{ marginTop: 8 }}
                            >
                                Upload Report
                            </button>
                        )}
                    </div>
                ) : (
                    filteredReports.map(r => (
                        <div key={r._id} className="card" style={{ padding: 0, overflow: 'hidden', border: '1px solid #e2e8f0', transition: 'transform 0.2s, box-shadow 0.2s' }}>
                            <div style={{ padding: 20, borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{ width: 40, height: 40, borderRadius: 10, background: 'white', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0d9488' }}>
                                        <Calendar size={20} />
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0, fontSize: 16, color: '#0f172a' }}>{r.date}</h3>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#64748b', marginTop: 2 }}>
                                            <Clock size={12} /> Processed on {new Date(r.Processed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setOpenReport(r)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 6,
                                        padding: '8px 16px',
                                        background: 'white',
                                        border: '1px solid #cbd5e1',
                                        borderRadius: 8,
                                        color: '#334155',
                                        fontWeight: 500,
                                        cursor: 'pointer',
                                        fontSize: 14
                                    }}
                                >
                                    View Details <ArrowUpRight size={16} />
                                </button>
                            </div>

                            <div style={{ padding: 20 }}>
                                {r.analysis ? (
                                    <AnalysisCard
                                        analysis={r.analysis}
                                        compact
                                        favoriteMarkers={favoriteMarkers}
                                        onAddFavorite={addMarkerToFavorites}
                                    />
                                ) : (
                                    <div style={{ padding: 20, textAlign: 'center', color: '#64748b', background: '#f8fafc', borderRadius: 8, border: '1px dashed #cbd5e1' }}>
                                        No AI analysis available for this report.
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {openReport && (
                <ReportTile
                    report={openReport}
                    user={user}
                    onClose={() => setOpenReport(null)}
                    favoriteMarkers={favoriteMarkers}
                    setFavoriteMarkers={setFavoriteMarkers}
                />
            )}
        </div>
    )
}
