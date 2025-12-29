import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Report } from "../types";

const ReportHistory: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [filteredReports, setFilteredReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "name">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const navigate = useNavigate();
  const { appUser, currentUser } = useAuth();

  useEffect(() => {
    if (appUser) {
      fetchReports();
    }
  }, [appUser]);

  useEffect(() => {
    filterAndSortReports();
  }, [reports, searchTerm, dateFilter, sortBy, sortOrder]);

  const fetchReports = async () => {
    if (!appUser || !currentUser) return;

    try {
      setLoading(true);
      const token = await currentUser!.getIdToken();
      const response = await fetch("/api/v1/reports", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch reports");
      }

      const reportsData = await response.json();
      setReports(reportsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortReports = () => {
    let filtered = [...reports];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter((report) => {
        const searchLower = searchTerm.toLowerCase();
        return (
          report.reportId.toLowerCase().includes(searchLower) ||
          Object.values(report.attributes).some((attr) =>
            attr.name?.toLowerCase().includes(searchLower)
          )
        );
      });
    }

    // Apply date filter
    if (dateFilter) {
      const filterDate = new Date(dateFilter);
      filtered = filtered.filter((report) => {
        const reportDate = new Date(report.processedAt);
        return reportDate.toDateString() === filterDate.toDateString();
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;

      if (sortBy === "date") {
        comparison =
          new Date(a.processedAt).getTime() - new Date(b.processedAt).getTime();
      } else {
        comparison = a.reportId.localeCompare(b.reportId);
      }

      return sortOrder === "asc" ? comparison : -comparison;
    });

    setFilteredReports(filtered);
  };

  const getAbnormalCount = (report: Report) => {
    return Object.values(report.attributes).filter(
      (attr) => attr.verdict && attr.verdict !== "NORMAL"
    ).length;
  };

  const formatDate = (date: Date | string) => {
    return new Date(date).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your reports...</p>
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
            Unable to Load Reports
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchReports}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Report History
                </h1>
                <p className="text-sm text-gray-500">
                  View and manage your uploaded medical test reports
                </p>
              </div>
              <button
                onClick={() => navigate("/patient/upload")}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Upload New Report
              </button>
            </div>
          </div>

          {/* Filters and Search */}
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <input
                  type="text"
                  placeholder="Search reports..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as "date" | "name")}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="date">Date</option>
                  <option value="name">Report ID</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Order
                </label>
                <select
                  value={sortOrder}
                  onChange={(e) =>
                    setSortOrder(e.target.value as "asc" | "desc")
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Reports List */}
        {filteredReports.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-8 text-center">
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {reports.length === 0 ? "No Reports Yet" : "No Matching Reports"}
            </h3>
            <p className="text-gray-500 mb-4">
              {reports.length === 0
                ? "Upload your first medical test report to get started."
                : "Try adjusting your search or filter criteria."}
            </p>
            {reports.length === 0 && (
              <button
                onClick={() => navigate("/patient/upload")}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Upload First Report
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredReports.map((report) => (
              <div
                key={report.reportId}
                className="bg-white shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate(`/patient/results/${report.reportId}`)}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900">
                          Report {report.reportId}
                        </h3>
                        {report.llmOutput && (
                          <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                            AI Analysis Available
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Processed on {formatDate(report.processedAt)}
                      </p>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                        <span>
                          {Object.keys(report.attributes).length} test results
                        </span>
                        {getAbnormalCount(report) > 0 && (
                          <span className="text-orange-600">
                            {getAbnormalCount(report)} abnormal values
                          </span>
                        )}
                        {report.selectedConcerns &&
                          report.selectedConcerns.length > 0 && (
                            <span className="text-blue-600">
                              {report.selectedConcerns.length} tracked metrics
                            </span>
                          )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {Object.keys(report.attributes).length}
                        </div>
                        <div className="text-xs text-gray-500">Tests</div>
                      </div>
                      <div className="text-gray-400">
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary Stats */}
        {reports.length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {reports.length}
                </div>
                <div className="text-sm text-gray-500">Total Reports</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {reports.reduce(
                    (sum, report) => sum + getAbnormalCount(report),
                    0
                  )}
                </div>
                <div className="text-sm text-gray-500">Abnormal Results</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {reports.reduce(
                    (sum, report) =>
                      sum + (report.selectedConcerns?.length || 0),
                    0
                  )}
                </div>
                <div className="text-sm text-gray-500">Tracked Metrics</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportHistory;
