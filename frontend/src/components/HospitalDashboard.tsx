import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Patient, Report, MetricData } from "../types";
import PatientTable from "./PatientTable";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";
import { Line } from "react-chartjs-2";
import "chartjs-adapter-date-fns";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface MetricTrend {
  name: string;
  data: Array<{
    date: Date;
    value: number;
    verdict: string;
    unit: string;
  }>;
}

const HospitalDashboard: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientReports, setPatientReports] = useState<Report[]>([]);
  const [metricTrends, setMetricTrends] = useState<MetricTrend[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { patientId } = useParams();
  const { appUser, currentUser } = useAuth();

  useEffect(() => {
    if (patientId) {
      fetchPatientData(patientId);
    }
  }, [patientId]);

  const fetchPatientData = async (uid: string) => {
    if (!currentUser) return;

    try {
      setLoading(true);
      setError(null);

      const token = await currentUser.getIdToken();

      // Fetch patient profile and reports in parallel
      const [patientResponse, reportsResponse] = await Promise.all([
        fetch(`/api/v1/hospitals/patients/${uid}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
        fetch(`/api/v1/hospitals/patients/${uid}/reports`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
      ]);

      if (!patientResponse.ok || !reportsResponse.ok) {
        throw new Error("Failed to fetch patient data");
      }

      const [patientData, reportsData] = await Promise.all([
        patientResponse.json(),
        reportsResponse.json(),
      ]);

      setSelectedPatient(patientData);
      setPatientReports(reportsData);

      // Process metric trends
      processMetricTrends(reportsData, patientData.favorites || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load patient data"
      );
    } finally {
      setLoading(false);
    }
  };

  const processMetricTrends = (reports: Report[], favorites: string[]) => {
    const trends: Record<string, MetricTrend> = {};

    // Process each report
    reports.forEach((report) => {
      Object.entries(report.attributes).forEach(
        ([key, metric]: [string, MetricData]) => {
          // Only process metrics that are in favorites or all if no favorites
          if (favorites.length > 0 && !favorites.includes(key)) return;
          if (!metric.value || !metric.unit) return;

          const numericValue = parseFloat(metric.value);
          if (isNaN(numericValue)) return;

          if (!trends[key]) {
            trends[key] = {
              name: metric.name || key,
              data: [],
            };
          }

          trends[key].data.push({
            date: new Date(report.processedAt),
            value: numericValue,
            verdict: metric.verdict || "NORMAL",
            unit: metric.unit,
          });
        }
      );
    });

    // Sort data points by date for each metric
    Object.values(trends).forEach((trend) => {
      trend.data.sort((a, b) => a.date.getTime() - b.date.getTime());
    });

    setMetricTrends(Object.values(trends));

    // Set first metric as selected if none selected
    if (!selectedMetric && Object.keys(trends).length > 0) {
      setSelectedMetric(Object.keys(trends)[0]);
    }
  };

  const handlePatientSelect = (patient: Patient) => {
    navigate(`/hospital/patient/${patient.uid}`);
  };

  const getChartData = (trend: MetricTrend) => {
    return {
      labels: trend.data.map((point) => point.date),
      datasets: [
        {
          label: trend.name,
          data: trend.data.map((point) => ({
            x: point.date,
            y: point.value,
          })),
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          pointBackgroundColor: trend.data.map((point) => {
            switch (point.verdict) {
              case "CRITICAL":
                return "rgb(239, 68, 68)";
              case "HIGH":
                return "rgb(245, 158, 11)";
              case "LOW":
                return "rgb(245, 158, 11)";
              case "NORMAL":
                return "rgb(34, 197, 94)";
              default:
                return "rgb(107, 114, 128)";
            }
          }),
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          pointRadius: 6,
          tension: 0.1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: selectedMetric
          ? metricTrends.find((t) => t.name === selectedMetric)?.name
          : "Metric Trend",
      },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const point = context.raw;
            const dataPoint = metricTrends.find(
              (t) => t.name === selectedMetric
            )?.data[context.dataIndex];
            return `${context.dataset.label}: ${point.y} ${
              dataPoint?.unit || ""
            } (${dataPoint?.verdict || ""})`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "time" as const,
        time: {
          displayFormats: {
            day: "MMM dd",
            week: "MMM dd",
            month: "MMM yyyy",
          },
        },
        title: {
          display: true,
          text: "Date",
        },
      },
      y: {
        title: {
          display: true,
          text: "Value",
        },
      },
    },
  };

  const getRecentAbnormalResults = () => {
    if (patientReports.length === 0) return [];

    const latestReport = patientReports[0]; // Assuming reports are sorted by date
    return Object.entries(latestReport.attributes)
      .filter(([_, metric]) => metric.verdict && metric.verdict !== "NORMAL")
      .slice(0, 5); // Show top 5 abnormal results
  };

  const handleLogout = async () => {
    try {
      const { logout } = useAuth();
      await logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  // Show patient table if no specific patient is selected
  if (!patientId) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Hospital Dashboard
                </h1>
                <p className="text-gray-600">
                  Welcome, {appUser?.name || "Hospital User"}
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <span className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
                  {appUser?.userType}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <PatientTable onPatientSelect={handlePatientSelect} />
          </div>
        </main>
      </div>
    );
  }

  // Show individual patient dashboard
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading patient data...</p>
        </div>
      </div>
    );
  }

  if (error) {
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
            Unable to Load Patient Data
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="space-x-4">
            <button
              onClick={() => fetchPatientData(patientId!)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate("/hospital")}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Back to Patient List
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate("/hospital")}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Patient Dashboard
                </h1>
                <p className="text-gray-600">
                  {selectedPatient?.name || "Patient"} - Medical Overview
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
                Hospital View
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Patient Info Summary */}
          <div className="bg-white shadow rounded-lg mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Patient Information
              </h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Patient Name
                  </h3>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedPatient?.name || "Not provided"}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Patient ID
                  </h3>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedPatient?.uid.substring(0, 12)}...
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Bio Data
                  </h3>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedPatient?.bioData &&
                    Object.keys(selectedPatient.bioData).length > 0
                      ? `${Object.keys(selectedPatient.bioData).length} fields`
                      : "Not provided"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-blue-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Reports
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {patientReports.length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-green-600"
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
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Tracked Metrics
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {selectedPatient?.favorites?.length || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-yellow-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Abnormal Results
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {getRecentAbnormalResults().length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-purple-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3a4 4 0 118 0v4m-4 8a4 4 0 11-8 0v-4a4 4 0 018 0v4z"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Last Report
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {patientReports.length > 0
                          ? new Date(
                              patientReports[0].processedAt
                            ).toLocaleDateString()
                          : "None"}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Chart Section */}
            <div className="lg:col-span-2">
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Metric Trends
                    </h2>
                    {metricTrends.length > 1 && (
                      <select
                        value={selectedMetric || ""}
                        onChange={(e) => setSelectedMetric(e.target.value)}
                        className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {metricTrends.map((trend) => (
                          <option key={trend.name} value={trend.name}>
                            {trend.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
                <div className="p-6">
                  {metricTrends.length > 0 && selectedMetric ? (
                    <div style={{ height: "400px" }}>
                      <Line
                        data={getChartData(
                          metricTrends.find((t) => t.name === selectedMetric)!
                        )}
                        options={chartOptions}
                      />
                    </div>
                  ) : (
                    <div className="text-center py-16">
                      <div className="text-gray-400 mb-4">
                        <svg
                          className="w-16 h-16 mx-auto"
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
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        No Metric Data Available
                      </h3>
                      <p className="text-gray-500">
                        This patient has no tracked metrics or report data to
                        display.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Recent Abnormal Results */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Recent Concerns
                  </h3>
                </div>
                <div className="p-6">
                  {getRecentAbnormalResults().length > 0 ? (
                    <div className="space-y-3">
                      {getRecentAbnormalResults().map(([key, metric]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between p-3 bg-red-50 rounded-lg"
                        >
                          <div>
                            <p className="text-sm font-medium text-red-900">
                              {metric.name || key}
                            </p>
                            <p className="text-xs text-red-600">
                              {metric.value} {metric.unit}
                            </p>
                          </div>
                          <span className="px-2 py-1 text-xs font-semibold bg-red-200 text-red-800 rounded-full">
                            {metric.verdict}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-green-500 mb-2">
                        <svg
                          className="w-8 h-8 mx-auto"
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
                      <p className="text-sm text-gray-500">
                        No abnormal results in latest report
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Patient Actions */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Patient Actions
                  </h3>
                </div>
                <div className="p-6 space-y-3">
                  <button
                    onClick={() =>
                      navigate(`/hospital/patient/${patientId}/reports`)
                    }
                    className="w-full flex items-center px-4 py-3 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100"
                  >
                    <svg
                      className="w-5 h-5 mr-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    View All Reports
                  </button>
                  <button
                    onClick={() =>
                      navigate(`/hospital/patient/${patientId}/profile`)
                    }
                    className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                  >
                    <svg
                      className="w-5 h-5 mr-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                    View Profile Details
                  </button>
                  <button
                    onClick={() => navigate("/hospital")}
                    className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100"
                  >
                    <svg
                      className="w-5 h-5 mr-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                    Back to Patient List
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default HospitalDashboard;
