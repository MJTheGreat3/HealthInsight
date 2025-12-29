import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Patient, Report, MetricData } from "../types";
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

const PatientDashboard: React.FC = () => {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [metricTrends, setMetricTrends] = useState<MetricTrend[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { appUser, currentUser } = useAuth();

  useEffect(() => {
    if (appUser) {
      fetchDashboardData();
    }
  }, [appUser]);

  const fetchDashboardData = async () => {
    if (!appUser) return;

    try {
      setLoading(true);

      // Fetch patient profile and reports in parallel
      const token = await currentUser!.getIdToken();
      const [profileResponse, reportsResponse] = await Promise.all([
        fetch("/api/v1/patients/profile", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
        fetch("/api/v1/reports", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }),
      ]);

      if (!profileResponse.ok || !reportsResponse.ok) {
        throw new Error("Failed to fetch dashboard data");
      }

      const [profileData, reportsData] = await Promise.all([
        profileResponse.json(),
        reportsResponse.json(),
      ]);

      setPatient(profileData);
      setReports(reportsData);

      // Process metric trends
      processMetricTrends(reportsData, profileData.favorites || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
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
          // Only process metrics that are in favorites
          if (!favorites.includes(key) || !metric.value || !metric.unit) return;

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
    if (reports.length === 0) return [];

    const latestReport = reports[0]; // Assuming reports are sorted by date
    return Object.entries(latestReport.attributes)
      .filter(([_, metric]) => metric.verdict && metric.verdict !== "NORMAL")
      .slice(0, 5); // Show top 5 abnormal results
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
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
            Unable to Load Dashboard
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
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
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Health Dashboard
              </h1>
              <p className="text-gray-600">
                Welcome back, {patient?.name || "Patient"}
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => navigate("/patient/upload")}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Upload Report
              </button>
              <button
                onClick={() => navigate("/patient/profile")}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Profile
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
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
                        {reports.length}
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
                        {patient?.favorites?.length || 0}
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
                        {reports.length > 0
                          ? new Date(
                              reports[0].processedAt
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
                        No Tracked Metrics
                      </h3>
                      <p className="text-gray-500 mb-4">
                        Upload reports and select concerning results to see
                        trends here.
                      </p>
                      <button
                        onClick={() => navigate("/patient/upload")}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        Upload First Report
                      </button>
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
                        No abnormal results in your latest report
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Quick Actions
                  </h3>
                </div>
                <div className="p-6 space-y-3">
                  <button
                    onClick={() => navigate("/patient/upload")}
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
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    Upload New Report
                  </button>
                  <button
                    onClick={() => navigate("/patient/history")}
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
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    View Report History
                  </button>
                  <button
                    onClick={() => navigate("/patient/profile")}
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
                    Update Profile
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

export default PatientDashboard;
