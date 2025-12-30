import React, { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import {
  createUserWithEmailAndPassword,
  sendEmailVerification,
} from "firebase/auth"
import { auth } from "../firebase/firebase"

const BACKEND_URL = "http://127.0.0.1:8000"

export default function Register() {
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [role, setRole] = useState("patient") // patient | institution
  const [hospitalName, setHospitalName] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleRegister = async () => {
    setError("")

    if (!email || !password || !confirmPassword) {
      setError("All fields are required")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    if (role === "institution" && !hospitalName.trim()) {
      setError("Hospital name is required")
      return
    }

    try {
      setLoading(true)

      // 1. Firebase signup
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      )

      const user = userCredential.user
      const token = await user.getIdToken()

      // 2. Send verification email (non-blocking)
      sendEmailVerification(user, {
        url: "http://localhost:5173/profile",
        handleCodeInApp: false,
      }).catch(() => {})

      // 3. Backend onboarding payload
      const payload = {
        user_type: role,
      }

      if (role === "institution") {
        payload.hospital_name = hospitalName
      }

      const res = await fetch(`${BACKEND_URL}/user`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(errText)
      }

      const data = await res.json()
      localStorage.setItem("user_id", data._id)

      // 4. Redirect by role
      if (role === "institution") {
        navigate("/hospital")
      } else {
        navigate("/dashboard")
      }
    } catch (err) {
      console.error(err)
      setError(err.message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 28 }}>
      <div className="card login-split">
        {/* LEFT */}
        <div className="login-left">
          <img src="/src/assets/illustration.png" alt="illustration" />
        </div>

        {/* RIGHT */}
        <div className="login-right">
          <div className="login-card">
            <h2>Create Account</h2>

            {error && <div className="error-box">{error}</div>}

            {/* ROLE TOGGLE */}
            <div className="toggle-role">
              <button
                className={role === "patient" ? "active" : ""}
                onClick={() => setRole("patient")}
              >
                Patient
              </button>
              <button
                className={role === "institution" ? "active" : ""}
                onClick={() => setRole("institution")}
              >
                Hospital
              </button>
            </div>

            {/* HOSPITAL NAME (ONLY FOR HOSPITAL) */}
            {role === "institution" && (
              <div className="form-row">
                <label>Hospital Name</label>
                <input
                  className="input"
                  type="text"
                  placeholder="Enter your Institution's Name"
                  value={hospitalName}
                  onChange={(e) => setHospitalName(e.target.value)}
                />
              </div>
            )}

            <div className="form-row">
              <label>Email</label>
              <input
                className="input"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Password</label>
              <input
                className="input"
                type="password"
                placeholder="••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Confirm Password</label>
              <input
                className="input"
                type="password"
                placeholder="••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                className="btn-primary"
                style={{ flex: 1 }}
                disabled={loading}
                onClick={handleRegister}
              >
                {loading ? "Creating account..." : "Register"}
              </button>
            </div>

            <div style={{ marginTop: 12, textAlign: "center" }}>
              <small className="small-muted">
                Already have an account? <Link to="/login">Login</Link>
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}