import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../auth/useAuth"
import { logout } from "../auth/logout"
import { API_URLS } from "../utils/api"

export default function HospitalDashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const [search, setSearch] = useState("")
  const [showModal, setShowModal] = useState(false)
  const [patientEmail, setPatientEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [patients, setPatients] = useState([])
  const [hospitalName, setHospitalName] = useState("")

  //LOAD HOSPITAL DATA + PATIENTS 
  useEffect(() => {
    if (!user) return

    async function loadHospitalData() {
      try {
        const token = await user.getIdToken()

        const res = await fetch(API_URLS.USER_ME, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!res.ok) throw new Error("Failed to load hospital profile")

        const data = await res.json()

        setHospitalName(
          data.hospital_name ||
          data.institution_name ||
          "Medical Institution"
        )
      } catch (err) {
        console.error("Failed to load hospital data:", err)
      }
    }

    async function loadPatients() {
      try {
        const token = await user.getIdToken()

        const res = await fetch(API_URLS.HOSPITAL_PATIENTS, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!res.ok) throw new Error("Failed to load patients")

        const data = await res.json()
        setPatients(data)
      } catch (err) {
        console.error("LOAD PATIENTS ERROR:", err)
      }
    }

    loadHospitalData()
    loadPatients()
  }, [user])

  async function sendAccessRequest() {
    if (!patientEmail) {
      alert("Enter patient email")
      return
    }

    try {
      setLoading(true)
      const token = await user.getIdToken()

      const res = await fetch(API_URLS.ACCESS_REQUEST, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email: patientEmail }),
      })

      if (!res.ok) throw new Error("Request failed")

      alert("Access request sent")
      setPatientEmail("")
      setShowModal(false)
    } catch (err) {
      console.error(err)
      alert("Failed to send request")
    } finally {
      setLoading(false)
    }
  }
  const filteredPatients = patients.filter(p =>
    (p.name || "").toLowerCase().includes(search.toLowerCase()) ||
    (p.email || "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div
        className="card"
        style={{
          marginBottom: 20,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h2 style={{ margin: 0 }}>{hospitalName}</h2>
        </div>

        <div style={{ textAlign: "right" }}>

          <div style={{ marginTop: 8 }}>
            <button
              className="btn-secondary"
              onClick={() => logout(navigate)}
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <p className="small-muted">
        Manage patients and request access
      </p>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <input
          className="input"
          placeholder="Search patient by name or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1 }}
        />
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          Add Patient
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {filteredPatients.length === 0 && (
          <div className="small-muted">No approved patients yet</div>
        )}

        {filteredPatients.map(p => (
          <div
            key={`patient-${p.uid}`}
            className="card"
            style={{
              padding: "12px 16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <strong>{p.name || "Unnamed Patient"}</strong>
              <div className="small-muted">{p.email}</div>
            </div>

            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn-primary"
                onClick={() =>
                  navigate(`/hospital/patient/${p.uid}/dashboard`)
                }
                style={{ fontSize: 12, padding: "4px 8px" }}
              >
                Dashboard
              </button>
              <button
                className="btn-secondary"
                onClick={() =>
                  navigate(`/hospital/patient/${p.uid}/profile`)
                }
                style={{ fontSize: 12, padding: "4px 8px" }}
              >
                Profile
              </button>
              <button
                className="btn-secondary"
                onClick={() =>
                  navigate(`/hospital/patient/${p.uid}/reports`)
                }
                style={{ fontSize: 12, padding: "4px 8px" }}
              >
                Reports
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-backdrop">
          <div className="card" style={{ maxWidth: 420 }}>
            <h3>Request Patient Access</h3>

            <input
              className="input"
              placeholder="Patient email"
              value={patientEmail}
              onChange={(e) => setPatientEmail(e.target.value)}
              style={{ marginTop: 12 }}
            />

            <div
              style={{
                display: "flex",
                gap: 8,
                marginTop: 16,
                justifyContent: "flex-end",
              }}
            >
              <button
                className="btn-secondary"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                disabled={loading}
                onClick={sendAccessRequest}
              >
                {loading ? "Sending..." : "Send Request"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}