import React, { useEffect, useState } from 'react'
import './reportTile.css'
import AnalysisCard from './AnalysisCard'
import EditReportTable from './EditReportTable'
import { X, Plus, Star, Trash2, FileText, Activity } from 'lucide-react'

export default function ReportTile({ report, user, onClose, favoriteMarkers, setFavoriteMarkers }) {
    const [biomarkers, setBiomarkers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")
    const [newMarkerName, setNewMarkerName] = useState("")
    const [saving, setSaving] = useState(false)
    const [editMode, setEditMode] = useState(false)

    useEffect(() => {
        if (!report) return

        // If biomarkers are already provided from LLM report input, use them directly
        if (report.biomarkers && report.biomarkers.length > 0) {
            setBiomarkers(report.biomarkers)
            setConcernOptions(report.analysis?.concern_options || [])
            setLoading(false)
            return
        }

        // Fall back to API fetch if Report_id exists and no biomarkers provided
        if (report.Report_id) {
            fetchBiomarkers()
        } else {
            setLoading(false)
        }
    }, [report])

    async function fetchBiomarkers() {
        setLoading(true)
        setError("")
        try {
            const token = user && user.getIdToken ? await user.getIdToken() : null
            const res = await fetch(`/api/reports/${report.Report_id}`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {}
            })

            if (!res.ok) throw new Error('Failed to load report')
            const reportData = await res.json()

            // Convert attributes object to array (same logic as ReportVisualization + EditReportTable)
            const attributes = reportData.Attributes || {}
            const biomarkersArray = Object.entries(attributes).map(([key, attr]) => ({
                key,
                name: attr.name || key,
                value: attr.value || '',
                range: attr.range || '',
                unit: attr.unit || '',
                remark: attr.remark || ''
            }))

            setBiomarkers(biomarkersArray)
        } catch (err) {
            console.error(err)
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    // Convert biomarkers array back to attributes object for EditReportTable
    const getAttributesObject = () => {
        if (!biomarkers) return {}

        const attributes = {}
        biomarkers.forEach(biomarker => {
            if (biomarker.key) {
                attributes[biomarker.key] = {
                    name: biomarker.name,
                    value: biomarker.value,
                    range: biomarker.range,
                    unit: biomarker.unit,
                    remark: biomarker.remark
                }
            }
        })
        return attributes
    }

    // Handle attribute updates from EditReportTable
    const handleAttributeUpdate = async (testName, updates) => {
        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report.Report_id}/attribute-by-name`, {
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

            // Refresh biomarkers after update
            await fetchBiomarkers()
            return { success: true }

        } catch (err) {
            console.error("Failed to update attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    // Handle attribute additions from EditReportTable
    const handleAttributeAdd = async (newAttribute) => {
        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report.Report_id}/attribute`, {
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

            // Refresh biomarkers after addition
            await fetchBiomarkers()
            return { success: true }

        } catch (err) {
            console.error("Failed to add attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    // Handle attribute deletions from EditReportTable
    const handleAttributeDelete = async (testName) => {
        if (!confirm(`Are you sure you want to delete "${testName}"?`)) {
            return { success: false, error: "User cancelled" }
        }

        setSaving(true)
        try {
            const token = await user.getIdToken()

            const response = await fetch(`/api/reports/${report.Report_id}/attribute-by-name`, {
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

            // Refresh biomarkers after deletion
            await fetchBiomarkers()
            return { success: true }

        } catch (err) {
            console.error("Failed to delete attribute:", err)
            return { success: false, error: err.message }
        } finally {
            setSaving(false)
        }
    }

    async function addFavorite(markerName) {
        try {
            const token = user && user.getIdToken ? await user.getIdToken() : null
            const res = await fetch(`/api/user/favorites`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ marker: markerName })
            })
            if (!res.ok) throw new Error('Failed to add favorite')
            const data = await res.json()
            setFavoriteMarkers(data.favorites || [])
        } catch (err) {
            console.error(err)
            alert('Failed to add favorite: ' + err.message)
        }
    }

    async function removeFavorite(markerName) {
        try {
            const token = user && user.getIdToken ? await user.getIdToken() : null
            const res = await fetch(`/api/user/favorites`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ marker: markerName })
            })
            if (!res.ok) throw new Error('Failed to remove favorite')
            const data = await res.json()
            setFavoriteMarkers(data.favorites || [])
        } catch (err) {
            console.error(err)
            alert('Failed to remove favorite: ' + err.message)
        }
    }

    // Keep the simple add function for left panel quick add
    async function addAttributeToReport() {
        const name = newMarkerName.trim()
        if (!name) return alert('Enter marker name')

        try {
            const token = user && user.getIdToken ? await user.getIdToken() : null
            const res = await fetch(`/api/reports/${report.Report_id}/attribute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ name, value: '', remark: '', range: '', unit: '' })
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || 'Failed to add attribute')
            }

            setNewMarkerName('')
            fetchBiomarkers()
            alert(`${name} added to report`)
        } catch (err) {
            console.error(err)
            alert('Failed to add attribute: ' + err.message)
        }
    }

    return (
        <div className="report-tile-overlay" onClick={onClose}>
            <div className="report-tile" onClick={e => e.stopPropagation()}>
                <div className="report-tile-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 40,
                            height: 40,
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
                        <div>
                            <h2 style={{ margin: 0, fontSize: 18, color: '#0f172a' }}>Report Details</h2>
                            <div style={{ fontSize: 13, color: '#64748b' }}>
                                {report.date ? report.date : 'Unknown Date'}
                            </div>
                        </div>
                    </div>
                    <button className="close-btn" onClick={onClose}>
                        <X size={18} />
                    </button>
                </div>

                <div className="report-tile-body">
                    <div className="left-panel">
                        <div style={{ padding: '16px 16px 8px', fontSize: 12, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            Biomarkers Found
                        </div>

                        <div className="biomarker-list">
                            {loading ? (
                                <div style={{ padding: 20, textAlign: 'center', color: '#64748b' }}>Loading biomarkers...</div>
                            ) : biomarkers.length === 0 ? (
                                <div style={{ padding: 20, textAlign: 'center', color: '#64748b' }}>No biomarkers found</div>
                            ) : (
                                biomarkers.map((b, i) => {
                                    const isFav = favoriteMarkers.some(f => f.toLowerCase() === b.name.toLowerCase())
                                    return (
                                        <div key={i} className="fav-row">
                                            <div>
                                                <div className="fav-name">{b.name}</div>
                                                <div className="fav-value">{b.value} {b.unit}</div>
                                            </div>
                                            <button
                                                className="btn-link"
                                                onClick={() => isFav ? removeFavorite(b.name) : addFavorite(b.name)}
                                                title={isFav ? "Remove from favorites" : "Add to favorites"}
                                            >
                                                {isFav ? <Star size={18} fill="#eab308" color="#eab308" /> : <Star size={18} color="#94a3b8" />}
                                            </button>
                                        </div>
                                    )
                                })
                            )}
                        </div>

                        <div className="add-marker">
                            <div style={{ fontSize: 13, fontWeight: 500, color: '#334155' }}>Add Missing Biomarker</div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <input
                                    value={newMarkerName}
                                    onChange={e => setNewMarkerName(e.target.value)}
                                    placeholder="e.g. Vitamin D"
                                    style={{ flex: 1 }}
                                />
                                <button className="btn-primary" onClick={addAttributeToReport}>
                                    <Plus size={18} />
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="right-panel">
                        {report.analysis ? (
                            <div style={{ marginBottom: 32 }}>
                                <AnalysisCard
                                    analysis={report.analysis}
                                    favoriteMarkers={favoriteMarkers}
                                    onAddFavorite={addFavorite}
                                />
                            </div>
                        ) : (
                            <div style={{ padding: 40, textAlign: 'center', color: '#64748b', background: '#f8fafc', borderRadius: 12, border: '1px dashed #cbd5e1', marginBottom: 32 }}>
                                <Activity size={32} color="#94a3b8" style={{ marginBottom: 12 }} />
                                <p>No AI analysis available for this report.</p>
                            </div>
                        )}

                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <h3 style={{ fontSize: 18, margin: 0, color: '#0f172a' }}>Extracted Data</h3>
                                <button
                                    className="button"
                                    onClick={() => setEditMode(!editMode)}
                                    style={{ fontSize: '14px', padding: '8px 16px' }}
                                >
                                    {editMode ? 'View Mode' : 'Edit Mode'}
                                </button>
                            </div>

                            {editMode ? (
                                <div>
                                    {saving && (
                                        <div style={{ backgroundColor: '#fef3c7', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px', fontSize: '14px' }}>
                                            <span>⏳ Saving changes...</span>
                                        </div>
                                    )}
                                    <EditReportTable
                                        attributes={getAttributesObject()}
                                        onUpdate={handleAttributeUpdate}
                                        onAdd={handleAttributeAdd}
                                        onDelete={handleAttributeDelete}
                                        saving={saving}
                                    />
                                </div>
                            ) : (
                                <div style={{ border: '1px solid #e2e8f0', borderRadius: 12, overflow: 'hidden' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                                        <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                                            <tr>
                                                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569', fontWeight: 600 }}>Biomarker</th>
                                                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569', fontWeight: 600 }}>Value</th>
                                                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569', fontWeight: 600 }}>Unit</th>
                                                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569', fontWeight: 600 }}>Reference Range</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {biomarkers.map((b, i) => (
                                                <tr key={i} style={{ borderBottom: i !== biomarkers.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                                                    <td style={{ padding: '12px 16px', color: '#0f172a', fontWeight: 500 }}>{b.name}</td>
                                                    <td style={{ padding: '12px 16px', color: '#334155' }}>{b.value}</td>
                                                    <td style={{ padding: '12px 16px', color: '#64748b' }}>{b.unit}</td>
                                                    <td style={{ padding: '12px 16px', color: '#64748b' }}>{b.range}</td>
                                                </tr>
                                            ))}
                                            {biomarkers.length === 0 && (
                                                <tr>
                                                    <td colSpan={4} style={{ padding: 24, textAlign: 'center', color: '#94a3b8' }}>No data extracted</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
