import React, { useState, useEffect } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import { useAuth } from "../auth/useAuth"
import { useParams, useLocation, useNavigate } from "react-router-dom"
import { Edit2 } from 'lucide-react'

export default function PreviousReports({ readOnly, hospitalView, patientUid: propPatientUid }) {
  const { user, loading: authLoading } = useAuth()
  const { uid: urlPatientUid } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  
  const isHospitalView = hospitalView || location.pathname.startsWith("/hospital/patient")
  const readOnlyMode = readOnly || location.state?.readOnly === true
  
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [favoriteMarkers, setFavoriteMarkers] = useState([])

  // Determine which patient UID to use
  const targetUid = isHospitalView ? (propPatientUid || urlPatientUid) : user?.uid

  useEffect(() => {
    // Wait for auth to load and targetUid to be available
    if (authLoading || !targetUid || (!user && !isHospitalView)) return

    const fetchData = async () => {
      // Fetch favorite markers first (only for patient view)
      if (!isHospitalView && user) {
        try {
          const token = await user.getIdToken()
          const favoritesRes = await fetch("http://localhost:8000/user/favorites", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          })

          if (favoritesRes.ok) {
            const favoritesData = await favoritesRes.json()
            setFavoriteMarkers(favoritesData.favorites || [])
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
        
        const response = await fetch(`http://127.0.0.1:8000/api/reports/patient/${targetUid}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error("Failed to fetch reports")
        }

        const data = await response.json()
        
        // Fetch LLM analyses for each report
        const reportsWithAnalysis = await Promise.all(
          data.reports.map(async (report) => {
            let analysis = null
            
            if (report.llm_report_id) {
              try {
                const analysisResponse = await fetch(`http://127.0.0.1:8000/api/LLMReport/${report.llm_report_id}`, {
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                })
                
                if (analysisResponse.ok) {
                  const analysisData = await analysisResponse.json()
                  analysis = analysisData.output
                }
              } catch (err) {
                console.error("Failed to fetch analysis for report:", report._id, err)
              }
            }
            
            return {
              ...report,
              analysis,
              date: report.Processed_at ? new Date(report.Processed_at).toISOString().split('T')[0] : 'Unknown date'
            }
          })
        )
        
        // Sort by date (newest first)
        reportsWithAnalysis.sort((a, b) => new Date(b.date) - new Date(a.date))
        
        setReports(reportsWithAnalysis)

      } catch (err) {
        console.error("Failed to fetch reports:", err)
        setError(err.message || "Failed to load reports")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [user, targetUid, isHospitalView])

  async function addMarkerToFavorites(markerName) {
    if (isHospitalView) return // Don't allow in hospital view
    
    try {
      const token = await user.getIdToken()
      
      console.log("Adding marker to favorites from reports:", markerName)
      
      const res = await fetch("http://localhost:8000/user/favorites", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ marker: markerName }),
      })

      console.log("Reports add response status:", res.status)

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        console.error("Error response:", errorData)
        throw new Error(errorData.detail || `Failed to add favorite marker (${res.status})`)
      }
      
      const data = await res.json()
      console.log("Reports add success:", data)
      setFavoriteMarkers(data.favorites || [])
      alert(`${markerName} added to favorites!`)
    } catch (err) {
      console.error("Failed to add favorite marker:", err)
      alert(`Failed to add marker to favorites: ${err.message}`)
    }
  }

  if (loading) {
    return (
      <div>
        <h2>Previous Reports</h2>
        <div className="card">Loading reports...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h2>Previous Reports</h2>
        <div className="card">
          <div className="error-box">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h2>Previous Reports</h2>
      <p className="small-muted">
        {reports.length === 0 ? "No reports uploaded yet" : `Showing ${reports.length} report${reports.length === 1 ? '' : 's'}`}
      </p>
      <div style={{display:'grid', gap:12}}>
        {reports.map(r => (
          <div key={r._id} className="card">
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom: '12px'}}>
              <div>
                <strong>{r.date}</strong>
                <div className="small-muted" style={{marginTop: '4px'}}>
                  {r.analysis?.interpretation ? r.analysis.interpretation.slice(0, 60) + "..." : "No analysis available"}
                </div>
              </div>
              <button
                onClick={() => navigate(`/report/${r.Report_id}`)}
                className="button"
                style={{ fontSize: '12px', padding: '6px 12px' }}
                title="View and edit full report"
              >
                <Edit2 size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                View & Edit
              </button>
            </div>
            {r.analysis && (
              <AnalysisCard 
                analysis={r.analysis} 
                compact 
                favoriteMarkers={favoriteMarkers}
                onAddFavorite={addMarkerToFavorites}
              />
            )}
            {!r.analysis && (
              <div className="small-muted" style={{marginTop: 12}}>
                No analysis available for this report
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
