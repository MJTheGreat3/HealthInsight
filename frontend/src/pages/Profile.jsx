import React, { useState, useEffect } from 'react'
import { sendEmailVerification } from "firebase/auth"
import { useAuth } from "../auth/useAuth"
import { useParams, useLocation } from "react-router-dom"
import { API_URLS } from "../utils/api"


export default function Profile({ readOnly: propReadOnly = false, hospitalView: propHospitalView = false, patientUid: propPatientUid }) {

    //Auth state
    const { uid: urlPatientUid } = useParams()
    const location = useLocation()
    const isHospitalView = propHospitalView || location.pathname.startsWith("/hospital/patient")
    const readOnly = propReadOnly || location.state?.readOnly === true

    const { user, loading: authLoading } = useAuth()

    //Email Verification
    const [email, setEmail] = useState("")
    const [emailVerified, setEmailVerified] = useState(false)
    const [sendingVerification, setSendingVerification] = useState(false)

    const [isEditing, setIsEditing] = useState(false)

    //Favorite Markers
    const [favoriteMarkers, setFavoriteMarkers] = useState([])
    const [newMarker, setNewMarker] = useState("")
    const [loadingMarkers, setLoadingMarkers] = useState(true)

    //Profile
    const [profile, setProfile] = useState(() => {
        try {
            const raw = localStorage.getItem("profile")
            return raw ? JSON.parse(raw) : {
                photo: "",
                name: "",
                gender: "",
                age: "",
                height: "",
                weight: "",
                blood_group: "",
                allergies: ""
            }
        } catch {
            return {
                photo: "",
                name: "",
                gender: "",
                age: "",
                height: "",
                weight: "",
                blood_group: "",
                allergies: ""
            }
        }
    })

    useEffect(() => {
        if (readOnly) {
            setIsEditing(false)
        }
    }, [readOnly])

    useEffect(() => {
        localStorage.setItem("profile", JSON.stringify(profile))
    }, [profile])

    // Determine which patient UID to use
    const targetUid = isHospitalView ? (propPatientUid || urlPatientUid) : user?.uid

    useEffect(() => {
        // Wait for auth to load and targetUid to be available
        if (authLoading || !targetUid || (!user && !isHospitalView)) return

        const fetchProfileFromBackend = async () => {
            try {
                if (!user) {
                    throw new Error("User not authenticated")
                }
                const token = await user.getIdToken()

                const url = isHospitalView
                    ? API_URLS.HOSPITAL_PATIENT(targetUid)
                    : API_URLS.USER_ME

                const res = await fetch(url, {

                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })

                if (!res.ok) {
                    throw new Error("Failed to fetch profile")
                }

                const data = await res.json()

                setEmail(data.email || "")
                setEmailVerified(true)

                setProfile({
                    photo: data.BioData?.photo || "",
                    name: data.name || "",
                    gender: data.BioData?.gender || "",
                    age: data.BioData?.age || "",
                    height: data.BioData?.height || "",
                    weight: data.BioData?.weight || "",
                    blood_group: data.BioData?.blood_group || "",
                    allergies: data.BioData?.allergies || "",
                })

                // Fetch favorite markers
                setFavoriteMarkers(data.Favorites || [])
                setLoadingMarkers(false)

            } catch (err) {
                console.error("PROFILE FETCH FAILED:", err)
            }
        }

        fetchProfileFromBackend()
    }, [user, isHospitalView, urlPatientUid])


    //Completion Wheel
    const REQUIRED_FIELDS = [
        "name",
        "gender",
        "age",
        "height",
        "weight",
        "blood_group",
        "allergies",
    ]

    const filledProfileFields = REQUIRED_FIELDS.filter(
        f => profile[f] && profile[f].toString().trim() !== ""
    ).length

    const totalFields = REQUIRED_FIELDS.length + 1 // + email verification
    const filledTotal = filledProfileFields + (emailVerified ? 1 : 0)

    const completionPercent = Math.round(
        (filledTotal / totalFields) * 100
    )

    const height = Number(profile.height) || 0
    const weight = Number(profile.weight) || 0
    const bmi =
        height > 0 ? (weight / ((height / 100) * (height / 100))).toFixed(1) : "—"

    if (authLoading) return <div className="card">Loading profile…</div>
    if (!user) return <div className="card">You are not logged in.</div>

    function updateField(e) {
        if (readOnly || !isEditing) return
        const { name, value } = e.target
        setProfile(prev => ({ ...prev, [name]: value }))
    }

    function handlePhotoUpload(e) {
        const file = e.target.files[0]
        if (!file) return

        const reader = new FileReader()
        reader.onload = () => {
            setProfile(prev => ({ ...prev, photo: reader.result }))
        }
        reader.readAsDataURL(file)
    }

    function removePhoto() {
        setProfile(prev => ({ ...prev, photo: "" }))
    }

    async function onSave() {
        try {
            // 1. Get Firebase ID token
            const token = await user.getIdToken()

            // 2. Call backend to update BioData
            const res = await fetch(API_URLS.USER_ME, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify(profile),
            })

            if (!res.ok) {
                throw new Error("Backend update failed")
            }

            // 3. Keep localStorage in sync (optional but good UX)
            localStorage.setItem("profile", JSON.stringify(profile))

            setIsEditing(false)

            alert("Profile saved to backend")
        } catch (err) {
            console.error("SAVE FAILED:", err)
            alert("Failed to save profile")
        }
    }

    async function addFavoriteMarker(markerName) {
        if (!markerName.trim()) return
        
        try {
            const token = await user.getIdToken()
            
            console.log("Adding favorite marker:", markerName)
            
            const res = await fetch(API_URLS.USER_FAVORITES, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ marker: markerName.trim() }),
            })

            console.log("Response status:", res.status)
            
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                console.error("Error response:", errorData)
                throw new Error(errorData.detail || `Failed to add favorite marker (${res.status})`)
            }
            
            const data = await res.json()
            console.log("Success response:", data)
            setFavoriteMarkers(data.favorites || [])
            setNewMarker("")
            alert("Marker added to favorites!")
        } catch (err) {
            console.error("Failed to add favorite marker:", err)
            alert(`Failed to add favorite marker: ${err.message}`)
        }
    }

    async function removeFavoriteMarker(markerName) {
        try {
            const token = await user.getIdToken()
            
            console.log("Removing favorite marker:", markerName)
            
            const res = await fetch(API_URLS.USER_FAVORITES, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ marker: markerName }),
            })

            console.log("Remove response status:", res.status)

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}))
                console.error("Error response:", errorData)
                throw new Error(errorData.detail || `Failed to remove favorite marker (${res.status})`)
            }
            
            const data = await res.json()
            console.log("Remove success response:", data)
            setFavoriteMarkers(data.favorites || [])
        } catch (err) {
            console.error("Failed to remove favorite marker:", err)
            alert(`Failed to remove favorite marker: ${err.message}`)
        }
    }

    function handleAddMarker(e) {
        e.preventDefault()
        addFavoriteMarker(newMarker)
    }

    //UI
    return (
        <div className="card" style={{ maxWidth: 980 }}>
            <h2>Profile</h2>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <div>
                    <strong>Email:</strong> {email || "—"}
                    {emailVerified ? (
                        <span style={{ color: "green", marginLeft: 10 }}>Verified</span>
                    ) : (
                        <button
                            className="btn-secondary"
                            style={{ marginLeft: 10 }}
                            disabled={sendingVerification}
                            onClick={async () => {
                                try {
                                    setSendingVerification(true)
                                    await sendEmailVerification(user, {
                                        url: "http://localhost:5173/profile",
                                        handleCodeInApp: false,
                                    })
                                    alert("Verification email sent")
                                } finally {
                                    setSendingVerification(false)
                                }
                            }}
                        >
                            Verify Email
                        </button>
                    )}
                </div>

                <div style={{ position: "relative", width: 70, height: 70 }}>
                    <svg width="70" height="70">
                        <circle cx="35" cy="35" r="28" stroke="#e5e7eb" strokeWidth="6" fill="none" />
                        <circle
                            cx="35"
                            cy="35"
                            r="28"
                            stroke={completionPercent === 100 ? "#16a34a" : "#0ea5a4"}
                            strokeWidth="6"
                            fill="none"
                            strokeDasharray={2 * Math.PI * 28}
                            strokeDashoffset={2 * Math.PI * 28 * (1 - completionPercent / 100)}
                            transform="rotate(-90 35 35)"
                            strokeLinecap="round"
                        />
                    </svg>
                    <div style={{
                        position: "absolute",
                        inset: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 13,
                        fontWeight: 600
                    }}>
                        {completionPercent}%
                    </div>
                </div>
            </div>

            <div className="profile-card">
                <div className="profile-left">

                    <div style={{ textAlign: "center" }}>
                        <label style={{ cursor: isEditing ? "pointer" : "default" }}>
                            <div className="profile-avatar" style={{ overflow: "hidden" }}>
                                {profile.photo ? (
                                    <img
                                        src={profile.photo}
                                        alt="Profile"
                                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                    />
                                ) : (
                                    profile.name
                                        ? profile.name.split(" ").map(s => s[0]).join("").slice(0, 2)
                                        : "JD"
                                )}
                            </div>

                            {isEditing && (
                                <input
                                    type="file"
                                    accept="image/*"
                                    hidden
                                    onChange={handlePhotoUpload}
                                />
                            )}
                        </label>

                        {isEditing && profile.photo && (
                            <button
                                className="btn-secondary"
                                style={{ marginTop: 6 }}
                                onClick={removePhoto}
                            >
                                Remove photo
                            </button>
                        )}
                    </div>


                    <div className="profile-stats">
                        <div className="stat"><strong>BMI</strong><div>{bmi}</div></div>
                        <div className="stat"><strong>Age</strong><div>{profile.age || "—"}</div></div>
                        <div className="stat"><strong>Weight</strong><div>{profile.weight || "—"} kg</div></div>
                    </div>

                    {/* Favorite Markers Section */}
                    <div style={{ marginTop: 24 }}>
                        <h4 style={{ marginBottom: 12, fontSize: 16 }}>Favorite Concern Markers</h4>
                        {loadingMarkers ? (
                            <p className="small-muted">Loading markers...</p>
                        ) : (
                            <>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
                                    {favoriteMarkers.length === 0 ? (
                                        <p className="small-muted">No favorite markers yet. Add markers to track them in your dashboard.</p>
                                    ) : (
                                        favoriteMarkers.map((marker, index) => (
                                            <div
                                                key={index}
                                                style={{
                                                    display: "inline-flex",
                                                    alignItems: "center",
                                                    gap: 6,
                                                    padding: "4px 8px",
                                                    backgroundColor: "#e5e7eb",
                                                    borderRadius: "16px",
                                                    fontSize: "12px",
                                                    color: "#374151"
                                                }}
                                            >
                                                {marker}
                                                {!readOnly && (
                                                    <button
                                                        onClick={() => removeFavoriteMarker(marker)}
                                                        style={{
                                                            background: "none",
                                                            border: "none",
                                                            color: "#ef4444",
                                                            cursor: "pointer",
                                                            padding: "0",
                                                            fontSize: "14px",
                                                            lineHeight: "1"
                                                        }}
                                                        title="Remove marker"
                                                    >
                                                        ×
                                                    </button>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>

                                {!readOnly && (
                                    <form onSubmit={handleAddMarker} style={{ display: "flex", gap: 8 }}>
                                        <input
                                            type="text"
                                            value={newMarker}
                                            onChange={(e) => setNewMarker(e.target.value)}
                                            placeholder="Add new marker..."
                                            className="input"
                                            style={{ flex: 1, fontSize: "12px", padding: "6px 8px" }}
                                        />
                                        <button
                                            type="submit"
                                            className="btn-primary"
                                            style={{ padding: "6px 12px", fontSize: "12px" }}
                                        >
                                            Add
                                        </button>
                                    </form>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="profile-right">
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <h3>Personal details</h3>
                        {isEditing ? (
                            <button
                                className="btn-primary"
                                disabled={readOnly}
                                onClick={onSave}
                            >
                                Save
                            </button>
                        ) : (
                            <button
                                className="btn-secondary"
                                disabled={readOnly}
                                onClick={() => setIsEditing(true)}
                            >
                                Edit
                            </button>
                        )}
                    </div>

                    <div className="form-grid">
                        <div>
                            <label>Full name</label>
                            <input disabled={!isEditing} name="name" value={profile.name} onChange={updateField} className="input" />
                        </div>

                        <div>
                            <label>Gender</label>
                            <select disabled={!isEditing} name="gender" value={profile.gender} onChange={updateField} className="input">
                                <option value="">Select</option>
                                <option value="female">Female</option>
                                <option value="male">Male</option>
                                <option value="other">Other</option>
                            </select>
                        </div>

                        <div>
                            <label>Height (cm)</label>
                            <input disabled={!isEditing} name="height" value={profile.height} onChange={updateField} className="input" />
                        </div>

                        <div>
                            <label>Weight (kg)</label>
                            <input disabled={!isEditing} name="weight" value={profile.weight} onChange={updateField} className="input" />
                        </div>

                        <div>
                            <label>Age</label>
                            <input disabled={!isEditing} name="age" value={profile.age} onChange={updateField} className="input" />
                        </div>

                        <div>
                            <label>Blood group</label>
                            <input disabled={!isEditing} name="blood_group" value={profile.blood_group} onChange={updateField} className="input" />
                        </div>

                        <div className="full">
                            <label>Allergies / Notes</label>
                            <textarea disabled={!isEditing} name="allergies" value={profile.allergies} onChange={updateField} className="input" rows={4} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
