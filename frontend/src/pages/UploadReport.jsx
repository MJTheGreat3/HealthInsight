import React, { useState, useRef } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import ReportTile from '../components/ReportTile'
import { UploadCloud, FileText, X, Sparkles, Loader2, ArrowRight } from 'lucide-react'
import { useAuth } from "../auth/useAuth"
import { useNavigate } from 'react-router-dom'

export default function UploadReport() {
    const { user } = useAuth()
    const [file, setFile] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState("")
    const inputRef = useRef()
    const [openReport, setOpenReport] = useState(null)
    const [favoriteMarkers, setFavoriteMarkers] = useState([])
    const navigate = useNavigate()

    function onFile(e) {
        const f = e.target.files && e.target.files[0]
        if (f) setFile(f)
        setError("")
    }

    function onDrop(e) {
        e.preventDefault()
        setDragOver(false)
        const f = e.dataTransfer.files && e.dataTransfer.files[0]
        if (f) setFile(f)
        setError("")
    }

    async function onUpload() {
        if (!file) {
            setError("Please select a file first")
            return
        }

        setUploading(true)
        setError("")

        try {
            const token = await user.getIdToken()

            const formData = new FormData()
            formData.append('file', file)
            formData.append('auto_analyze', 'true')

            const response = await fetch(`/api/reports/upload-and-analyze`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => null)
                const errorMessage = errorData?.detail || errorData?.message || "Upload failed"
                throw new Error(errorMessage)
            }

            const data = await response.json()

            // Open the report tile modal so user can review biomarkers and add favorites
            setOpenReport({ Report_id: data.report_id, ...data })
            if (data.llm_analysis_complete && data.llm_analysis) {
                setAnalysis(data.llm_analysis)
            }

        } catch (err) {
            console.error("Upload error:", err)
            setError(err.message || "Failed to upload file")
        } finally {
            setUploading(false)
        }
    }

    return (
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <h2 style={{ marginBottom: 24 }}>Upload Report</h2>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div
                    className={`upload-drop ${dragOver ? 'dragover' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={onDrop}
                    onClick={() => !file && inputRef.current && inputRef.current.click()}
                    style={{
                        cursor: file ? 'default' : 'pointer',
                        minHeight: 320,
                        background: dragOver ? '#f0f9ff' : '#ffffff',
                        transition: 'all 0.2s ease',
                        position: 'relative'
                    }}
                >
                    <input
                        ref={inputRef}
                        className="file-input"
                        id="report-file"
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={onFile}
                        style={{ display: 'none' }}
                    />

                    {!file ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 40 }}>
                            <div style={{
                                width: 80,
                                height: 80,
                                borderRadius: '50%',
                                background: '#eff6ff',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: 24
                            }}>
                                <UploadCloud size={40} color="#3b82f6" strokeWidth={1.5} />
                            </div>
                            <h3 style={{ margin: '0 0 8px 0', fontSize: 20, color: '#1e293b' }}>Upload Medical Report</h3>
                            <p className="small-muted" style={{ marginBottom: 32, fontSize: 15 }}>
                                Drag & drop your file here or click to browse
                                <br />
                                <span style={{ fontSize: 13, opacity: 0.7 }}>Supports PDF, PNG, JPG</span>
                            </p>

                            <button
                                type="button"
                                className="btn-primary"
                                onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
                                style={{
                                    padding: '12px 32px',
                                    fontSize: '15px',
                                    borderRadius: '50px',
                                    boxShadow: '0 4px 12px rgba(14, 165, 164, 0.2)'
                                }}
                            >
                                Select File
                            </button>
                        </div>
                    ) : (
                        <div style={{ width: '100%', maxWidth: 420, padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div style={{
                                width: '100%',
                                background: '#f8fafc',
                                padding: 16,
                                borderRadius: 16,
                                border: '1px solid #e2e8f0',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 16,
                                marginBottom: 32,
                                boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                            }}>
                                <div style={{
                                    width: 48,
                                    height: 48,
                                    borderRadius: 12,
                                    background: '#fff',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    border: '1px solid #f1f5f9'
                                }}>
                                    <FileText size={24} color="#0ea5a4" />
                                </div>
                                <div style={{ flex: 1, overflow: 'hidden' }}>
                                    <div style={{ fontWeight: 600, color: '#334155', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {file.name}
                                    </div>
                                    <div style={{ fontSize: 13, color: '#94a3b8' }}>
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); setFile(null); setError(""); }}
                                    style={{
                                        background: 'white',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '50%',
                                        width: 32,
                                        height: 32,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: 'pointer',
                                        color: '#64748b',
                                        transition: 'all 0.2s'
                                    }}
                                    title="Remove file"
                                >
                                    <X size={16} />
                                </button>
                            </div>

                            {error && (
                                <div className="error-box" style={{ width: '100%', marginBottom: 24, padding: '12px 16px', borderRadius: 12, background: '#fef2f2', border: '1px solid #fee2e2', color: '#ef4444', fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#ef4444' }}></div>
                                    {error}
                                </div>
                            )}

                            <button
                                type="button"
                                className="btn-primary"
                                onClick={(e) => { e.stopPropagation(); onUpload(); }}
                                disabled={uploading}
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    fontSize: '16px',
                                    borderRadius: '14px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: 10,
                                    background: uploading ? '#94a3b8' : 'linear-gradient(135deg, #0ea5a4 0%, #0d9488 100%)',
                                    boxShadow: uploading ? 'none' : '0 4px 12px rgba(13, 148, 136, 0.3)',
                                    transform: uploading ? 'none' : 'translateY(0)',
                                    transition: 'all 0.2s'
                                }}
                            >
                                {uploading ? (
                                    <>
                                        <Loader2 className="spin" size={20} />
                                        Analyzing Report...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles size={20} />
                                        Analyze Report
                                    </>
                                )}
                            </button>

                            <div style={{ marginTop: 16 }}>
                                <button
                                    onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
                                    style={{ background: 'none', border: 'none', color: '#64748b', fontSize: 14, cursor: 'pointer', textDecoration: 'underline' }}
                                >
                                    Choose a different file
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {analysis && (
                <div style={{ marginTop: 16 }}>
                    <AnalysisCard analysis={analysis} />
                </div>
            )}

            {openReport && (
                <ReportTile
                    report={openReport}
                    user={user}
                    onClose={() => {
                        // Close modal and navigate to the reports section
                        setOpenReport(null)
                        navigate('/previous')
                    }}
                    favoriteMarkers={favoriteMarkers}
                    setFavoriteMarkers={setFavoriteMarkers}
                />
            )}
        </div>
    )
}
