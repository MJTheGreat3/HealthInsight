import React, { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/useAuth"
import AnalysisCard from "../components/AnalysisCard"
import { API_URLS } from "../utils/api"

export default function HospitalPatient() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  const [patientData, setPatientData] = useState(null)
  const [patientReports, setPatientReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!user || !id) return

    const fetchPatientData = async () => {
      try {
        const token = await user.getIdToken()

        // First, get all approved patients to find the one with matching UID
        const patientsRes = await fetch(API_URLS.HOSPITAL_PATIENTS, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!patientsRes.ok) {
          throw new Error("Failed to fetch patients")
        }

        const patients = await patientsRes.json()
        const patient = patients.find(p => p.uid === id)

        if (!patient) {
          throw new Error("Patient not found or access not approved")
        }

        setPatientData(patient)

        // Fetch patient's reports
        const reportsRes = await fetch(`http://127.0.0.1:8000/api/reports/patient/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (reportsRes.ok) {
          const reportsData = await reportsRes.json()
          
          // Fetch LLM analyses for each report
          const reportsWithAnalysis = await Promise.all(
            reportsData.reports.map(async (report) => {
              let analysis = null
              
              if (report.llm_report_id) {
                try {
                  const analysisRes = await fetch(`http://127.0.0.1:8000/api/LLMReport/${report.llm_report_id}`, {
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                  })
                  
                  if (analysisRes.ok) {
                    const analysisData = await analysisRes.json()
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
          
          setPatientReports(reportsWithAnalysis)
        }

      } catch (err) {
        console.error("Failed to fetch patient data:", err)
        setError(err.message || "Failed to load patient data")
      } finally {
        setLoading(false)
      }
    }

    fetchPatientData()
  }, [user, id])

  if (loading) {
    return (
      <div>
        <h2>Patient Details</h2>
        <div className="card">Loading patient data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h2>Patient Details</h2>
        <div className="card">
          <div className="error-box">{error}</div>
          <button 
            className="btn-secondary" 
            style={{ marginTop: 12 }}
            onClick={() => navigate("/hospital")}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2>Patient Details</h2>
          <p className="small-muted">Patient ID: {id}</p>
        </div>
        <button 
          className="btn-secondary"
          onClick={() => navigate("/hospital")}
        >
          ← Back to Dashboard
        </button>
      </div>

      {/* Patient Information */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3>Patient Information</h3>
        <div className="form-grid">
          <div>
            <label>Name</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.name || "Not provided"}
            </div>
          </div>
          <div>
            <label>Email</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.email || "Not provided"}
            </div>
          </div>
          <div>
            <label>Age</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.BioData?.age || "Not provided"}
            </div>
          </div>
          <div>
            <label>Gender</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.BioData?.gender || "Not provided"}
            </div>
          </div>
          <div>
            <label>Blood Group</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.BioData?.blood_group || "Not provided"}
            </div>
          </div>
          <div>
            <label>Allergies</label>
            <div style={{ padding: "8px 12px", backgroundColor: "#f9fafb", borderRadius: "4px" }}>
              {patientData?.BioData?.allergies || "None specified"}
            </div>
          </div>
        </div>
      </div>

      {/* Patient Reports */}
      <div className="card">
        <h3>Medical Reports ({patientReports.length})</h3>
        {patientReports.length === 0 ? (
          <p className="small-muted">No reports available for this patient</p>
        ) : (
          <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
            {patientReports.map((report) => (
              <div key={report._id} className="card" style={{ backgroundColor: "#f9fafb" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div>
                    <strong>Report Date: {report.date}</strong>
                    <div className="small-muted">Report ID: {report.Report_id}</div>
                    <div className="small-muted">Tests: {Object.keys(report.Attributes || {}).length}</div>
                  </div>
                </div>
                
                {report.analysis && <AnalysisCard analysis={report.analysis} compact />}
                
                {!report.analysis && (
                  <div className="small-muted" style={{ marginTop: 8 }}>
                    No analysis available for this report
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
