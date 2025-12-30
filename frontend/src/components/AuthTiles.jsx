import React, { useState, useEffect } from 'react'
import './AuthTiles.css'
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, sendEmailVerification } from 'firebase/auth'
import { auth } from '../firebase/firebase'



export default function AuthTiles({ initial = 'login' }) {
  const [tab, setTab] = useState(initial)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Login fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Register fields
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirm, setRegConfirm] = useState('')
  const [role, setRole] = useState('patient')
  const [hospitalName, setHospitalName] = useState('')

  useEffect(() => setTab(initial), [initial])

  async function handleLogin() {
    setError('')
    setMessage('')
    if (!email || !password) return setError('Email and password are required')
    try {
      setLoading(true)
      const userCred = await signInWithEmailAndPassword(auth, email, password)
      const user = userCred.user
      const token = await user.getIdToken()

      // Check role
      const res = await fetch(`/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (res.ok) {
        const data = await res.json()
        if (data.role === 'institution') {
          window.location.href = '/hospital'
          return
        }
      }
      
      window.location.href = '/dashboard'
    } catch (e) {
      console.error(e)
      setError(e.message || 'Login failed')
    } finally { setLoading(false) }
  }

  async function handleRegister() {
    setError('')
    setMessage('')
    if (!regEmail || !regPassword) return setError('All fields are required')
    if (regPassword !== regConfirm) return setError('Passwords do not match')
    try {
      setLoading(true)
      const uc = await createUserWithEmailAndPassword(auth, regEmail, regPassword)
      const user = uc.user
      sendEmailVerification(user).catch(()=>{})

      // Backend onboarding (best-effort)
      try {
        const token = await user.getIdToken()
        const payload = { user_type: role }
        if (role === 'institution') payload.hospital_name = hospitalName
        await fetch(`/api/user`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload),
        })
      } catch (err) {
        console.warn('Backend onboarding failed', err)
      }

      // reset and go to login
      setTab('login')
      setEmail(regEmail)
      setPassword('')
      setRegEmail('')
      setRegPassword('')
      setRegConfirm('')
      setRole('patient')
      setHospitalName('')
      setMessage('Registration successful — check your email for verification')
    } catch (e) {
      setError(e.message || 'Registration failed')
    } finally { setLoading(false) }
  }

  function toggleTab() {
    setError('')
    setMessage('')
    setTab(prev => (prev === 'login' ? 'register' : 'login'))
  }

  return (
    <div className="auth-viewport">
      <div className="auth-bg" />
      <div className="auth-center">
        <div className={`auth-tiles`}>
          <div className="auth-strip">
            <div className="strip-inner">
              <div className="strip-logo">
                <div style={{ 
                    width: 36, 
                    height: 36, 
                    borderRadius: 10, 
                    background: 'rgba(255,255,255,0.2)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    backdropFilter: 'blur(4px)'
                }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                </div>
                <span>HealthInsight</span>
              </div>
              <div className="strip-main">
                <h1>Smart Health <br/>Management</h1>
                <p>Access your medical reports, get AI insights, and track your health journey in one place.</p>
              </div>
            </div>
          </div>
          <div className="tile">
            <div className="tile-header">
              <h2 className="tile-heading">{tab === 'login' ? 'Welcome back' : 'Create account'}</h2>
              <button className="toggle-single" onClick={toggleTab}>{tab === 'login' ? 'Create account' : 'Sign in'}</button>
            </div>
            <div className="tile-inner">
              {message && <div className="message-box">{message}</div>}
              {error && <div className="error-box">{error}</div>}

              {tab === 'login' ? (
                <>
                  <h1 className="tile-title">Sign in to <span className="accent">HealthInsight</span></h1>
                  <p className="tile-sub">Securely manage your lab reports and insights.</p>

                  <div className="form-row">
                    <label>Email</label>
                    <input className="input" value={email} onChange={e=>setEmail(e.target.value)} />
                  </div>
                  <div className="form-row">
                    <label>Password</label>
                    <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
                  </div>

                  <div className="actions-row">
                    <button className="btn-primary" onClick={handleLogin} disabled={loading}>{loading? 'Signing in...':'Sign in'}</button>
                  </div>

                  <div className="legal small-muted">By continuing you agree to our <a className="link-secondary" href="#">Terms</a></div>
                </>
              ) : (
                <>
                  <h1 className="tile-title">Create your <span className="accent">account</span></h1>
                  <p className="tile-sub">Start uploading reports and get AI-driven suggestions.</p>

                  <div className="form-row">
                    <label>Account type</label>
                    <div className="toggle-role">
                      <button className={role === 'patient' ? 'active' : ''} onClick={()=>setRole('patient')}>Patient</button>
                      <button className={role === 'institution' ? 'active' : ''} onClick={()=>setRole('institution')}>Hospital</button>
                    </div>
                  </div>

                  {role === 'institution' && (
                    <div className="form-row">
                      <label>Hospital name</label>
                      <input className="input" value={hospitalName} onChange={e=>setHospitalName(e.target.value)} />
                    </div>
                  )}

                  <div className="form-row">
                    <label>Email</label>
                    <input className="input" value={regEmail} onChange={e=>setRegEmail(e.target.value)} />
                  </div>
                  <div className="form-row">
                    <label>Password</label>
                    <input className="input" type="password" value={regPassword} onChange={e=>setRegPassword(e.target.value)} />
                  </div>
                  <div className="form-row">
                    <label>Confirm</label>
                    <input className="input" type="password" value={regConfirm} onChange={e=>setRegConfirm(e.target.value)} />
                  </div>

                  <div className="actions-row">
                    <button className="btn-primary" onClick={handleRegister} disabled={loading}>{loading? 'Creating...':'Create account'}</button>
                  </div>

                  <div className="legal small-muted">Already have account? <a className="link-secondary" onClick={()=>setTab('login')}>Sign in</a></div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
