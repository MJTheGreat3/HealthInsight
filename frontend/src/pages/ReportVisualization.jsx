import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from "../auth/useAuth"
import EditReportTable from '../components/EditReportTable'
import AnalysisCard from '../components/AnalysisCard'
import { Edit2 } from 'lucide-react'

export default function ReportVisualization() {
    const { report_id } = useParams()
    const navigate = useNavigate()
    const { user } = useAuth()

    const [report, setReport] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")
    const [saving, setSaving] = useState(false)
    const [editingDate, setEditingDate] = useState(false)
    const [tempDate, setTempDate] = useState('')

    useEffect(() => {
        if (!user || !report_id) return

        fetchReportData()
    }, [user, report_id])

    const fetchReportData = async () => {
        try {
            const token = await user.getIdToken()

            // Fetch report details
            const reportResponse = await fetch(`/api/reports/${report_id}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })

            if (!reportResponse.ok) {
                throw new Error("Report not found")
            }

            const reportData = await reportResponse.json()
            setReport(reportData)

            // Fetch analysis if available
            if (reportData.llm_report_id) {
                try {
                    const analysisResponse = await fetch(`/api/LLMReport/${reportData.llm_report_id}`, {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    })

                    if (analysisResponse.ok) {
                        const analysisData = await analysisResponse.json()
                        setAnalysis(analysisData.output)
                    }
                } catch (err) {
                    console.error("Failed to fetch analysis:", err)
                }
            }

        } catch (err) {
            console.error("Failed to fetch report:", err)
            setError(err.message || "Failed to load report")
        } finally {
            setLoading(false)
        }
    }

    const handleAttributeUpdate = async (testName, updates) => {
        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report_id}/attribute-by-name`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    name: testName,
                    ...updates
                }),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Failed to update attribute")
            }

            // Refresh report data after update
            await fetchReportData()
            return { success: true }

        } catch (err) {
            console.error("Failed to update attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    const handleAttributeAdd = async (newAttribute) => {
        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report_id}/attribute`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(newAttribute),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Failed to add attribute")
            }

            // Refresh report data after addition
            await fetchReportData()
            return { success: true }

        } catch (err) {
            console.error("Failed to add attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    const handleAttributeDelete = async (testName) => {
        if (!confirm(`Are you sure you want to delete "${testName}"?`)) {
            return { success: false, error: "User cancelled" }
        }

        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report_id}/attribute-by-name`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    name: testName
                }),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Failed to delete attribute")
            }

            // Refresh report data after deletion
            await fetchReportData()
            return { success: true }

        } catch (err) {
            console.error("Failed to delete attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    const handleDateUpdate = async (newDate) => {
        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report_id}/processed-at`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    processed_at: new Date(newDate).toISOString()
                }),
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || "Failed to update date")
            }

            // Refresh report data after update
            await fetchReportData()
            setEditingDate(false)
            return { success: true }

        } catch (err) {
            console.error("Failed to update date:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    const startDateEdit = () => {
        setTempDate(report.Processed_at ? new Date(report.Processed_at).toISOString().split('T')[0] : '')
        setEditingDate(true)
    }

    const saveDateEdit = () => {
        if (tempDate) {
            handleDateUpdate(tempDate)
        } else {
            setEditingDate(false)
        }
    }

    const cancelDateEdit = () => {
        setEditingDate(false)
        setTempDate('')
    }

    if (loading) {
        return (
            <div>
                <h2>Report Visualization</h2>
                <div className="card">Loading report...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div>
                <h2>Report Visualization</h2>
                <div className="card">
                    <div className="error-box">{error}</div>
                </div>
            </div>
        )
    }

    if (!report) {
        return (
            <div>
                <h2>Report Visualization</h2>
                <div className="card">Report not found</div>
            </div>
        )
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2>Report Visualization</h2>
                <button
                    className="button"
                    onClick={() => navigate(-1)}
                    style={{ fontSize: '14px' }}
                >
                    ← Back to Reports
                </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
                <div className="card">
                    <h3 style={{ marginTop: 0 }}>Report Information</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '10px' }}>
                        <strong>Report ID:</strong> {report.Report_id}<br />
                        <strong>Patient ID:</strong> {report.Patient_id}<br />
                        <strong>Reported Date:</strong>
                        {editingDate ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <input
                                    type="date"
                                    value={tempDate}
                                    onChange={(e) => setTempDate(e.target.value)}
                                    style={{ padding: '4px 8px', border: '1px solid #3b82f6', borderRadius: '4px' }}
                                    autoFocus
                                />
                                <button
                                    onClick={saveDateEdit}
                                    disabled={saving}
                                    style={{
                                        backgroundColor: '#dcfce7',
                                        color: '#16a34a',
                                        border: 'none',
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '12px'
                                    }}
                                    title="Save date"
                                >
                                    ✓
                                </button>
                                <button
                                    onClick={cancelDateEdit}
                                    style={{
                                        backgroundColor: '#fee2e2',
                                        color: '#dc2626',
                                        border: 'none',
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '12px'
                                    }}
                                    title="Cancel"
                                >
                                    ✕
                                </button>
                            </div>
                        ) : (
                            <div
                                onClick={startDateEdit}
                                style={{ cursor: 'pointer', padding: '4px', borderRadius: '4px', display: 'inline-block' }}
                                title="Click to edit date"
                            >
                                {report.Processed_at ? new Date(report.Processed_at).toLocaleDateString() : 'Unknown'}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {report.Attributes && Object.keys(report.Attributes).length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <EditReportTable
                        attributes={report.Attributes}
                        onUpdate={handleAttributeUpdate}
                        onAdd={handleAttributeAdd}
                        onDelete={handleAttributeDelete}
                        saving={saving}
                    />
                </div>
            )}

            {analysis && (
                <div>
                    <AnalysisCard analysis={analysis} />
                </div>
            )}

            {(!report.Attributes || Object.keys(report.Attributes).length === 0) && (
                <div className="card">
                    <p>No test data available for this report.</p>
                </div>
            )}
        </div>
    )
}
