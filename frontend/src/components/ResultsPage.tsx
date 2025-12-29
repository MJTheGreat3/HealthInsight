import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useRealtimeData } from "../hooks/useRealtimeData";
import { Report, MetricData } from "../types";
import { apiService, ApiError } from "../services/api";
import LoadingSpinner, { PageLoader, InlineLoader } from "./LoadingSpinner";
import ErrorBoundary from "./ErrorBoundary";

const ResultsPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [updatingConcerns, setUpdatingConcerns] = useState(false);
  const navigate = useNavigate();
  const { appUser, currentUser } = useAuth();
  const { notify } = useRealtimeData();

  useEffect(() => {
    if (reportId && appUser) {
      fetchReport();
    }
  }, [reportId, appUser]);

  const fetchReport = async () => {
    if (!reportId || !appUser || !currentUser) return;

    try {
      setLoading(true);
      setError(null);

      const reportData = await apiService.reports.getReport(reportId);
      setReport(reportData.report);
      setSelectedConcerns(reportData.report.selected_concerns || []);
    } catch (err) {
      console.error("Error fetching report:", err);
      let errorMessage = "Failed to load report";

      if (err instanceof ApiError) {
        errorMessage = err.message;
        if (err.status === 404) {
          errorMessage =
            "Report not found. It may have been deleted or you don't have access to it.";
        } else if (err.status === 403) {
          errorMessage = "You don't have permission to view this report.";
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const generateAnalysis = async () => {
    if (!report || !reportId) return;

    try {
      setAnalysisLoading(true);
      const analysisData = await apiService.reports.generateAnalysis(
        reportId,
        true
      );

      // Update report with new analysis
      setReport((prev) =>
        prev
          ? {
              ...prev,
              llmOutput: JSON.stringify(analysisData.analysis),
              llmReportId: analysisData.llm_report_id,
            }
          : null
      );

      notify({
        type: "success",
        title: "Analysis Generated",
        message: "AI analysis has been generated for your report.",
      });
    } catch (err) {
      console.error("Error generating analysis:", err);
      let errorMessage = "Failed to generate analysis";

      if (err instanceof ApiError) {
        errorMessage = err.message;
      }

      notify({
        type: "error",
        title: "Analysis Failed",
        message: errorMessage,
      });
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getVerdictColor = (verdict?: string) => {
    switch (verdict) {
      case "CRITICAL":
        return "text-red-700 bg-red-100";
      case "HIGH":
        return "text-orange-700 bg-orange-100";
      case "LOW":
        return "text-yellow-700 bg-yellow-100";
      case "NORMAL":
        return "text-green-700 bg-green-100";
      default:
        return "text-gray-700 bg-gray-100";
    }
  };

  const toggleConcern = async (metricName: string) => {
    if (!report || !appUser || !currentUser || updatingConcerns) return;

    const newConcerns = selectedConcerns.includes(metricName)
      ? selectedConcerns.filter((c) => c !== metricName)
      : [...selectedConcerns, metricName];

    try {
      setUpdatingConcerns(true);

      // Update tracked metrics via API
      if (selectedConcerns.includes(metricName)) {
        await apiService.metrics.removeTrackedMetric(metricName);
      } else {
        await apiService.metrics.addTrackedMetric(metricName);
      }

      setSelectedConcerns(newConcerns);

      notify({
        type: "success",
        title: selectedConcerns.includes(metricName)
          ? "Metric Untracked"
          : "Metric Tracked",
        message: `${metricName} ${
          selectedConcerns.includes(metricName) ? "removed from" : "added to"
        } your tracked metrics.`,
      });
    } catch (err) {
      console.error("Failed to update concerns:", err);

      let errorMessage = "Failed to update tracked metrics";
      if (err instanceof ApiError) {
        errorMessage = err.message;
      }

      notify({
        type: "error",
        title: "Update Failed",
        message: errorMessage,
      });
    } finally {
      setUpdatingConcerns(false);
    }
  };

  if (loading) {
    return <PageLoader text="Loading your results..." />;
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
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
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Unable to Load Results
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate("/patient/upload")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Upload New Report
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Test Results Analysis
                </h1>
                <p className="text-sm text-gray-500">
                  Report processed on{" "}
                  {report.processed_at
                    ? new Date(report.processed_at).toLocaleDateString()
                    : "Unknown date"}
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => navigate("/patient/history")}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  View History
                </button>
                <button
                  onClick={() => navigate("/patient/upload")}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Upload New Report
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Test Results */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Test Results
                </h2>
                <p className="text-sm text-gray-500">
                  Click on concerning results to track them over time
                </p>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {Object.entries(report.attributes).map(
                    ([key, metric]: [string, MetricData]) => (
                      <div
                        key={key}
                        className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                          selectedConcerns.includes(key)
                            ? "border-blue-300 bg-blue-50"
                            : "border-gray-200 hover:border-gray-300"
                        } ${
                          updatingConcerns
                            ? "opacity-50 cursor-not-allowed"
                            : ""
                        }`}
                        onClick={() => !updatingConcerns && toggleConcern(key)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900">
                              {metric.name || key}
                            </h3>
                            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-600">
                              <span className="font-semibold">
                                {metric.value} {metric.unit}
                              </span>
                              {metric.range && (
                                <span>Range: {metric.range}</span>
                              )}
                            </div>
                            {metric.remark && (
                              <p className="mt-1 text-sm text-gray-500">
                                {metric.remark}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center space-x-3">
                            {metric.verdict && (
                              <span
                                className={`px-2 py-1 text-xs font-semibold rounded-full ${getVerdictColor(
                                  metric.verdict
                                )}`}
                              >
                                {metric.verdict}
                              </span>
                            )}
                            {selectedConcerns.includes(key) && (
                              <div className="text-blue-600">
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
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">
                    AI Analysis & Recommendations
                  </h2>
                  {!report.llmOutput && (
                    <button
                      onClick={generateAnalysis}
                      disabled={analysisLoading}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {analysisLoading && (
                        <LoadingSpinner size="sm" color="white" />
                      )}
                      <span>
                        {analysisLoading
                          ? "Generating..."
                          : "Generate Analysis"}
                      </span>
                    </button>
                  )}
                </div>
              </div>
              <div className="p-6">
                {analysisLoading ? (
                  <InlineLoader text="Generating AI analysis..." />
                ) : report.llmOutput ? (
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {typeof report.llmOutput === "string"
                        ? report.llmOutput
                        : JSON.stringify(report.llmOutput, null, 2)}
                    </div>
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
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                      </svg>
                    </div>
                    <p className="text-gray-500 mb-4">
                      No AI analysis available yet. Click "Generate Analysis" to
                      create personalized health insights.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Tracked Metrics Info */}
            {selectedConcerns.length > 0 && (
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="text-blue-600 mr-3">
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-blue-900">
                      Tracking {selectedConcerns.length} metric
                      {selectedConcerns.length !== 1 ? "s" : ""}
                    </h3>
                    <p className="text-sm text-blue-700 mt-1">
                      These metrics will appear in your dashboard for trend
                      analysis.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
