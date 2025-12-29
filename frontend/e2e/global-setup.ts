/**
 * Global setup for E2E tests
 * Prepares test environment and data
 */

import { chromium, FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig) {
  console.log("🚀 Starting global setup for E2E tests...");

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Wait for backend to be ready
    const backendUrl = process.env.E2E_API_URL || "http://localhost:8000";
    console.log(`⏳ Waiting for backend at ${backendUrl}...`);

    let retries = 30;
    while (retries > 0) {
      try {
        const response = await page.goto(`${backendUrl}/health`);
        if (response?.ok()) {
          console.log("✅ Backend is ready");
          break;
        }
      } catch (error) {
        // Backend not ready yet
      }

      retries--;
      if (retries === 0) {
        throw new Error("Backend failed to start within timeout");
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }

    // Wait for frontend to be ready
    const frontendUrl = process.env.E2E_BASE_URL || "http://localhost:5173";
    console.log(`⏳ Waiting for frontend at ${frontendUrl}...`);

    retries = 30;
    while (retries > 0) {
      try {
        const response = await page.goto(frontendUrl);
        if (response?.ok()) {
          console.log("✅ Frontend is ready");
          break;
        }
      } catch (error) {
        // Frontend not ready yet
      }

      retries--;
      if (retries === 0) {
        throw new Error("Frontend failed to start within timeout");
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }

    // Set up test data
    await setupTestData(page, backendUrl);

    console.log("✅ Global setup completed successfully");
  } catch (error) {
    console.error("❌ Global setup failed:", error);
    throw error;
  } finally {
    await browser.close();
  }
}

async function setupTestData(page: any, backendUrl: string) {
  console.log("📝 Setting up test data...");

  try {
    // Create test users if they don't exist
    // This would typically involve API calls to create test data

    // For now, we'll just verify the API is accessible
    const healthResponse = await page.goto(`${backendUrl}/health`);
    if (!healthResponse?.ok()) {
      throw new Error("Backend health check failed");
    }

    // In a real implementation, you might:
    // 1. Create test patient and hospital users
    // 2. Upload sample medical reports
    // 3. Generate test AI analyses
    // 4. Set up test chat sessions

    console.log("✅ Test data setup completed");
  } catch (error) {
    console.error("❌ Test data setup failed:", error);
    throw error;
  }
}

export default globalSetup;
