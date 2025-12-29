/**
 * End-to-End tests for complete user workflows
 * Tests the entire application from user perspective
 */

import { test, expect, Page } from "@playwright/test";
import path from "path";

// Test configuration
const BASE_URL = process.env.E2E_BASE_URL || "http://localhost:5173";
const API_BASE_URL = process.env.E2E_API_URL || "http://localhost:8000";

// Mock user credentials
const PATIENT_EMAIL = "patient@test.com";
const PATIENT_PASSWORD = "testpassword123";
const HOSPITAL_EMAIL = "hospital@test.com";
const HOSPITAL_PASSWORD = "testpassword123";

// Helper functions
async function loginAsPatient(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"]', PATIENT_EMAIL);
  await page.fill('input[type="password"]', PATIENT_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/patient/dashboard");
}

async function loginAsHospital(page: Page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"]', HOSPITAL_EMAIL);
  await page.fill('input[type="password"]', HOSPITAL_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/hospital");
}

async function uploadTestReport(page: Page) {
  // Navigate to upload page
  await page.click('a[href="/patient/upload"]');
  await page.waitForURL("**/patient/upload");

  // Upload a test PDF file
  const testFilePath = path.join(__dirname, "fixtures", "sample-report.pdf");
  await page.setInputFiles('input[type="file"]', testFilePath);

  // Click upload button
  await page.click('button:has-text("Upload & Analyze")');

  // Wait for processing to complete
  await page.waitForSelector("text=Processing...", { timeout: 5000 });
  await page.waitForSelector("text=Complete!", { timeout: 30000 });
}

test.describe("Patient Workflow Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Set up API mocking if needed
    await page.route(`${API_BASE_URL}/api/v1/**`, (route) => {
      // Allow requests to pass through to actual backend
      route.continue();
    });
  });

  test("Complete patient registration and onboarding", async ({ page }) => {
    // Navigate to registration page
    await page.goto(`${BASE_URL}/register`);

    // Fill registration form
    await page.fill('input[type="email"]', PATIENT_EMAIL);
    await page.fill('input[type="password"]', PATIENT_PASSWORD);
    await page.fill('input[name="confirmPassword"]', PATIENT_PASSWORD);
    await page.selectOption('select[name="userType"]', "patient");
    await page.fill('input[name="name"]', "Test Patient");

    // Submit registration
    await page.click('button[type="submit"]');

    // Verify redirect to dashboard
    await page.waitForURL("**/patient/dashboard");
    await expect(page.locator("h1")).toContainText("Welcome");
  });

  test("Upload medical report and view results", async ({ page }) => {
    await loginAsPatient(page);

    // Upload test report
    await uploadTestReport(page);

    // Verify redirect to results page
    await expect(page).toHaveURL(/.*\/patient\/results\/.*/);

    // Verify test results are displayed
    await expect(page.locator("h1")).toContainText("Test Results Analysis");
    await expect(page.locator('[data-testid="test-results"]')).toBeVisible();

    // Verify metrics can be tracked
    const firstMetric = page.locator('[data-testid="metric-item"]').first();
    await firstMetric.click();
    await expect(firstMetric).toHaveClass(/border-blue-300/);
  });

  test("Generate AI analysis for report", async ({ page }) => {
    await loginAsPatient(page);
    await uploadTestReport(page);

    // Wait for results page
    await page.waitForURL(/.*\/patient\/results\/.*/);

    // Generate AI analysis
    await page.click('button:has-text("Generate Analysis")');
    await page.waitForSelector("text=Generating...", { timeout: 5000 });
    await page.waitForSelector('[data-testid="ai-analysis"]', {
      timeout: 30000,
    });

    // Verify analysis is displayed
    await expect(page.locator('[data-testid="ai-analysis"]')).toBeVisible();
    await expect(page.locator('[data-testid="ai-analysis"]')).toContainText(
      "recommendations"
    );
  });

  test("View report history and manage reports", async ({ page }) => {
    await loginAsPatient(page);

    // Navigate to report history
    await page.click('a[href="/patient/history"]');
    await page.waitForURL("**/patient/history");

    // Verify history page loads
    await expect(page.locator("h1")).toContainText("Report History");

    // If reports exist, verify they're displayed
    const reportItems = page.locator('[data-testid="report-item"]');
    const reportCount = await reportItems.count();

    if (reportCount > 0) {
      // Click on first report
      await reportItems.first().click();
      await expect(page).toHaveURL(/.*\/patient\/results\/.*/);
    }
  });

  test("Update profile information", async ({ page }) => {
    await loginAsPatient(page);

    // Navigate to profile page
    await page.click('a[href="/patient/profile"]');
    await page.waitForURL("**/patient/profile");

    // Update profile information
    await page.fill('input[name="height"]', "175");
    await page.fill('input[name="weight"]', "70");
    await page.fill('textarea[name="allergies"]', "Peanuts, Shellfish");

    // Save changes
    await page.click('button:has-text("Save Changes")');

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test("Use chat interface for health questions", async ({ page }) => {
    await loginAsPatient(page);

    // Open chat interface
    await page.click('[data-testid="chat-button"]');
    await page.waitForSelector('[data-testid="chat-interface"]');

    // Wait for connection
    await page.waitForSelector("text=Connected", { timeout: 10000 });

    // Send a message
    const messageInput = page.locator(
      'input[placeholder*="Ask me about your health"]'
    );
    await messageInput.fill("What do my test results mean?");
    await page.click('button:has-text("Send")');

    // Verify message appears
    await expect(
      page.locator('[data-testid="user-message"]').last()
    ).toContainText("What do my test results mean?");

    // Wait for AI response
    await page.waitForSelector('[data-testid="ai-message"]', {
      timeout: 15000,
    });
    await expect(
      page.locator('[data-testid="ai-message"]').last()
    ).toBeVisible();
  });
});

test.describe("Hospital Workflow Tests", () => {
  test("Hospital user can search and view patients", async ({ page }) => {
    await loginAsHospital(page);

    // Verify hospital dashboard loads
    await expect(page.locator("h1")).toContainText("Hospital Dashboard");

    // Search for patients
    const searchInput = page.locator('input[placeholder*="Search patients"]');
    await searchInput.fill("Test Patient");
    await page.keyboard.press("Enter");

    // Verify search results
    await page.waitForSelector('[data-testid="patient-list"]');
    const patientItems = page.locator('[data-testid="patient-item"]');

    if ((await patientItems.count()) > 0) {
      // Click on first patient
      await patientItems.first().click();

      // Verify patient details page
      await expect(
        page.locator('[data-testid="patient-details"]')
      ).toBeVisible();
    }
  });

  test("Hospital user can view patient reports", async ({ page }) => {
    await loginAsHospital(page);

    // Navigate to a patient's reports
    const patientItems = page.locator('[data-testid="patient-item"]');

    if ((await patientItems.count()) > 0) {
      await patientItems.first().click();

      // View patient reports
      await page.click('a:has-text("Reports")');
      await expect(
        page.locator('[data-testid="patient-reports"]')
      ).toBeVisible();

      // Click on a report if available
      const reportItems = page.locator('[data-testid="report-item"]');
      if ((await reportItems.count()) > 0) {
        await reportItems.first().click();
        await expect(
          page.locator('[data-testid="report-details"]')
        ).toBeVisible();
      }
    }
  });
});

test.describe("Real-time Synchronization Tests", () => {
  test("Real-time updates work across multiple sessions", async ({
    browser,
  }) => {
    // Create two browser contexts to simulate multiple sessions
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    try {
      // Login as same patient in both sessions
      await loginAsPatient(page1);
      await loginAsPatient(page2);

      // Navigate both to dashboard
      await page1.goto(`${BASE_URL}/patient/dashboard`);
      await page2.goto(`${BASE_URL}/patient/dashboard`);

      // Upload report in first session
      await page1.click('a[href="/patient/upload"]');
      await uploadTestReport(page1);

      // Verify second session receives update
      await page2.waitForSelector('[data-testid="notification"]', {
        timeout: 10000,
      });
      await expect(page2.locator('[data-testid="notification"]')).toContainText(
        "Report"
      );
    } finally {
      await context1.close();
      await context2.close();
    }
  });

  test("Chat synchronization across sessions", async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    try {
      await loginAsPatient(page1);
      await loginAsPatient(page2);

      // Open chat in both sessions
      await page1.click('[data-testid="chat-button"]');
      await page2.click('[data-testid="chat-button"]');

      // Send message in first session
      const messageInput1 = page1.locator(
        'input[placeholder*="Ask me about your health"]'
      );
      await messageInput1.fill("Test message from session 1");
      await page1.click('button:has-text("Send")');

      // Verify message appears in second session
      await page2.waitForSelector(
        '[data-testid="user-message"]:has-text("Test message from session 1")',
        { timeout: 10000 }
      );
    } finally {
      await context1.close();
      await context2.close();
    }
  });
});

test.describe("Error Handling Tests", () => {
  test("Handle network errors gracefully", async ({ page }) => {
    // Simulate network failure
    await page.route(`${API_BASE_URL}/api/v1/**`, (route) => {
      route.abort("failed");
    });

    await page.goto(`${BASE_URL}/login`);

    // Try to login
    await page.fill('input[type="email"]', PATIENT_EMAIL);
    await page.fill('input[type="password"]', PATIENT_PASSWORD);
    await page.click('button[type="submit"]');

    // Verify error message is displayed
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      "network"
    );
  });

  test("Handle file upload errors", async ({ page }) => {
    await loginAsPatient(page);

    // Navigate to upload page
    await page.click('a[href="/patient/upload"]');

    // Try to upload invalid file
    const invalidFilePath = path.join(
      __dirname,
      "fixtures",
      "invalid-file.txt"
    );
    await page.setInputFiles('input[type="file"]', invalidFilePath);

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      "PDF"
    );
  });

  test("Handle authentication errors", async ({ page }) => {
    // Mock authentication failure
    await page.route(`${API_BASE_URL}/api/v1/auth/**`, (route) => {
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      });
    });

    await page.goto(`${BASE_URL}/login`);

    // Try to login with invalid credentials
    await page.fill('input[type="email"]', "invalid@test.com");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      "Unauthorized"
    );
  });
});

test.describe("Performance Tests", () => {
  test("Page load times are acceptable", async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState("networkidle");

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000); // 3 seconds max
  });

  test("Large report processing is handled efficiently", async ({ page }) => {
    await loginAsPatient(page);

    // Upload large report
    const largeReportPath = path.join(
      __dirname,
      "fixtures",
      "large-report.pdf"
    );
    await page.goto(`${BASE_URL}/patient/upload`);
    await page.setInputFiles('input[type="file"]', largeReportPath);

    const startTime = Date.now();
    await page.click('button:has-text("Upload & Analyze")');

    // Wait for processing with reasonable timeout
    await page.waitForSelector("text=Complete!", { timeout: 60000 });

    const processingTime = Date.now() - startTime;
    expect(processingTime).toBeLessThan(60000); // 1 minute max
  });
});

test.describe("Accessibility Tests", () => {
  test("Application is keyboard navigable", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Navigate using keyboard
    await page.keyboard.press("Tab"); // Email field
    await page.keyboard.type(PATIENT_EMAIL);
    await page.keyboard.press("Tab"); // Password field
    await page.keyboard.type(PATIENT_PASSWORD);
    await page.keyboard.press("Tab"); // Submit button
    await page.keyboard.press("Enter");

    // Verify navigation worked
    await page.waitForURL("**/patient/dashboard");
  });

  test("Screen reader compatibility", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Check for proper ARIA labels and roles
    await expect(page.locator('input[type="email"]')).toHaveAttribute(
      "aria-label"
    );
    await expect(page.locator('input[type="password"]')).toHaveAttribute(
      "aria-label"
    );
    await expect(page.locator('button[type="submit"]')).toHaveAttribute(
      "aria-label"
    );
  });
});

// Test fixtures setup
test.beforeAll(async () => {
  // Create test fixtures directory if it doesn't exist
  const fixturesDir = path.join(__dirname, "fixtures");

  // This would create sample PDF files for testing
  // In a real implementation, you'd have actual test files
});

test.afterAll(async () => {
  // Cleanup test data if needed
});
