/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useEffect, useState } from "react";
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  UserCredential,
} from "firebase/auth";
import { auth } from "../config/firebase";
import { User as AppUser } from "../types";
import { apiClient, ApiError } from "../services/api";

interface AuthContextType {
  currentUser: User | null;
  appUser: AppUser | null;
  login: (email: string, password: string) => Promise<UserCredential>;
  register: (email: string, password: string) => Promise<UserCredential>;
  logout: () => Promise<void>;
  loading: boolean;
  error: string | null;
  getIdToken: () => Promise<string | null>;
  refreshUserProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [appUser, setAppUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const login = async (
    email: string,
    password: string
  ): Promise<UserCredential> => {
    setError(null);
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      return result;
    } catch (error: any) {
      const errorMessage = error.message || "Login failed";
      setError(errorMessage);
      throw error;
    }
  };

  const register = async (
    email: string,
    password: string
  ): Promise<UserCredential> => {
    setError(null);
    try {
      const result = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      );
      return result;
    } catch (error: any) {
      const errorMessage = error.message || "Registration failed";
      setError(errorMessage);
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    setError(null);
    try {
      // Clear API client token
      apiClient.clearAuthToken();
      setAppUser(null);
      await signOut(auth);
    } catch (error: any) {
      const errorMessage = error.message || "Logout failed";
      setError(errorMessage);
      throw error;
    }
  };

  const getIdToken = async (): Promise<string | null> => {
    if (currentUser) {
      try {
        const token = await currentUser.getIdToken();
        return token;
      } catch (error) {
        console.error("Error getting ID token:", error);
        setError("Failed to get authentication token");
        return null;
      }
    }
    return null;
  };

  // Fetch user profile from backend when Firebase user changes
  const fetchUserProfile = async (firebaseUser: User): Promise<void> => {
    try {
      const token = await firebaseUser.getIdToken();
      apiClient.setAuthToken(token);

      // Try to get existing user profile
      try {
        const response = await apiClient.get("/auth/me");
        setAppUser(response.user);
        setError(null);
      } catch (apiError) {
        if (apiError instanceof ApiError && apiError.status === 404) {
          // User doesn't exist in backend, this is expected for new users
          console.log("User not found in backend, will need to register");
          setAppUser(null);
        } else {
          throw apiError;
        }
      }
    } catch (error) {
      console.error("Error fetching user profile:", error);
      if (error instanceof ApiError) {
        setError(`Failed to fetch user profile: ${error.message}`);
      } else {
        setError("Failed to fetch user profile");
      }
      setAppUser(null);
    }
  };

  // Refresh user profile from backend
  const refreshUserProfile = async (): Promise<void> => {
    if (currentUser) {
      await fetchUserProfile(currentUser);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        await fetchUserProfile(user);
      } else {
        setAppUser(null);
        apiClient.clearAuthToken();
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Clear error after 10 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const value: AuthContextType = {
    currentUser,
    appUser,
    login,
    register,
    logout,
    loading,
    error,
    getIdToken,
    refreshUserProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
