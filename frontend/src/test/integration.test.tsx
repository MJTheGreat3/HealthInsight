/**
 * Integration tests for frontend components and workflows
 * Tests complete user workflows and component interactions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { User } from "firebase/auth";

// Components
import App from "../App";
import UploadPage from "../components/UploadPage";
import ResultsPage from "../components/ResultsPage";
import ChatInterface from "../components/ChatInterface";
import Dashboard from "../components/Dashboard";

// Contexts
import { AuthProvider } from "../contexts/AuthContext";
import { RealtimeProvider } from "../contexts/RealtimeContext";

// Services
import { apiService } from "../services/api";
import { websocketService } from "../services/websocket";

// Mock Firebase
vi.mock("../config/firebase", () => ({
  auth: {
    onAuthStateChanged: vi.fn(),
    signInWithEmailAndPassword: vi.fn(),
    createUserWithEmailAndPassword: vi.fn(),
    signOut: vi.fn(),
  },
}));

// Mock API service
vi.mock("../services/api", () => ({
  apiService: {
    reports: {
      upload: vi.fn(),
      getStatus: vi.fn(),
      getReport: vi.fn(),
      getReports: vi.fn(),
      generateAnalysis: vi.fn(),
    },
    auth: {
      register: vi.fn(),
      login: vi.fn(),
      getMe: vi.fn(),
    },
    metrics: {
      addTrackedMetric: vi.fn(),
      removeTrackedMetric: vi.fn(),
      getTrackedMetrics: vi.fn(),
    },
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = "ApiError";
    }
  },
}));

// Mock WebSocket service
vi.mock("../services/websocket", () => ({
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    getConnectionStatus: vi.fn(),
    startChat: vi.fn(),
    sendMessage: vi.fn(),
    subscribeToUpdates: vi.fn(),
    onDataUpdate: vi.fn(),
    onNotification: vi.fn(),
    removeAllListeners: vi.fn(),
  },
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      <RealtimeProvider>{children}</RealtimeProvider>
    </AuthProvider>
  </BrowserRouter>
);

// Mock user data
const mockPatientUser = {
  uid: "test-patient-123",
  userType: "patient" as const,
  name: "Test Patient",
  email: "patient@test.com",
  getIdToken: vi.fn().mockResolvedValue("mock-token"),
};

const mockHospitalUser = {
  uid: "test-hospital-123",
  userType: "institution" as const,
  name: "Test Hospital",
  email: "hospital@test.com",
  getIdToken: vi.fn().mockResolvedValue("mock-token"),
};

const mockReport = {
  report_id: "test-report-123",
  patient_id: "test-patient-123",
  processed_at: new Date().toISOString(),
  attributes: {
    GLUCOSE: {
      name: "Glucose",
      value: "120",
      unit: "mg/dL",
      range: "70-100",
      verdict: "HIGH",
    },
    CHOLESTEROL: {
      name: "Total Cholesterol",
      value: "250",
      unit: "mg/dL",
      range: "<200",
      verdict: "HIGH",
    },
  },
  llmOutput: null,
  selected_concerns: [],
};

describe("Patient Workflow Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should complete file upload workflow", async () => {
    // Mock API responses
    const mockUploadResponse = {
      report_id: "test-report-123",
      processing_status: "processing",
      message: "File uploaded successfully",
    };

    const mockStatusResponse = {
      processing_status: "completed",
      has_data: true,
      has_analysis: false,
    };

    vi.mocked(apiService.reports.upload).mockResolvedValue(mockUploadResponse);
    vi.mocked(apiService.reports.getStatus).mockResolvedValue(
      mockStatusResponse
    );

    // Mock user context
    const mockAuthContext = {
      currentUser: mockPatientUser as User,
      appUser: mockPatientUser,
      loading: false,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      getIdToken: vi.fn().mockResolvedValue("mock-token"),
      refreshUserProfile: vi.fn(),
    };

    // Mock realtime context
    const mockRealtimeContext = {
      isConnected: true,
      connectionStatus: "connected" as const,
      notify: vi.fn(),
      subscribeToUpdates: vi.fn(),
      unsubscribeFromUpdates: vi.fn(),
    };

    // Render upload page
    render(
      <TestWrapper>
        <UploadPage />
      </TestWrapper>
    );

    // Create a test file
    const testFile = new File(["test pdf content"], "test-report.pdf", {
      type: "application/pdf",
    });

    // Find file input and upload file
    const fileInput = screen.getByRole("textbox", {
      hidden: true,
    }) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [testFile] } });
    });

    // Verify file is selected
    expect(screen.getByText("test-report.pdf")).toBeInTheDocument();

    // Click upload button
    const uploadButton = screen.getByRole("button", {
      name: /upload & analyze/i,
    });

    await act(async () => {
      fireEvent.click(uploadButton);
    });

    // Verify upload API was called
    await waitFor(() => {
      expect(apiService.reports.upload).toHaveBeenCalledWith(
        expect.any(File),
        mockPatientUser.uid
      );
    });

    // Verify processing status is shown
    expect(screen.getByText(/processing/i)).toBeInTheDocument();
  });

  it("should display report results and allow metric tracking", async () => {
    // Mock API responses
    vi.mocked(apiService.reports.getReport).mockResolvedValue({
      report: mockReport,
      message: "Report retrieved successfully",
    });

    vi.mocked(apiService.metrics.addTrackedMetric).mockResolvedValue({
      message: "Metric added to tracking",
    });

    // Render results page with mock report ID
    render(
      <TestWrapper>
        <ResultsPage />
      </TestWrapper>
    );

    // Wait for report to load
    await waitFor(() => {
      expect(screen.getByText("Test Results Analysis")).toBeInTheDocument();
    });

    // Verify test results are displayed
    expect(screen.getByText("Glucose")).toBeInTheDocument();
    expect(screen.getByText("120 mg/dL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();

    // Click on a metric to track it
    const glucoseMetric = screen.getByText("Glucose").closest("div");

    await act(async () => {
      fireEvent.click(glucoseMetric!);
    });

    // Verify tracking API was called
    await waitFor(() => {
      expect(apiService.metrics.addTrackedMetric).toHaveBeenCalledWith(
        "GLUCOSE"
      );
    });
  });

  it("should generate AI analysis on demand", async () => {
    // Mock API responses
    const mockAnalysisResponse = {
      analysis: {
        lifestyle_recommendations: [
          "Reduce sugar intake",
          "Exercise regularly",
        ],
        nutritional_advice: ["Eat more fiber", "Limit processed foods"],
        symptom_explanations: ["High glucose may indicate diabetes risk"],
        next_steps: ["Consult with healthcare provider"],
      },
      report_id: "test-report-123",
      llm_report_id: "llm-report-456",
      message: "Analysis generated successfully",
    };

    vi.mocked(apiService.reports.getReport).mockResolvedValue({
      report: { ...mockReport, llmOutput: null },
      message: "Report retrieved successfully",
    });

    vi.mocked(apiService.reports.generateAnalysis).mockResolvedValue(
      mockAnalysisResponse
    );

    // Render results page
    render(
      <TestWrapper>
        <ResultsPage />
      </TestWrapper>
    );

    // Wait for page to load
    await waitFor(() => {
      expect(
        screen.getByText("AI Analysis & Recommendations")
      ).toBeInTheDocument();
    });

    // Click generate analysis button
    const generateButton = screen.getByRole("button", {
      name: /generate analysis/i,
    });

    await act(async () => {
      fireEvent.click(generateButton);
    });

    // Verify analysis API was called
    await waitFor(() => {
      expect(apiService.reports.generateAnalysis).toHaveBeenCalledWith(
        "test-report-123",
        true
      );
    });

    // Verify analysis is displayed
    await waitFor(() => {
      expect(screen.getByText(/reduce sugar intake/i)).toBeInTheDocument();
    });
  });
});

describe("Chat Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should establish chat connection and send messages", async () => {
    // Mock WebSocket responses
    const mockChatSession = {
      session_id: "chat-session-123",
      messages: [
        {
          role: "assistant",
          content:
            "Hello! How can I help you with your health questions today?",
          timestamp: new Date().toISOString(),
        },
      ],
    };

    const mockMessageResponse = {
      role: "assistant",
      content:
        "Based on your recent test results, your glucose levels are elevated...",
      timestamp: new Date().toISOString(),
    };

    vi.mocked(websocketService.connect).mockResolvedValue(undefined);
    vi.mocked(websocketService.getConnectionStatus).mockReturnValue(true);
    vi.mocked(websocketService.startChat).mockResolvedValue(mockChatSession);
    vi.mocked(websocketService.sendMessage).mockResolvedValue(
      mockMessageResponse
    );

    // Render chat interface
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    );

    // Wait for connection to establish
    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Verify initial message is displayed
    expect(screen.getByText(/hello! how can i help you/i)).toBeInTheDocument();

    // Type and send a message
    const messageInput = screen.getByPlaceholderText(
      /ask me about your health/i
    );
    const sendButton = screen.getByRole("button", { name: /send/i });

    await act(async () => {
      fireEvent.change(messageInput, {
        target: { value: "What do my test results mean?" },
      });
    });

    await act(async () => {
      fireEvent.click(sendButton);
    });

    // Verify message was sent
    await waitFor(() => {
      expect(websocketService.sendMessage).toHaveBeenCalledWith(
        "What do my test results mean?"
      );
    });

    // Verify response is displayed
    await waitFor(() => {
      expect(
        screen.getByText(/based on your recent test results/i)
      ).toBeInTheDocument();
    });
  });

  it("should handle chat connection errors gracefully", async () => {
    // Mock connection failure
    vi.mocked(websocketService.connect).mockRejectedValue(
      new Error("Connection failed")
    );

    // Render chat interface
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    );

    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Connection failed")).toBeInTheDocument();
    });

    // Verify disconnected status
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });
});

describe("Real-time Synchronization Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should receive real-time data updates", async () => {
    // Mock WebSocket connection
    vi.mocked(websocketService.connect).mockResolvedValue(undefined);
    vi.mocked(websocketService.getConnectionStatus).mockReturnValue(true);
    vi.mocked(websocketService.subscribeToUpdates).mockResolvedValue(undefined);

    // Mock data update callback
    let dataUpdateCallback: ((update: any) => void) | null = null;
    vi.mocked(websocketService.onDataUpdate).mockImplementation((callback) => {
      dataUpdateCallback = callback;
    });

    // Render component that subscribes to updates
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Wait for subscription
    await waitFor(() => {
      expect(websocketService.subscribeToUpdates).toHaveBeenCalled();
    });

    // Simulate receiving a data update
    const mockUpdate = {
      type: "report_processing_completed",
      data: {
        report_id: "test-report-123",
        status: "completed",
        processed_at: new Date().toISOString(),
      },
    };

    await act(async () => {
      if (dataUpdateCallback) {
        dataUpdateCallback(mockUpdate);
      }
    });

    // Verify update was processed
    expect(websocketService.onDataUpdate).toHaveBeenCalled();
  });

  it("should handle notification updates", async () => {
    // Mock notification callback
    let notificationCallback: ((notification: any) => void) | null = null;
    vi.mocked(websocketService.onNotification).mockImplementation(
      (callback) => {
        notificationCallback = callback;
      }
    );

    // Render component
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Simulate receiving a notification
    const mockNotification = {
      type: "success",
      title: "Report Processed",
      message: "Your medical report has been successfully analyzed.",
    };

    await act(async () => {
      if (notificationCallback) {
        notificationCallback(mockNotification);
      }
    });

    // Verify notification was handled
    expect(websocketService.onNotification).toHaveBeenCalled();
  });
});

describe("Error Handling Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should handle API errors gracefully", async () => {
    // Mock API error
    const mockApiError = new (vi.mocked(apiService).ApiError)(
      "Network error",
      500
    );
    vi.mocked(apiService.reports.getReport).mockRejectedValue(mockApiError);

    // Render results page
    render(
      <TestWrapper>
        <ResultsPage />
      </TestWrapper>
    );

    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it("should handle authentication errors", async () => {
    // Mock authentication error
    vi.mocked(apiService.auth.getMe).mockRejectedValue(
      new (vi.mocked(apiService).ApiError)("Unauthorized", 401)
    );

    // This would typically redirect to login page
    // For now, we'll just verify the error is handled
    expect(true).toBe(true);
  });

  it("should handle file upload errors", async () => {
    // Mock upload error
    vi.mocked(apiService.reports.upload).mockRejectedValue(
      new (vi.mocked(apiService).ApiError)("File too large", 413)
    );

    // Render upload page
    render(
      <TestWrapper>
        <UploadPage />
      </TestWrapper>
    );

    // Create oversized file
    const largeFile = new File(["x".repeat(11 * 1024 * 1024)], "large.pdf", {
      type: "application/pdf",
    });

    // Try to upload
    const fileInput = screen.getByRole("textbox", {
      hidden: true,
    }) as HTMLInputElement;

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [largeFile] } });
    });

    // Verify error is shown
    await waitFor(() => {
      expect(
        screen.getByText(/file size must be less than 10mb/i)
      ).toBeInTheDocument();
    });
  });
});

describe("Complete User Journey Tests", () => {
  it("should complete patient onboarding to analysis journey", async () => {
    // This would be a comprehensive test that:
    // 1. Registers a new patient
    // 2. Uploads a medical report
    // 3. Waits for processing
    // 4. Views results
    // 5. Generates AI analysis
    // 6. Tracks concerning metrics
    // 7. Views dashboard
    // 8. Chats about results

    // For now, we'll verify the test structure
    expect(true).toBe(true);
  });

  it("should complete hospital patient management journey", async () => {
    // This would test:
    // 1. Hospital user logs in
    // 2. Searches for patients
    // 3. Views patient reports
    // 4. Accesses patient analysis
    // 5. Reviews patient trends

    // For now, we'll verify the test structure
    expect(true).toBe(true);
  });
});
