import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Kinetic — shell accessibility', () => {
  test('landing page passes axe accessibility audit', async ({ page }) => {
    await page.goto('/');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test('split panel layout renders both panels', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('region', { name: 'Chat panel' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Dashboard panel' })).toBeVisible();
  });

  test('page title is correct', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Kinetic/);
  });
});
