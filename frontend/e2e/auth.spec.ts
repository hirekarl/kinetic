import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Kinetic — Auth Flow', () => {
  test('shows login screen when no token in localStorage', async ({ page }) => {
    // No addInitScript — localStorage starts empty
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /^kinetic$/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /^sign in$/i })).toBeVisible();
  });

  test('successful login navigates to dashboard', async ({ page }) => {
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        json: { access_token: 'e2e-test-token', token_type: 'bearer', tenant: 'demo' },
      });
    });
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        json: { username: 'demo', tenant: 'demo', display_name: 'Demo' },
      });
    });
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: null, messages: [] } });
    });

    await page.goto('/login');
    await expect(page.getByLabel(/username/i)).toBeVisible();

    await page.getByLabel(/username/i).fill('demo');
    await page.getByLabel(/password/i).fill('demo_password');
    await page.getByRole('button', { name: /^sign in$/i }).click();

    await expect(page.getByRole('heading', { name: /mission control/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).not.toBeVisible();
  });

  test('invalid credentials shows error message', async ({ page }) => {
    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({ status: 401, json: { detail: 'Invalid credentials' } });
    });

    await page.goto('/login');
    await expect(page.getByLabel(/username/i)).toBeVisible();

    await page.getByLabel(/username/i).fill('demo');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /^sign in$/i }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByText(/invalid credentials/i)).toBeVisible();
    // Login screen still visible
    await expect(page.getByLabel(/username/i)).toBeVisible();
  });

  test('logout returns to login screen', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('kinetic_onboarded', 'true');
      localStorage.setItem('kinetic_token', 'e2e-test-token');
    });
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        json: { username: 'demo', tenant: 'demo', display_name: 'Demo' },
      });
    });
    await page.route('**/api/auth/logout', async (route) => {
      await route.fulfill({ json: { status: 'ok' } });
    });
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: null, messages: [] } });
    });

    await page.goto('/');
    await expect(page.getByRole('heading', { name: /mission control/i })).toBeVisible();

    await page.getByRole('button', { name: /sign out/i }).click();

    await expect(
      page.getByRole('heading', { name: /your infrastructure is showing/i })
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: /mission control/i })).not.toBeVisible();
  });

  test('login screen passes axe accessibility audit', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /^kinetic$/i })).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
