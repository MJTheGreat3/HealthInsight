import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signInWithEmailAndPassword } from "firebase/auth"
import { auth } from "../firebase/firebase"

export default function Login() {
    const navigate = useNavigate()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleLogin() {
        setError("")

        if (!email || !password) {
            setError("Email and password are required")
            return
        }

        try {
            setLoading(true)

            // 1. Firebase login
            const userCredential = await signInWithEmailAndPassword(
                auth,
                email,
                password
            )

            const user = userCredential.user

            if (!user.emailVerified) {
                console.warn("User email not verified")
            }

            // 2. Get Firebase ID token
            const token = await user.getIdToken()

            // 3. Call backend /me
            const response = await fetch("http://127.0.0.1:8000/auth/me", {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                throw new Error("Backend authentication failed")
            }

            const data = await response.json()
            console.log("Backend /me response:", data)

            // 4. Persist auth info
            localStorage.setItem("auth_uid", data.uid)
            localStorage.setItem("auth_email", data.email)
            localStorage.setItem("auth_role", data.role)

            // 5. Redirect by role
            if (data.role === "institution") {
                navigate("/hospital")
            } else {
                navigate("/dashboard")
            }

        } catch (err) {
            console.error("Login error details:", {
                code: err.code,
                message: err.message,
                customData: err.customData
            })

            // Provide more specific error messages
            if (err.code === 'auth/invalid-credential') {
                setError("Invalid email or password. Please check your credentials and try again.")
            } else if (err.code === 'auth/user-not-found') {
                setError("No account found with this email address.")
            } else if (err.code === 'auth/wrong-password') {
                setError("Incorrect password. Please try again.")
            } else if (err.code === 'auth/too-many-requests') {
                setError("Too many failed attempts. Please try again later.")
            } else if (err.code === 'auth/network-request-failed') {
                setError("Network error. Please check your internet connection.")
            } else if (err.message && err.message.includes("Backend authentication failed")) {
                setError("Backend authentication failed. Please try again or contact support.")
            } else {
                setError(err.message || "Login failed")
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ padding: 28 }}>
            <div className="card login-split">
                <div className="login-left">
                    <img src="/illustration.png" alt="illustration" />
                </div>

                <div className="login-right">
                    <div className="login-card">
                        <h2 style={{ marginTop: 0 }}>Login</h2>

                        {error && (
                            <div className="error-box">
                                {error}
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
                            <label>
                                Password
                                <small style={{ float: 'right' }}>
                                    <a className="link-secondary" href="#">Forgot password?</a>
                                </small>
                            </label>
                            <input
                                className="input"
                                type="password"
                                placeholder="••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>

                        <div style={{ display: 'flex', gap: 8 }}>
                            <button
                                type="button"
                                className="btn-primary"
                                style={{ flex: 1 }}
                                disabled={loading}
                                onClick={handleLogin}
                            >
                                {loading ? "Logging in..." : "Login"}
                            </button>
                        </div>

                        <div style={{ marginTop: 12, textAlign: 'center' }}>
                            <small className="small-muted">
                                No account? <Link to="/register">Register</Link>
                            </small>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    )
}
