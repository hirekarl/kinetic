import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Full mock representing all three agents populated — used by multiple tests
const FULL_HEALTH_RESPONSE = {
  overall_status: 'yellow',
  bio: {
    status: 'yellow',
    burnout_score: 62,
    forecast: 'Sleep deficit increasing — performance drop risk within 48 hours.',
    sleep_debt_hours: 3,
    recommendations: ['Hard stop at 11pm tonight', 'No caffeine after 2pm'],
    error_message: null,
  },
  logistics: {
    status: 'yellow',
    critical_tasks: ['laundry'],
    tasks_with_steps: [],
    outsourcing_suggestions: ['Consider a laundry service this week.'],
    time_to_resolve_minutes: 90,
    error_message: null,
  },
  relational: {
    status: 'yellow',
    connection_margin_score: 60,
    at_risk_relationships: ['Marcus'],
    interaction_sprints: ['Send Marcus a brief check-in message today.'],
    error_message: null,
  },
  triage_items: [
    {
      id: 'bio-001',
      priority: 6,
      domain: 'bio',
      description: 'Sleep debt accumulating',
      action: 'Hard stop at 11pm',
      snooze_until: null,
      completed: false,
    },
    {
      id: 'logistics-001',
      priority: 6,
      domain: 'logistics',
      description: 'Laundry overdue 3 days',
      action: 'Batch or outsource',
      snooze_until: null,
      completed: false,
    },
    {
      id: 'relational-001',
      priority: 6,
      domain: 'relational',
      description: 'Marcus: contact drift detected',
      action: 'Send a brief check-in',
      snooze_until: null,
      completed: false,
    },
  ],
  roi_summary: {
    time_recovered_minutes: 90,
    margin_recovered: '12% reclaimed',
    burnout_risk_delta: -5.0,
  },
  liaison_feedback: 'Focus on sleep first — everything else compounds from there.',
  behavioral_profiles: [
    {
      profile_key: 'chronic_sleep_deficit',
      insight: 'Sleep consistently falls below 6 hours on weekdays.',
      evidence: { avg_weekday_sleep: 5.4 },
      first_observed: '2026-04-20T08:00:00',
      last_updated: '2026-04-25T08:00:00',
      observation_count: 5,
    },
  ],
};

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
    await expect(page.getByRole('heading', { name: /operational liaison/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /mission control/i })).toBeVisible();
  });

  test('can perform a check-in and see dashboard updates', async ({ page }) => {
    await page.route('**/api/checkin', async (route) => {
      // Small delay so the "Analyzing..." loading state is visible before mock resolves
      await new Promise((resolve) => setTimeout(resolve, 150));
      const json = {
        overall_status: 'yellow',
        bio: {
          status: 'yellow',
          burnout_score: 65,
          forecast: 'Moderate risk',
          sleep_debt_hours: 2.5,
          recommendations: ['Sleep more'],
          error_message: null,
        },
        logistics: {
          status: 'green',
          critical_tasks: [],
          tasks_with_steps: [],
          outsourcing_suggestions: [],
          time_to_resolve_minutes: 0,
          error_message: null,
        },
        relational: null,
        triage_items: [
          {
            id: 'bio-001',
            priority: 6,
            domain: 'bio',
            description: 'Sleep debt accumulated',
            action: 'Hard stop at 11pm',
            snooze_until: null,
            completed: false,
          },
        ],
        roi_summary: {
          time_recovered_minutes: 0,
          margin_recovered: '0% reclaimed',
          burnout_risk_delta: -8.0,
        },
        liaison_feedback: null,
        behavioral_profiles: [],
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
    await expect(page.getByText('Burnout Score', { exact: true })).toBeVisible();
    await expect(page.getByText('65')).toBeVisible();
    await expect(page.getByText(/prioritized triage/i)).toBeVisible();
    await expect(page.getByText(/performance yield/i)).toBeVisible();
  });

  test('full check-in populates all three sector cards and triage list', async ({ page }) => {
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: null, messages: [] } });
    });
    await page.route('**/api/checkin', async (route) => {
      await route.fulfill({ json: FULL_HEALTH_RESPONSE });
    });

    await page.goto('/');
    const input = page.getByPlaceholder(/what's your status/i);
    await input.fill('Slept 5 hours, ate okay, feeling disconnected from Marcus.');
    await page.getByRole('button', { name: /send/i }).click();

    // Wait for the populated dashboard
    await expect(page.getByText(/sector status/i)).toBeVisible();

    // All three agent cards must be visible with data
    await expect(page.getByText('Bio-Metric Archivist').first()).toBeVisible();
    await expect(page.getByText('Logistics Fixer').first()).toBeVisible();
    await expect(page.getByText('Relational Diplomat').first()).toBeVisible();

    // Triage list shows all three items
    await expect(page.getByText('3 items pending')).toBeVisible();
    await expect(page.getByText('Sleep debt accumulating')).toBeVisible();
    await expect(page.getByText('Laundry overdue 3 days')).toBeVisible();
    await expect(page.getByText('Marcus: contact drift detected')).toBeVisible();
  });

  test('behavioral profile panel is collapsed by default', async ({ page }) => {
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: FULL_HEALTH_RESPONSE, messages: [] } });
    });

    await page.goto('/');
    await expect(page.getByText(/sector status/i)).toBeVisible();

    const trigger = page.getByRole('button', { name: /behavioral profile/i });
    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await expect(
      page.getByText('Sleep consistently falls below 6 hours on weekdays.')
    ).not.toBeVisible();
  });

  test('behavioral profile panel expands on click and shows insights', async ({ page }) => {
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: FULL_HEALTH_RESPONSE, messages: [] } });
    });

    await page.goto('/');
    await expect(page.getByText(/sector status/i)).toBeVisible();

    const trigger = page.getByRole('button', { name: /behavioral profile/i });
    await trigger.click();

    await expect(trigger).toHaveAttribute('aria-expanded', 'true');
    await expect(
      page.getByText('Sleep consistently falls below 6 hours on weekdays.')
    ).toBeVisible();
    await expect(page.getByText('chronic_sleep_deficit')).toBeVisible();
    await expect(page.getByText('5 observations')).toBeVisible();
  });

  test('populated dashboard state passes axe accessibility audit', async ({ page }) => {
    // Pre-populate via the history endpoint so we can audit without interaction
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: FULL_HEALTH_RESPONSE, messages: [] } });
    });

    await page.goto('/');
    // Wait for the populated dashboard to fully render
    await expect(page.getByText(/sector status/i)).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
