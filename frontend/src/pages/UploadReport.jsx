import React, { useState, useRef } from 'react'
import AnalysisCard from '../components/AnalysisCard'
import UploadSplashScreen from '../components/UploadSplashScreen'
import { UploadCloud } from 'lucide-react'
import { useAuth } from "../auth/useAuth"
import { useNavigate } from 'react-router-dom'

export default function UploadReport() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [file, setFile] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState("")
    const inputRef = useRef()

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

            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/reports/upload-and-analyze`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.text()
                throw new Error(errorData || "Upload failed")
            }

            const data = await response.json()

            // Auto-redirect to report visualization on successful upload
            if (data.report_id) {
                console.log("Upload successful, redirecting to report visualization...")
                navigate(`/report/${data.report_id}`, {
                    state: {
                        reportData: data,
                        isNewUpload: true
                    }
                })
            } else {
                // Fallback to old behavior if no report_id
                if (data.llm_analysis_complete && data.llm_analysis) {
                    setAnalysis(data.llm_analysis)
                } else if (data.llm_error) {
                    setError(`Upload successful but analysis failed: ${data.llm_error}`)
                } else {
                    setError("Upload successful but analysis is not available")
                }
            }

        } catch (err) {
            console.error("Upload error:", err)
            setError(err.message || "Failed to upload file")
        } finally {
            setUploading(false)
        }
    }

    return (
        <div>
            <h2>Upload Report</h2>

            <div className="card">
                <div
                    className={`upload-drop ${dragOver ? 'dragover' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={onDrop}
                >
                    {/* Icon from lucide-react */}
                    <UploadCloud size={84} color="#60a5fa" style={{ marginBottom: 12 }} />
                    <div style={{ fontSize: 18, fontWeight: 600 }}>Drop a file or click to browse</div>
                    <div className="small-muted">Supported: PDF, PNG, JPG</div>

                    {error && (
                        <div className="error-box" style={{ marginBottom: 12 }}>
                            {error}
                        </div>
                    )}

                    <div className="upload-actions">
                        <input ref={inputRef} className="file-input" id="report-file" type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={onFile} />
                        <button className="upload-btn" onClick={() => inputRef.current && inputRef.current.click()}>Choose file</button>
                        <button className="upload-btn primary" onClick={onUpload} disabled={!file || uploading}>
                            {uploading ? 'Uploading...' : (file ? 'Upload & Get Analysis' : 'Upload')}
                        </button>
                    </div>

                    {file && (
                        <div className="file-info">
                            <div className="file-name">{file.name}</div>
                            <button className="remove-file" onClick={() => { setFile(null); setError(""); setAnalysis(null) }}>Remove</button>
                        </div>
                    )}
                </div>
            </div>

            {/* Show animated splash screen during upload */}
            {uploading && <UploadSplashScreen />}

            {analysis && (
                <div style={{ marginTop: 16 }}>
                    <AnalysisCard analysis={analysis} />
                </div>
            )}
        </div>
    )
}
