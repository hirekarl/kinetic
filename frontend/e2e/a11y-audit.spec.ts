import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Shared fixture — all three agents populated + behavioral profiles.
// Reused from app.spec.ts pattern so the axe test covers the same rich state.
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
  ],
  roi_summary: {
    time_recovered_minutes: 90,
    margin_recovered: '12% reclaimed',
    burnout_risk_delta: -5.0,
  },
  liaison_feedback: 'Focus on sleep first.',
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
  behavioral_summary: {
    bio_trend: {
      avg_sleep_hours: 6.1,
      sleep_slope: -0.32,
      avg_nutrition: 7.0,
      avg_energy: 6.0,
      worst_sleep_day: '2026-04-24',
      days_analyzed: 7,
      sleep_series: [7.5, 7.0, 6.5, 6.0, 5.5, 5.5, 5.0],
    },
    recurring_tasks: [],
    relational_drifts: [],
    days_analyzed: 7,
    generated_at: '2026-04-26T08:00:00',
  },
};

test.describe('Kinetic — Accessibility Final Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('kinetic_onboarded', 'true');
    });
  });

  test('keyboard navigation: all interactive elements reachable without mouse', async ({
    page,
  }) => {
    // Return null health so the idle state renders with suggested prompts visible.
    // The history fetch failure path is caught silently, so mocking a clean
    // empty response is more predictable.
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: null, messages: [] } });
    });

    await page.goto('/');
    // Wait for the idle state to confirm history fetch settled
    await expect(page.getByText(/system idle/i)).toBeVisible();

    // DOM tab order with empty textarea (Send is disabled → not focusable):
    //   1. Suggested prompt 1  (ChatPanel scroll region, first in DOM)
    //   2. Suggested prompt 2
    //   3. Suggested prompt 3
    //   4. textarea            (ChatPanel input area)
    //   5. Reset System button (right-panel header)
    //   6. Scrollable content  (main > div[tabIndex=0])

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /slept 5 hours/i })).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(
      page.getByRole('button', { name: /i need help breaking down my triage list/i })
    ).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /marcus vibe check/i })).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByPlaceholder(/what's your status/i)).toBeFocused();

    // Send is disabled when textarea is empty — browser skips disabled buttons.
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /reset system/i })).toBeFocused();

    await page.keyboard.press('Tab');
    // The scrollable content region has tabIndex=0 — it must receive focus
    await expect(page.locator('[tabindex="0"]')).toBeFocused();
  });

  test('axe audit with BehavioralProfilePanel expanded passes WCAG 2.1 AA', async ({ page }) => {
    // Pre-populate via history so we get the full dashboard including the profile panel.
    await page.route('**/api/history', async (route) => {
      await route.fulfill({ json: { health: FULL_HEALTH_RESPONSE, messages: [] } });
    });

    await page.goto('/');
    await expect(page.getByText(/sector status/i)).toBeVisible();

    // Expand the behavioral profile panel — this reveals the "Last updated" text
    // whose contrast was previously failing (text-zinc-500 = 4.12:1 < 4.5:1).
    const trigger = page.getByRole('button', { name: /behavioral profile/i });
    await trigger.click();
    await expect(trigger).toHaveAttribute('aria-expanded', 'true');
    await expect(
      page.getByText('Sleep consistently falls below 6 hours on weekdays.')
    ).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    expect(results.violations).toEqual([]);
  });
});
