import { initializeApp } from "firebase/app"
import { browserLocalPersistence, getAuth, setPersistence } from "firebase/auth"

const firebaseConfig = {
  apiKey: "AIzaSyDm4bERB6XEMk_QQINQHFZo0GpmLAwGTRI",
  authDomain: "hackxios-authentication.firebaseapp.com",
  projectId: "hackxios-authentication",
  storageBucket: "hackxios-authentication.firebasestorage.app",
  messagingSenderId: "295050118112",
  appId: "1:295050118112:web:582d42492681c977d16185"
}

let app
let auth

try {
  app = initializeApp(firebaseConfig)
  auth = getAuth(app)
  setPersistence(auth, browserLocalPersistence)
  console.log("Firebase initialized successfully")
} catch (error) {
  console.error("Firebase initialization error:", error)
  throw error
}

export { auth }