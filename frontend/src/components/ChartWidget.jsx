import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend } from 'chart.js'
import { useAuth } from "../auth/useAuth"

// Normalize biomarker name for better matching - less aggressive to preserve matching potential
const normalizeBiomarkerName = (name) => {
    return name.toLowerCase()
        .replace(/\s+/g, ' ')           // normalize spaces
        .replace(/\s*\(.*?\)\s*/g, '')  // remove content in parentheses but keep surrounding context
        .replace(/\/[a-z]*[a-z]$/gi, '')  // remove units only at end like /dL, /uL
        .replace(/mg\/dl|mmol\/l|mm\/hg|%$/gi, '')  // remove other units only at end
        .trim();
};

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend)

export default function ChartWidget({ biomarker, patientUid }) {
    const { user } = useAuth()
    const [chartData, setChartData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")

    useEffect(() => {
        if (!user || !biomarker) return

        const fetchChartData = async () => {
            try {
                const token = await user.getIdToken()

                // Use patientUid if provided (hospital view), otherwise use current user's uid
                const uid = patientUid || user.uid

                // Use normalized biomarker name for better matching
                const normalizedBiomarker = normalizeBiomarkerName(biomarker);
                const response = await fetch(`http://127.0.0.1:8000/api/draw_graph/${uid}/${encodeURIComponent(normalizedBiomarker)}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (!response.ok) {
                    throw new Error("Failed to fetch chart data")
                }

                const data = await response.json()

                if (data.data_points === 0) {
                    setError("No data available for this biomarker")
                    return
                }

                // Process chart data
                const sortedValues = data.values.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

                const labels = sortedValues.map(v => {
                    const date = new Date(v.timestamp)
                    return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
                })

                const chartValues = sortedValues.map(v => {
                    // Use numeric value if available, otherwise 0 for chart
                    return typeof v.value === 'number' ? v.value : 0
                })

                setChartData({
                    labels,
                    datasets: [
                        {
                            label: biomarker,
                            data: chartValues,
                            borderColor: 'rgba(14,165,164,0.9)',
                            backgroundColor: 'rgba(14,165,164,0.2)',
                            tension: 0.3,
                            fill: true
                        }
                    ]
                })

            } catch (err) {
                console.error("Failed to fetch chart data:", err)
                setError("Failed to load chart data")
            } finally {
                setLoading(false)
            }
        }

        fetchChartData()
    }, [user, biomarker, patientUid])

    if (loading) {
        return (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="small-muted">Loading chart...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="small-muted" style={{ textAlign: 'center' }}>{error}</div>
            </div>
        )
    }

    if (!chartData) {
        return (
            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="small-muted">No chart data available</div>
            </div>
        )
    }

    return (
        <div>
            <Line data={chartData} options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }} />
        </div>
    )
}
