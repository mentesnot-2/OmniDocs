import { test, expect } from "@playwright/test";

test.describe("authenticated flows", () => {
  test.skip(true, "Requires seeded test user and running API with E2E_TEST_MODE");

  test("dashboard shows workspace after login", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("e2e@example.com");
    await page.getByLabel(/password/i).fill("Password1!");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/your workspace/i)).toBeVisible();
  });
});
