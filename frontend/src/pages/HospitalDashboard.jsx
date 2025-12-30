import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../auth/useAuth"
import { logout } from "../auth/logout"
import { Search, UserPlus, Users, LogOut, Building2, X } from "lucide-react"



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

        const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/user/me`, {
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

        const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/hospital/patients`, {
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

      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/access/request`, {
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
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            <Building2 size={28} color="#0d9488" />
            {hospitalName}
          </h1>
          <p style={{ color: '#64748b', fontSize: 16 }}>Manage your patients and access requests</p>
        </div>
        <button 
          onClick={() => logout(navigate)}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <LogOut size={16} /> Logout
        </button>
      </div>

      {/* Actions Bar */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input
            className="input"
            placeholder="Search patients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 40, height: 44 }}
          />
        </div>
        <button 
          className="btn-primary" 
          onClick={() => setShowModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 8, height: 44 }}
        >
          <UserPlus size={18} /> Request Access
        </button>
      </div>

      {/* Patients List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {filteredPatients.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0', color: '#94a3b8', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>
            <Users size={48} style={{ opacity: 0.2, marginBottom: 12 }} />
            <p>No patients found</p>
          </div>
        ) : (
          filteredPatients.map(p => (
            <div
              key={`patient-${p.uid}`}
              className="card"
              style={{
                padding: 20,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'default'
              }}
              onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1)'; }}
              onMouseOut={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(14,30,37,0.06)'; }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontWeight: 600, fontSize: 18 }}>
                  {p.name ? p.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div>
                  <strong style={{ display: 'block', fontSize: 16, color: '#0f172a' }}>{p.name || "Unnamed Patient"}</strong>
                  <div style={{ fontSize: 14, color: '#64748b' }}>{p.email}</div>
                </div>
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="btn-secondary"
                  onClick={() => navigate(`/hospital/patient/${p.uid}/dashboard`)}
                  style={{ fontSize: 13 }}
                >
                  Dashboard
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => navigate(`/hospital/patient/${p.uid}/reports`)}
                  style={{ fontSize: 13 }}
                >
                  Reports
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50
        }} onClick={() => setShowModal(false)}>
          <div className="card" style={{ width: '100%', maxWidth: 420, padding: 24, animation: 'slideUp 0.2s ease-out' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: 20 }}>Request Access</h3>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>
            </div>

            <p style={{ color: '#64748b', marginBottom: 16, fontSize: 14 }}>
              Enter the patient's email address to request access to their medical records.
            </p>

            <input
              className="input"
              placeholder="patient@example.com"
              value={patientEmail}
              onChange={(e) => setPatientEmail(e.target.value)}
              style={{ marginBottom: 24 }}
              autoFocus
            />

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
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
                style={{ display: 'flex', alignItems: 'center', gap: 8 }}
              >
                {loading ? "Sending..." : <><UserPlus size={16} /> Send Request</>}
              </button>
            </div>
          </div>
        </div>
      )}
      <style>{`@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`}</style>
    </div>
  )
}