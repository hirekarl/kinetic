import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Kinetic — Mission Control', () => {
  test('landing page passes axe accessibility audit', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('split panel layout renders chat and mission control', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /brief kinetic/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /mission control/i })).toBeVisible();
  });

  test('can perform a check-in and see dashboard updates', async ({ page }) => {
    // Mock the checkin API response
    await page.route('**/api/checkin', async (route) => {
      const json = {
        overall_status: 'yellow',
        bio: {
          status: 'yellow',
          burnout_score: 65,
          forecast: 'Moderate risk',
          sleep_debt_hours: 2.5,
          recommendations: ['Sleep more'],
        },
        logistics: {
          status: 'green',
          critical_tasks: [],
          outsourcing_suggestions: [],
          time_to_resolve_minutes: 0,
        },
        relational: null,
        triage_items: [
          {
            id: 'bio-001',
            priority: 6,
            domain: 'bio',
            description: 'Sleep debt accumulated',
            action: 'Hard stop at 11pm',
            completed: false,
          },
        ],
        roi_summary: {
          time_recovered_minutes: 0,
          margin_recovered: '0% reclaimed',
          burnout_risk_delta: -8.0,
        },
      };
      await route.fulfill({ json });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/what's your status/i);
    await input.fill('Slept 5 hours.');
    await page.getByRole('button', { name: /send/i }).click();

    // Verify loading state appears (briefly)
    await expect(page.getByRole('button', { name: /analyzing/i })).toBeVisible();

    // Verify dashboard updates
    await expect(page.getByText(/burnout score/i)).toBeVisible();
    await expect(page.getByText('65')).toBeVisible();
    await expect(page.getByText(/prioritized triage/i)).toBeVisible();
    await expect(page.getByText(/performance yield/i)).toBeVisible();
  });
});
