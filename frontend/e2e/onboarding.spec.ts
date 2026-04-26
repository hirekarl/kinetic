import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Each test gets a fresh browser context (Playwright default), so localStorage
// starts empty — the onboarding modal shows on first visit without any setup.

test.describe('Kinetic — Onboarding', () => {
  test('shows modal on first visit with "Personal Infrastructure" as step 0', async ({ page }) => {
    await page.goto('/');
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(page.getByRole('heading', { name: /personal infrastructure/i })).toBeVisible();
  });

  test('step navigation: Next → Next → Done closes the modal', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('dialog')).toBeVisible();

    // Step 0 → 1
    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByRole('heading', { name: /chat-first/i })).toBeVisible();

    // Step 1 → 2
    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByRole('heading', { name: /your agent team/i })).toBeVisible();

    // Done closes
    await page.getByRole('button', { name: /done/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('Skip from step 1 dismisses the modal', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /skip/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('after Skip, localStorage flag is set and reload does not re-show modal', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.getByRole('button', { name: /skip/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Verify flag was persisted
    const flag = await page.evaluate(() => localStorage.getItem('kinetic_onboarded'));
    expect(flag).toBe('true');

    // Reload — modal must NOT reappear
    await page.reload();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('Back button returns to previous step', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByRole('heading', { name: /your agent team/i })).toBeVisible();

    await page.getByRole('button', { name: /back/i }).click();
    await expect(page.getByRole('heading', { name: /chat-first/i })).toBeVisible();
  });

  test('step 2 shows all three agent names', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /next/i }).click();
    await page.getByRole('button', { name: /next/i }).click();
    await expect(page.getByText(/bio-metric archivist/i)).toBeVisible();
    await expect(page.getByText(/logistics fixer/i)).toBeVisible();
    await expect(page.getByText(/relational diplomat/i)).toBeVisible();
  });

  test('onboarding modal passes axe accessibility audit', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('dialog')).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
