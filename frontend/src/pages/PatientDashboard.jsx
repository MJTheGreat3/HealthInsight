import React from "react"
import { useParams } from "react-router-dom"
import { useAuth } from "../auth/useAuth"
import { useEffect, useState } from "react"
import Dashboard from "./Dashboard"

export default function HospitalPatientDashboard() {
  const { uid } = useParams()
  const { user } = useAuth()
  const [patient, setPatient] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !uid) return

    const fetchPatient = async () => {
      try {
        const token = await user.getIdToken()

        const res = await fetch(
          `/api/hospital/patient/${uid}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!res.ok) throw new Error("Failed to load patient")

        const data = await res.json()
        setPatient(data)
      } catch (err) {
        console.error("Failed to load patient:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchPatient()
  }, [user, uid])

  if (loading) return <div className="card">Loading patient...</div>
  if (!patient) return <div className="card">Patient not found</div>

  return ( <Dashboard readOnly={true} hospitalView={true} patientUid={uid} />
  )
}
