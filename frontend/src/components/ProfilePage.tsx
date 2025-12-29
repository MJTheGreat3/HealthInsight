import React, { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { Patient } from "../types";

interface BioData {
  height?: number;
  weight?: number;
  age?: number;
  gender?: string;
  allergies?: string[];
  medications?: string[];
  medicalHistory?: string[];
}

const ProfilePage: React.FC = () => {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [bioData, setBioData] = useState<BioData>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [newAllergy, setNewAllergy] = useState("");
  const [newMedication, setNewMedication] = useState("");
  const [newMedicalHistory, setNewMedicalHistory] = useState("");
  const { appUser, currentUser } = useAuth();

  useEffect(() => {
    if (appUser) {
      fetchProfile();
    }
  }, [appUser]);

  const fetchProfile = async () => {
    if (!appUser || !currentUser) return;

    try {
      setLoading(true);
      const token = await currentUser!.getIdToken();
      const response = await fetch("/api/v1/patients/profile", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch profile");
      }

      const profileData = await response.json();
      setPatient(profileData);
      setBioData(profileData.bioData || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!appUser || !currentUser) return;

    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      const token = await currentUser!.getIdToken();
      const response = await fetch("/api/v1/patients/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          bioData: bioData,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save profile");
      }

      setSuccessMessage("Profile updated successfully!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof BioData, value: any) => {
    setBioData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const addToArray = (
    field: "allergies" | "medications" | "medicalHistory",
    value: string
  ) => {
    if (!value.trim()) return;

    setBioData((prev) => ({
      ...prev,
      [field]: [...(prev[field] || []), value.trim()],
    }));

    // Clear the input
    if (field === "allergies") setNewAllergy("");
    if (field === "medications") setNewMedication("");
    if (field === "medicalHistory") setNewMedicalHistory("");
  };

  const removeFromArray = (
    field: "allergies" | "medications" | "medicalHistory",
    index: number
  ) => {
    setBioData((prev) => ({
      ...prev,
      [field]: (prev[field] || []).filter((_, i) => i !== index),
    }));
  };

  const calculateBMI = () => {
    if (bioData.height && bioData.weight) {
      const heightInMeters = bioData.height / 100;
      const bmi = bioData.weight / (heightInMeters * heightInMeters);
      return bmi.toFixed(1);
    }
    return null;
  };

  const getBMICategory = (bmi: number) => {
    if (bmi < 18.5) return { category: "Underweight", color: "text-blue-600" };
    if (bmi < 25) return { category: "Normal", color: "text-green-600" };
    if (bmi < 30) return { category: "Overweight", color: "text-yellow-600" };
    return { category: "Obese", color: "text-red-600" };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">
              Profile & Health Information
            </h1>
            <p className="text-sm text-gray-500">
              Manage your personal information to get more personalized AI
              analysis
            </p>
          </div>
        </div>

        {/* Success/Error Messages */}
        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="text-green-600 mr-3">
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <p className="text-green-800">{successMessage}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="text-red-600 mr-3">
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Basic Information
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    value={bioData.height || ""}
                    onChange={(e) =>
                      handleInputChange(
                        "height",
                        parseFloat(e.target.value) || undefined
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="170"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    value={bioData.weight || ""}
                    onChange={(e) =>
                      handleInputChange(
                        "weight",
                        parseFloat(e.target.value) || undefined
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="70"
                  />
                </div>
              </div>

              {/* BMI Calculation */}
              {calculateBMI() && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      BMI
                    </span>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-gray-900">
                        {calculateBMI()}
                      </div>
                      <div
                        className={`text-sm ${
                          getBMICategory(parseFloat(calculateBMI()!)).color
                        }`}
                      >
                        {getBMICategory(parseFloat(calculateBMI()!)).category}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    value={bioData.age || ""}
                    onChange={(e) =>
                      handleInputChange(
                        "age",
                        parseInt(e.target.value) || undefined
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="30"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={bioData.gender || ""}
                    onChange={(e) =>
                      handleInputChange("gender", e.target.value || undefined)
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer-not-to-say">Prefer not to say</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Tracked Metrics */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Tracked Metrics
              </h2>
              <p className="text-sm text-gray-500">
                Metrics you're currently tracking from your reports
              </p>
            </div>
            <div className="p-6">
              {patient?.favorites && patient.favorites.length > 0 ? (
                <div className="space-y-2">
                  {patient.favorites.map((metric, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-blue-50 rounded-lg"
                    >
                      <span className="text-sm font-medium text-blue-900">
                        {metric}
                      </span>
                      <span className="text-xs text-blue-600">Tracking</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg
                      className="w-12 h-12 mx-auto"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <p className="text-gray-500">
                    No metrics tracked yet. Upload reports and select concerning
                    results to track them.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Medical Information */}
        <div className="mt-6 bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Medical Information
            </h2>
            <p className="text-sm text-gray-500">
              This information helps provide more accurate AI analysis
            </p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Allergies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Allergies
                </label>
                <div className="space-y-2 mb-3">
                  {(bioData.allergies || []).map((allergy, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-red-50 rounded-md"
                    >
                      <span className="text-sm text-red-800">{allergy}</span>
                      <button
                        onClick={() => removeFromArray("allergies", index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newAllergy}
                    onChange={(e) => setNewAllergy(e.target.value)}
                    placeholder="Add allergy"
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) =>
                      e.key === "Enter" && addToArray("allergies", newAllergy)
                    }
                  />
                  <button
                    onClick={() => addToArray("allergies", newAllergy)}
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Current Medications */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Medications
                </label>
                <div className="space-y-2 mb-3">
                  {(bioData.medications || []).map((medication, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-blue-50 rounded-md"
                    >
                      <span className="text-sm text-blue-800">
                        {medication}
                      </span>
                      <button
                        onClick={() => removeFromArray("medications", index)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newMedication}
                    onChange={(e) => setNewMedication(e.target.value)}
                    placeholder="Add medication"
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) =>
                      e.key === "Enter" &&
                      addToArray("medications", newMedication)
                    }
                  />
                  <button
                    onClick={() => addToArray("medications", newMedication)}
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Medical History */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Medical History
                </label>
                <div className="space-y-2 mb-3">
                  {(bioData.medicalHistory || []).map((condition, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-yellow-50 rounded-md"
                    >
                      <span className="text-sm text-yellow-800">
                        {condition}
                      </span>
                      <button
                        onClick={() => removeFromArray("medicalHistory", index)}
                        className="text-yellow-600 hover:text-yellow-800"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newMedicalHistory}
                    onChange={(e) => setNewMedicalHistory(e.target.value)}
                    placeholder="Add condition"
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) =>
                      e.key === "Enter" &&
                      addToArray("medicalHistory", newMedicalHistory)
                    }
                  />
                  <button
                    onClick={() =>
                      addToArray("medicalHistory", newMedicalHistory)
                    }
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
