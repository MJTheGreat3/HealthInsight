import React from "react"
import { NavLink, Outlet, useParams, useNavigate } from "react-router-dom"

export default function HospitalPatientLayout() {
  const { uid } = useParams()
  const navigate = useNavigate()

  return (
    <div>
      {/* Unified Top Bar */}
      <div
        className="card"
        style={{
          marginBottom: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* LEFT: Page navigation */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <NavLink
            to={`/hospital/patient/${uid}/dashboard`}
            className={({ isActive }) =>
              isActive ? "btn-primary" : "btn-secondary"
            }
          >
            Dashboard
          </NavLink>

          <NavLink
            to={`/hospital/patient/${uid}/profile`}
            className={({ isActive }) =>
              isActive ? "btn-primary" : "btn-secondary"
            }
          >
            Profile
          </NavLink>

          <NavLink
            to={`/hospital/patient/${uid}/reports`}
            className={({ isActive }) =>
              isActive ? "btn-primary" : "btn-secondary"
            }
          >
            Reports
          </NavLink>
        </div>

        {/* RIGHT: Read-only badge + Back button */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              padding: "4px 10px",
              fontSize: 12,
              fontWeight: 600,
              borderRadius: 999,
              background: "#fee2e2",
              color: "#991b1b",
              whiteSpace: "nowrap",
            }}
          >
            Read-only access
          </span>

          <button
            className="btn-secondary"
            onClick={() => navigate("/hospital")}
          >
            ← Back to Hospital Dashboard
          </button>
        </div>
      </div>

      {/* Page Content */}
      <Outlet />
    </div>
  )
}
