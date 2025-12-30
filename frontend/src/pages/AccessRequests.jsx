import React, { useState, useEffect } from "react"
import { useAuth } from "../auth/useAuth"

const BACKEND_URL = "http://127.0.0.1:8000"

export default function AccessRequests() {
  const { user, loading } = useAuth()

  const [pendingRequests, setPendingRequests] = useState([])
  const [activeAccess, setActiveAccess] = useState([])
  const [fetching, setFetching] = useState(true)

  // FETCH DATA 
  async function fetchPendingRequests(token) {
    const res = await fetch(`${BACKEND_URL}/access/my-requests`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error("Failed to fetch requests")
    return res.json()
  }

  async function fetchActiveAccess(token) {
    const res = await fetch(`${BACKEND_URL}/access/active`, {
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

      const res = await fetch(`${BACKEND_URL}/access/respond`, {
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
    return <div className="card">Loading access data…</div>
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Hospitals with Access</h3>
        <p className="small-muted">
          These hospitals currently have access to your medical data
        </p>

        {activeAccess.length === 0 && (
          <div className="small-muted">No hospitals currently have access</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {activeAccess.map(h => (
            <div
              key={h.request_id}
              className="card"
              style={{
                padding: 16,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <strong>{h.hospital_name || "Hospital"}</strong>
                <div className="small-muted">{h.hospital_email}</div>
                <div className="small-muted">
                  Approved on{" "}
                  {h.approved_at
                    ? new Date(h.approved_at).toLocaleDateString()
                    : "—"}
                </div>
              </div>

              <button
                className="btn-secondary"
                onClick={() => respond(h.request_id, "revoke")}
              >
                Revoke Access
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Pending Access Requests</h3>
        <p className="small-muted">
          Hospitals requesting access to your data
        </p>

        {pendingRequests.length === 0 && (
          <div className="small-muted">No pending requests</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {pendingRequests.map(req => (
            <div
              key={req._id}
              className="card"
              style={{
                padding: 16,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <strong>{req.hospital_name || "Hospital"}</strong>
                <div className="small-muted">{req.hospital_email}</div>
                <div className="small-muted">
                  Requested on{" "}
                  {req.created_at
                    ? new Date(req.created_at).toLocaleDateString()
                    : "—"}
                </div>
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="btn-primary"
                  onClick={() => respond(req._id, "approve")}
                >
                  Approve
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => respond(req._id, "reject")}
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}