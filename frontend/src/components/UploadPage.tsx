import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useRealtimeData } from "../hooks/useRealtimeData";
import { apiService, ApiError } from "../services/api";
import LoadingSpinner, { ButtonLoader } from "./LoadingSpinner";

interface UploadProgress {
  progress: number;
  status: "idle" | "uploading" | "processing" | "success" | "error";
  message?: string;
}

const UploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    progress: 0,
    status: "idle",
  });
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { appUser, currentUser } = useAuth();
  const { notify } = useRealtimeData();

  const handleFileSelect = (file: File) => {
    if (file.type !== "application/pdf") {
      setUploadProgress({
        progress: 0,
        status: "error",
        message: "Please select a PDF file",
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      // 10MB limit
      setUploadProgress({
        progress: 0,
        status: "error",
        message: "File size must be less than 10MB",
      });
      return;
    }

    setSelectedFile(file);
    setUploadProgress({ progress: 0, status: "idle" });
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !appUser || !currentUser) return;

    setUploadProgress({ progress: 0, status: "uploading" });

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev.progress < 90) {
            return { ...prev, progress: prev.progress + 10 };
          }
          return prev;
        });
      }, 200);

      // Upload file using API service
      const result = await apiService.reports.upload(selectedFile, appUser.uid);

      clearInterval(progressInterval);
      setUploadProgress({ progress: 100, status: "processing" });

      // Poll for processing completion
      const pollProcessing = async (reportId: string) => {
        try {
          const statusResponse = await apiService.reports.getStatus(reportId);

          if (statusResponse.processing_status === "completed") {
            setUploadProgress({ progress: 100, status: "success" });

            // Notify about successful upload
            notify({
              type: "success",
              title: "Report Uploaded Successfully",
              message: "Your medical report has been processed and analyzed.",
            });

            // Navigate to results page with report ID
            navigate(`/patient/results/${reportId}`);
          } else if (statusResponse.processing_status === "failed") {
            throw new Error("Report processing failed");
          } else {
            // Still processing, poll again
            setTimeout(() => pollProcessing(reportId), 2000);
          }
        } catch (error) {
          console.error("Error checking processing status:", error);
          setUploadProgress({
            progress: 0,
            status: "error",
            message: "Failed to check processing status",
          });
        }
      };

      // Start polling for processing status
      if (result.report_id) {
        setTimeout(() => pollProcessing(result.report_id), 1000);
      }
    } catch (error) {
      console.error("Upload error:", error);
      let errorMessage = "Upload failed";

      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setUploadProgress({
        progress: 0,
        status: "error",
        message: errorMessage,
      });

      // Notify about upload failure
      notify({
        type: "error",
        title: "Upload Failed",
        message: errorMessage,
      });
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadProgress({ progress: 0, status: "idle" });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Upload Medical Test Report
            </h1>
            <p className="text-gray-600 mb-8">
              Upload your PDF medical test report to get AI-powered analysis and
              lifestyle recommendations.
            </p>

            {/* Upload Area */}
            <div
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? "border-blue-400 bg-blue-50"
                  : selectedFile
                  ? "border-green-400 bg-green-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileInputChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploadProgress.status === "uploading"}
              />

              {selectedFile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center">
                    <svg
                      className="w-12 h-12 text-green-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={resetUpload}
                    className="text-sm text-blue-600 hover:text-blue-800"
                    disabled={uploadProgress.status === "uploading"}
                  >
                    Choose different file
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-center">
                    <svg
                      className="w-12 h-12 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Drop your PDF file here, or click to browse
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports PDF files up to 10MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {uploadProgress.status !== "idle" && (
              <div className="mt-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {uploadProgress.status === "uploading" && "Uploading..."}
                    {uploadProgress.status === "processing" && "Processing..."}
                    {uploadProgress.status === "success" && "Complete!"}
                    {uploadProgress.status === "error" && "Error"}
                  </span>
                  <span className="text-sm text-gray-500">
                    {uploadProgress.progress}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      uploadProgress.status === "error"
                        ? "bg-red-500"
                        : uploadProgress.status === "success"
                        ? "bg-green-500"
                        : "bg-blue-500"
                    }`}
                    style={{ width: `${uploadProgress.progress}%` }}
                  />
                </div>
                {uploadProgress.message && (
                  <p
                    className={`text-sm mt-2 ${
                      uploadProgress.status === "error"
                        ? "text-red-600"
                        : "text-gray-600"
                    }`}
                  >
                    {uploadProgress.message}
                  </p>
                )}
              </div>
            )}

            {/* Upload Button */}
            <div className="mt-8 flex justify-end space-x-4">
              <button
                onClick={() => navigate("/patient/history")}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                View History
              </button>
              <button
                onClick={handleUpload}
                disabled={
                  !selectedFile ||
                  uploadProgress.status === "uploading" ||
                  uploadProgress.status === "processing"
                }
                className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {(uploadProgress.status === "uploading" ||
                  uploadProgress.status === "processing") && <ButtonLoader />}
                <span>
                  {uploadProgress.status === "uploading" ||
                  uploadProgress.status === "processing"
                    ? "Processing..."
                    : "Upload & Analyze"}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
