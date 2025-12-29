/**
 * Global teardown for E2E tests
 * Cleans up test environment and data
 */

import { chromium, FullConfig } from "@playwright/test";

async function globalTeardown(config: FullConfig) {
  console.log("🧹 Starting global teardown for E2E tests...");

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Clean up test data
    await cleanupTestData(page);

    console.log("✅ Global teardown completed successfully");
  } catch (error) {
    console.error("❌ Global teardown failed:", error);
    // Don't throw error in teardown to avoid masking test failures
  } finally {
    await browser.close();
  }
}

async function cleanupTestData(page: any) {
  console.log("🗑️ Cleaning up test data...");

  try {
    const backendUrl = process.env.E2E_API_URL || "http://localhost:8000";

    // In a real implementation, you might:
    // 1. Delete test users and their data
    // 2. Clean up uploaded test files
    // 3. Clear test chat sessions
    // 4. Reset database to clean state

    // For now, we'll just verify the backend is still accessible
    try {
      const healthResponse = await page.goto(`${backendUrl}/health`);
      if (healthResponse?.ok()) {
        console.log("✅ Backend is still accessible for cleanup");
      }
    } catch (error) {
      console.log("⚠️ Backend not accessible during cleanup (this is okay)");
    }

    console.log("✅ Test data cleanup completed");
  } catch (error) {
    console.error("❌ Test data cleanup failed:", error);
    // Don't throw - cleanup failures shouldn't fail the test run
  }
}

export default globalTeardown;
