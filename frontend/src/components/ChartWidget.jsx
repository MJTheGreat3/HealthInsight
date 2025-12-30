import React, { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend } from 'chart.js'
import { useAuth } from "../auth/useAuth"

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

                const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/draw_graph/${uid}/${encodeURIComponent(biomarker)}`, {
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
        <div style={{ height: '200px', width: '100%' }}>
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
