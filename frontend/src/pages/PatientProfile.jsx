import React from "react"
import Profile from "./Profile"
import { useParams } from "react-router-dom"

export default function HospitalPatientProfile() {
  const { uid } = useParams()

  return <Profile readOnly={true} hospitalView={true} patientUid={uid} />

}
