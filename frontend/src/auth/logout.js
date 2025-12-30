import { signOut } from "firebase/auth"
import { auth } from "../firebase/firebase"

export async function logout(navigate) {
  try {
    await signOut(auth)

    // clear all local state
    localStorage.clear()
    sessionStorage.clear()

    navigate("/login", { replace: true })
  } catch (err) {
    console.error("Logout failed:", err)
    alert("Logout failed")
  }
}
