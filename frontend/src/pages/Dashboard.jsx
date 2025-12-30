import React, { useEffect, useState } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import ChartWidget from '../components/ChartWidget'
import { useAuth } from "../auth/useAuth"
import { useParams, useLocation } from "react-router-dom"
import { auth } from '../firebase/firebase'

export default function Dashboard({ readOnly: propReadOnly, hospitalView: propHospitalView, patientUid: propPatientUid }) {
    const { uid: urlPatientUid } = useParams()
    const location = useLocation()
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
    const [refreshKey, setRefreshKey] = useState(0)

    // Determine which patient UID to use
    const targetUid = isHospitalView ? (propPatientUid || urlPatientUid) : user?.uid

    useEffect(() => {
        // Wait for auth to load and targetUid to be available
        if (authLoading || !targetUid || (!user && !isHospitalView)) return

        const fetchDashboardData = async () => {
            try {
                const token = await user.getIdToken()

                // Fetch user data (different endpoints for hospital vs patient view)
                const url = isHospitalView
                    ? `http://localhost:8000/hospital/patient/${targetUid}`
                    : "http://localhost:8000/user/me"

                const userRes = await fetch(url, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (!userRes.ok) throw new Error("Failed to fetch user data")
                const userData = await userRes.json()
                setUserData(userData)

                // Set favorite markers from user data (only for patient view)
                if (!isHospitalView) {
                    setFavoriteMarkers(userData.Favorites || [])
                    setLoadingFavorites(false)
                }

                // Fetch latest report and analysis
                const reportsRes = await fetch(`http://127.0.0.1:8000/api/reports/patient/${targetUid}`, {
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
                                const analysisRes = await fetch(`http://127.0.0.1:8000/api/LLMReport/${latestReport.llm_report_id}`, {
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

                // Fetch actionable suggestions (only for patient view)
                if (!isHospitalView) {
                    const suggestionsRes = await fetch(
                        "http://localhost:8000/dashboard/actionable-suggestions",
                        {
                            headers: {
                                Authorization: `Bearer ${token}`,
                            },
                        }
                    )

                    if (suggestionsRes.ok) {
                        const suggestionsData = await suggestionsRes.json()
                        const suggestions = suggestionsData.actionable_suggestions || []
                        setActionableSuggestions(suggestionsData.actionable_suggestions || [])

                        if (suggestions.length === 0) {
                            setTimeout(() => {setRefreshKey(k => k + 1)}, 4000)
                        }
                    } else {
                        console.error("Failed to fetch actionable suggestions")
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
    }, [user, targetUid, isHospitalView, refreshKey])

    async function addMarkerToFavorites(markerName) {
        try {
            const token = await user.getIdToken()

            console.log("Adding marker to favorites from dashboard:", markerName)

            const res = await fetch("http://localhost:8000/user/favorites", {
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
        <div>
            <div className="hero">
                <div className="hero-left" style={{ flex: 1 }}>
                    <h2>
                        {isHospitalView
                            ? `Patient Dashboard${userData?.name ? ` — ${userData.name}` : ""}`
                            : `Welcome back${userData?.name ? `, ${userData.name}` : ""}!`}
                    </h2>

                    <p className="small-muted">
                        {latestAnalysis?.interpretation
                            ? latestAnalysis.interpretation.slice(0, 120) + "..."
                            : "Upload your first medical report to see personalized insights and recommendations."
                        }
                    </p>
                </div>
            </div>

            <h3>Favorite Concern Markers</h3>
            <div className="concern-row">
                {loadingFavorites ? (
                    <div className="card">Loading favorite markers...</div>
                ) : favoriteMarkers.length === 0 ? (
                    <div className="card">No favorite markers yet. Add markers in your profile or click on concerned biomarkers below to add them to favorites.</div>
                ) : (
                    favoriteMarkers.map((marker) => (
                        <div key={marker} className="card concern-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <strong>{marker}</strong>
                                    <div className="small-muted">Favorite marker</div>
                                </div>
                            </div>
                            <div style={{ marginTop: 8 }}>
                                <ChartWidget biomarker={marker} patientUid={urlPatientUid} />
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* {!isHospitalView && ( */}
            {/*     <> */}
            {/*         <h3>Current Concern Biomarkers</h3> */}
            {/*         <div className="concern-row"> */}
            {/*             {loadingAnalysis ? ( */}
            {/*                 <div className="card">Loading biomarkers...</div> */}
            {/*             ) : concernedBiomarkers.length === 0 ? ( */}
            {/*                 <div className="card">No biomarkers to display. Upload a report to see your health metrics.</div> */}
            {/*             ) : ( */}
            {/*                 concernedBiomarkers.map((c) => ( */}
            {/*                     <div */}
            {/*                         key={c.name} */}
            {/*                         className="card concern-card" */}
            {/*                         style={{ cursor: 'pointer', position: 'relative' }} */}
            {/*                         onClick={() => { */}
            {/*                             if (!favoriteMarkers.some(fav => fav.toLowerCase() === c.name.toLowerCase())) { */}
            {/*                                 if (confirm(`Add ${c.name} to your favorite markers?`)) { */}
            {/*                                     addMarkerToFavorites(c.name) */}
            {/*                                 } */}
            {/*                             } */}
            {/*                         }} */}
            {/*                         title={favoriteMarkers.some(fav => fav.toLowerCase() === c.name.toLowerCase()) ? "Already in favorites" : "Click to add to favorites"} */}
            {/*                     > */}
            {/*                         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}> */}
            {/*                             <div> */}
            {/*                                 <strong>{c.name}</strong> */}
            {/*                                 <div className="small-muted">{c.value} {c.unit}</div> */}
            {/*                                 {favoriteMarkers.some(fav => fav.toLowerCase() === c.name.toLowerCase()) && ( */}
            {/*                                     <div style={{ fontSize: '11px', color: '#16a34a', marginTop: 2 }}> */}
            {/*                                         ✓ In favorites */}
            {/*                                     </div> */}
            {/*                                 )} */}
            {/*                             </div> */}
            {/*                             {!favoriteMarkers.some(fav => fav.toLowerCase() === c.name.toLowerCase()) && ( */}
            {/*                                 <div style={{ fontSize: '12px', color: '#6b7280' }}> */}
            {/*                                     Click to add */}
            {/*                                 </div> */}
            {/*                             )} */}
            {/*                         </div> */}
            {/*                         <div style={{ marginTop: 8 }}> */}
            {/*                             <ChartWidget biomarker={c.name} patientUid={urlPatientUid} /> */}
            {/*                         </div> */}
            {/*                     </div> */}
            {/*                 )) */}
            {/*             )} */}
            {/*         </div> */}
            {/*     </> */}
            {/* )} */}

            <div className="grid">
                {/* Only show actionable suggestions for patient view */}
                {!isHospitalView && (
                    <div className="card">
                        <h3>Actionable Suggestions</h3>
                        {loadingSuggestions ? (
                            <p className="small-muted">Generating personalized suggestions...</p>
                        ) : actionableSuggestions.length === 0 ? (
                            <p className="small-muted">No suggestions available yet.</p>
                        ) : (
                            <ul style={{ marginTop: 12 }}>
                                {actionableSuggestions.map((s, idx) => (
                                    <li key={idx}>{s}</li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                <div className="card">
                    <h3>Detailed Analysis</h3>
                    {loadingAnalysis ? (
                        <p className="small-muted">Loading latest analysis...</p>
                    ) : latestAnalysis ? (
                        <AnalysisCard analysis={latestAnalysis} />
                    ) : (
                        <p className="small-muted">No analysis available. Upload and analyze a report to see detailed insights.</p>
                    )}
                </div>
            </div>
        </div>
    )
}
