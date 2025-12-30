import React, { useState, useEffect } from "react"
import { useAuth } from "../auth/useAuth"
import { Building2, Calendar, Check, X, Shield, Clock, AlertCircle } from "lucide-react"



export default function AccessRequests() {
  const { user, loading } = useAuth()

  const [pendingRequests, setPendingRequests] = useState([])
  const [activeAccess, setActiveAccess] = useState([])
  const [fetching, setFetching] = useState(true)

  // FETCH DATA 
  async function fetchPendingRequests(token) {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/access/my-requests`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error("Failed to fetch requests")
    return res.json()
  }

  async function fetchActiveAccess(token) {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/access/active`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error("Failed to fetch active access")
    return res.json()
  }

  async function loadData() {
    try {
      const token = await user.getIdToken()

      const [allRequests, active] = await Promise.all([
        fetchPendingRequests(token),
        fetchActiveAccess(token),
      ])

      setPendingRequests(
        allRequests.filter(r => r.status === "pending")
      )
      setActiveAccess(active)
    } catch (err) {
      console.error("Failed to load access data:", err)
    } finally {
      setFetching(false)
    }
  }

  //  RESPOND 
  async function respond(request_id, action) {
    try {
      const token = await user.getIdToken()

      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/access/respond`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ request_id, action }),
      })

      if (!res.ok) throw new Error("Action failed")

      // Refresh data after action
      loadData()
    } catch (err) {
      console.error(err)
      alert("Failed to update access")
    }
  }

  useEffect(() => {
    if (user) loadData()
  }, [user])

  if (loading || fetching) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#64748b' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <div className="spinner" style={{ width: 32, height: 32, border: '3px solid #e2e8f0', borderTopColor: '#0d9488', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
          <span>Loading access data...</span>
        </div>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Hero Section */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
          <Shield size={28} color="#0d9488" />
          Access Management
        </h1>
        <p style={{ color: '#64748b', fontSize: 16 }}>
          Control which hospitals and institutions can view your medical records.
        </p>
      </div>

      <div style={{ display: 'grid', gap: 32 }}>
        
        {/* Pending Requests Section */}
        <div className="card" style={{ border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ background: '#fff7ed', padding: 8, borderRadius: 8 }}>
              <Clock size={20} color="#ea580c" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, color: '#0f172a' }}>Pending Requests</h3>
              <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>Hospitals waiting for your approval</p>
            </div>
            {pendingRequests.length > 0 && (
              <span style={{ marginLeft: 'auto', background: '#ea580c', color: '#fff', padding: '2px 10px', borderRadius: 99, fontSize: 12, fontWeight: 600 }}>
                {pendingRequests.length}
              </span>
            )}
          </div>

          {pendingRequests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8' }}>
              <Check size={48} style={{ opacity: 0.2, marginBottom: 12 }} />
              <p>No pending requests at the moment</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {pendingRequests.map(req => (
                <div key={req._id} style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center",
                  padding: 16,
                  background: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: 12,
                  transition: 'all 0.2s'
                }}>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <div style={{ width: 48, height: 48, background: '#f1f5f9', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                      <Building2 size={24} />
                    </div>
                    <div>
                      <strong style={{ display: 'block', color: '#0f172a', fontSize: 16 }}>{req.hospital_name || "Unknown Hospital"}</strong>
                      <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>{req.hospital_email}</div>
                      <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Calendar size={12} />
                        Requested {req.created_at ? new Date(req.created_at).toLocaleDateString() : "recently"}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      onClick={() => respond(req._id, "approve")}
                      style={{ 
                        display: 'flex', alignItems: 'center', gap: 6,
                        background: '#0d9488', color: '#fff', border: 'none', 
                        padding: '8px 16px', borderRadius: 8, fontWeight: 500, cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={e => e.currentTarget.style.background = '#0f766e'}
                      onMouseOut={e => e.currentTarget.style.background = '#0d9488'}
                    >
                      <Check size={16} /> Approve
                    </button>
                    <button
                      onClick={() => respond(req._id, "reject")}
                      style={{ 
                        display: 'flex', alignItems: 'center', gap: 6,
                        background: '#fff', color: '#ef4444', border: '1px solid #ef4444', 
                        padding: '8px 16px', borderRadius: 8, fontWeight: 500, cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={e => { e.currentTarget.style.background = '#fef2f2'; }}
                      onMouseOut={e => { e.currentTarget.style.background = '#fff'; }}
                    >
                      <X size={16} /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Access Section */}
        <div className="card" style={{ border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ background: '#ecfdf5', padding: 8, borderRadius: 8 }}>
              <Shield size={20} color="#059669" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, color: '#0f172a' }}>Active Access</h3>
              <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>Hospitals with access to your data</p>
            </div>
          </div>

          {activeAccess.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8' }}>
              <Shield size={48} style={{ opacity: 0.2, marginBottom: 12 }} />
              <p>No hospitals currently have access</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {activeAccess.map(h => (
                <div key={h.request_id} style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center",
                  padding: 16,
                  background: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: 12,
                }}>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <div style={{ width: 48, height: 48, background: '#f0fdfa', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0d9488' }}>
                      <Building2 size={24} />
                    </div>
                    <div>
                      <strong style={{ display: 'block', color: '#0f172a', fontSize: 16 }}>{h.hospital_name || "Hospital"}</strong>
                      <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>{h.hospital_email}</div>
                      <div style={{ fontSize: 12, color: '#059669', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Check size={12} />
                        Access granted on {h.approved_at ? new Date(h.approved_at).toLocaleDateString() : "—"}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => respond(h.request_id, "revoke")}
                    style={{ 
                      display: 'flex', alignItems: 'center', gap: 6,
                      background: '#f1f5f9', color: '#64748b', border: 'none', 
                      padding: '8px 16px', borderRadius: 8, fontWeight: 500, cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={e => { e.currentTarget.style.background = '#e2e8f0'; e.currentTarget.style.color = '#0f172a'; }}
                    onMouseOut={e => { e.currentTarget.style.background = '#f1f5f9'; e.currentTarget.style.color = '#64748b'; }}
                  >
                    Revoke Access
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}