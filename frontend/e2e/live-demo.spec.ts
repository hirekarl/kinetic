import { test, expect } from '@playwright/test';

// ── Scenario fixtures ───────────────────────────────────────────────────────

const INITIAL_HISTORY_RESPONSE = {
  overall_status: 'yellow',
  bio: {
    status: 'yellow',
    burnout_score: 55,
    forecast:
      'Mild sleep debt accumulating. Jordan has averaged only 5.4h of sleep over the last 5 weekdays.',
    sleep_debt_hours: 2.5,
    recommendations: ['Prioritize 7h sleep tonight'],
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
  relational: {
    status: 'yellow',
    connection_margin_score: 70,
    at_risk_relationships: ['Marcus'],
    interaction_sprints: ['Send Marcus a quick text'],
    error_message: null,
  },
  triage_items: [],
  roi_summary: {
    time_recovered_minutes: 0,
    margin_recovered: '0% reclaimed',
    burnout_risk_delta: 0,
  },
  liaison_feedback: 'System in mild drift. Bio and Relational sectors require attention.',
  active_pauses: [],
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
      burnout_series: [40, 45, 50, 55, 60, 55, 55],
    },
    recurring_tasks: [],
    relational_drifts: [],
    days_analyzed: 7,
    generated_at: new Date().toISOString(),
  },
  responding_agent: null,
};

const CRISIS_HEALTH_RESPONSE = {
  ...INITIAL_HISTORY_RESPONSE,
  overall_status: 'red',
  bio: {
    ...INITIAL_HISTORY_RESPONSE.bio,
    status: 'red',
    burnout_score: 82,
    forecast: "CRITICAL: High burnout risk. Jordan's sleep debt has peaked at 4.5 hours.",
    sleep_debt_hours: 4.5,
    recommendations: ['Immediate work stop', '9h sleep recovery protocol', 'No screens after 9pm'],
  },
  logistics: {
    status: 'red',
    critical_tasks: ['Laundry'],
    tasks_with_steps: [
      {
        name: 'Laundry Protocol',
        status: 'pending',
        subtasks: [
          'Sort by fabric/color',
          'Main wash (warm)',
          'Tumble dry (low)',
          'Fold & stage for tomorrow',
        ],
        completed_subtasks: [],
        priority: 'high',
        days_overdue: 6,
        notes: null,
      },
    ],
    outsourcing_suggestions: ['Outsource laundry to "Wash-N-Fold" for 90min time reclamation.'],
    time_to_resolve_minutes: 120,
    error_message: null,
  },
  relational: {
    status: 'red',
    connection_margin_score: 35,
    at_risk_relationships: ['Marcus'],
    interaction_sprints: ['Marcus: 5-min voice memo to arrest drift.'],
    error_message: null,
  },
  triage_items: [
    {
      id: 'bio-recovery',
      priority: 9,
      domain: 'bio',
      description: 'Critical Sleep Deficit',
      action: '9h Sleep Recovery Protocol',
      completed: false,
      source_id: null,
      snooze_until: null,
    },
    {
      id: 'relational-marcus',
      priority: 8,
      domain: 'relational',
      description: 'Marcus: Critical Drift',
      action: '5-min Voice Memo',
      completed: false,
      source_id: null,
      snooze_until: null,
    },
    {
      id: 'logistics-laundry',
      priority: 7,
      domain: 'logistics',
      description: 'Laundry Overdue (6 Days)',
      action: 'Outsource to Wash-N-Fold',
      completed: false,
      source_id: 'Laundry Protocol',
      snooze_until: null,
    },
  ],
  roi_summary: {
    time_recovered_minutes: 120,
    margin_recovered: '18% reclaimed',
    burnout_risk_delta: -15.5,
  },
  liaison_feedback: 'Jordan, data is red across all sectors. Activating cross-domain triage.',
  responding_agent: 'operational_liaison',
};

const STREAM_DONE_PAYLOAD = {
  responding_agent: 'liaison',
  contact_pauses: [],
  task_completions: [],
  active_pauses: [],
  behavioral_profiles: INITIAL_HISTORY_RESPONSE.behavioral_profiles,
  behavioral_summary: INITIAL_HISTORY_RESPONSE.behavioral_summary,
};

const RECOVERY_HEALTH_RESPONSE = {
  ...CRISIS_HEALTH_RESPONSE,
  overall_status: 'yellow',
  logistics: {
    ...CRISIS_HEALTH_RESPONSE.logistics,
    status: 'green',
    critical_tasks: [],
    tasks_with_steps: [],
    outsourcing_suggestions: [],
    time_to_resolve_minutes: 0,
  },
  triage_items: CRISIS_HEALTH_RESPONSE.triage_items.filter(
    (i) => i.source_id !== 'Laundry Protocol'
  ),
  roi_summary: {
    time_recovered_minutes: 120,
    margin_recovered: '22% reclaimed',
    burnout_risk_delta: -18.0,
  },
  liaison_feedback: 'Logistics sector stabilized. Focus now on Bio and Relational recovery.',
};

// ── SSE + timing helpers ─────────────────────────────────────────────────────

function createSSE(event: string, data: unknown) {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

// Simulates Gemini processing latency so the loading indicator is visible.
const simulatedDelay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

// ── Visual helpers (cursor overlay + smooth scroll for recording) ───────────

async function installMouseHelper(page: { addInitScript: (fn: () => void) => Promise<void> }) {
  await page.addInitScript(() => {
    const box = document.createElement('playwright-mouse-pointer');
    const styleEl = document.createElement('style');
    styleEl.innerHTML = `
      playwright-mouse-pointer {
        pointer-events: none; position: absolute; top: 0; left: 0; z-index: 10000;
        width: 20px; height: 20px; background: rgba(16,185,129,0.35);
        border: 2px solid rgba(255,255,255,0.9); border-radius: 50%;
        margin: -10px 0 0 -10px; transition: background 0.15s, transform 0.15s;
        box-shadow: 0 0 8px rgba(0,0,0,0.4);
      }
      playwright-mouse-pointer.down { background: rgba(245,158,11,0.75); transform: scale(0.82); }
    `;
    document.head.appendChild(styleEl);
    document.body.appendChild(box);
    document.addEventListener(
      'mousemove',
      (e) => {
        box.style.left = e.pageX + 'px';
        box.style.top = e.pageY + 'px';
      },
      true
    );
    document.addEventListener('mousedown', () => box.classList.add('down'), true);
    document.addEventListener('mouseup', () => box.classList.remove('down'), true);
  });
}

async function smoothScroll(
  page: {
    evaluate: (
      fn: (args: { target: number; duration: number }) => Promise<void>,
      args: { target: number; duration: number }
    ) => Promise<void>;
  },
  targetScrollTop: number,
  durationMs: number
) {
  await page.evaluate(
    async ({ target, duration }) => {
      const el = document.querySelector('[tabindex="0"]');
      if (!el) return;
      const start = el.scrollTop;
      const dist = target - start;
      const t0 = performance.now();
      const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
      await new Promise<void>((res) => {
        const step = (now: number) => {
          const p = Math.min((now - t0) / duration, 1);
          el.scrollTop = start + dist * ease(p);
          p < 1 ? requestAnimationFrame(step) : res();
        };
        requestAnimationFrame(step);
      });
    },
    { target: targetScrollTop, duration: durationMs }
  );
}

async function smoothScrollToElement(
  page: Parameters<typeof smoothScroll>[0] & {
    evaluate: (fn: () => number) => Promise<number>;
  },
  locator: { first: () => { boundingBox: () => Promise<{ y: number } | null> } },
  durationMs: number
) {
  const box = await locator.first().boundingBox();
  if (!box) return;
  const scrollableTop = await page.evaluate(
    () => document.querySelector('[tabindex="0"]')?.getBoundingClientRect().top ?? 0
  );
  const currentScroll = await page.evaluate(
    () => document.querySelector('[tabindex="0"]')?.scrollTop ?? 0
  );
  const target = currentScroll + (box.y - scrollableTop) - 120;
  await smoothScroll(page, Math.max(0, target), durationMs);
}

async function scrollToTop(page: Parameters<typeof smoothScroll>[0], durationMs = 1000) {
  await smoothScroll(page, 0, durationMs);
}

async function hoverAndClick(
  page: {
    mouse: {
      move: (x: number, y: number, opts?: { steps: number }) => Promise<void>;
      down: () => Promise<void>;
      up: () => Promise<void>;
    };
    waitForTimeout: (ms: number) => Promise<void>;
  },
  locator: {
    first: () => {
      boundingBox: () => Promise<{
        x: number;
        y: number;
        width: number;
        height: number;
      } | null>;
      click: () => Promise<void>;
    };
  }
) {
  const box = await locator.first().boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 18 });
    await page.waitForTimeout(500);
    await page.mouse.down();
    await page.waitForTimeout(80);
    await page.mouse.up();
    await page.waitForTimeout(400);
  } else {
    await locator.first().click();
  }
}

// ── Demo test ───────────────────────────────────────────────────────────────

test('Kinetic Comprehensive MVP Demo', async ({ page }) => {
  await installMouseHelper(page);

  // ── 1. Global API mocks ─────────────────────────────────────────────────

  // Login: intentionally fails on wrong password, succeeds otherwise
  await page.context().route('**/api/auth/login', async (route) => {
    const body = (await route.request().postDataJSON()) as { password: string };
    await new Promise((r) => setTimeout(r, 500));
    if (body.password === 'wrongpassword') {
      await route.fulfill({ status: 401, json: { detail: 'Invalid credentials.' } });
    } else {
      await route.fulfill({ json: { access_token: 'demo-token', tenant: 'demo' } });
    }
  });
  await page.context().route('**/api/auth/me', async (route) => {
    await route.fulfill({ json: { username: 'demo', tenant: 'demo', display_name: 'Jordan' } });
  });
  await page.context().route('**/api/history', async (route) => {
    await route.fulfill({ json: { health: null, messages: [] } });
  });
  await page.context().route('**/api/demo/simulate', async (route) => {
    await simulatedDelay(1800); // simulate historical data insertion
    await route.fulfill({ json: { inserted: 5 } });
  });
  await page.context().route('**/api/digest', async (route) => {
    await route.fulfill({
      json: {
        summary:
          "Jordan's week shows a steady decline in sleep (baseline 7.5h → 5.0h) while relational drift with Marcus has doubled. Logistics backlogs are beginning to peak. Recommend prioritising sleep recovery and a brief reconnection sprint this week.",
        generated_at: new Date().toISOString(),
      },
    });
  });
  // Task completion endpoint — always returns 200
  await page.context().route('**/api/tasks/**/complete', async (route) => {
    await route.fulfill({ status: 200, json: {} });
  });

  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  // ── 2. Login error → recovery (demonstrates T-4 error handling) ─────────

  await page.getByLabel(/username/i).fill('demo');
  await page.getByLabel(/password/i).fill('wrongpassword');
  await page.waitForTimeout(800);
  await hoverAndClick(page, page.getByRole('button', { name: /sign in/i }));
  await expect(page.getByRole('alert')).toBeVisible({ timeout: 6000 });
  await page.waitForTimeout(2500);

  // Correct the password and succeed
  await page.getByLabel(/password/i).fill('demo');
  await page.waitForTimeout(600);
  await hoverAndClick(page, page.getByRole('button', { name: /sign in/i }));

  // ── 3. Onboarding ───────────────────────────────────────────────────────

  await expect(page.getByRole('heading', { name: 'Personal Infrastructure' })).toBeVisible({
    timeout: 10000,
  });
  await page.waitForTimeout(4000);
  await hoverAndClick(page, page.getByRole('button', { name: /next/i }));
  await page.waitForTimeout(4000);
  await hoverAndClick(page, page.getByRole('button', { name: /next/i }));
  await page.waitForTimeout(4000);
  await hoverAndClick(page, page.getByRole('button', { name: /done/i }));
  await page.waitForTimeout(1000);

  // ── 4. Simulate a week of history ───────────────────────────────────────

  // Update history mock so the dashboard populates after simulate
  await page.context().route('**/api/history', async (route) => {
    await route.fulfill({ json: { health: INITIAL_HISTORY_RESPONSE, messages: [] } });
  });

  await hoverAndClick(page, page.getByRole('button', { name: /simulate week/i }));
  await page.waitForTimeout(2000);
  await scrollToTop(page);
  await page.waitForTimeout(1000);

  // Show Behavioral Profile → pattern detection in action
  const profileTrigger = page.getByRole('button', { name: /behavioral profile/i });
  await smoothScrollToElement(page, profileTrigger, 1200);
  await page.waitForTimeout(600);
  await hoverAndClick(page, profileTrigger);
  await page.waitForTimeout(5000);
  await hoverAndClick(page, profileTrigger); // collapse before scrolling on

  // Show Weekly Digest → AI-synthesised prose summary
  const digestTrigger = page.getByRole('button', { name: /weekly review/i });
  await smoothScrollToElement(page, digestTrigger, 1200);
  await page.waitForTimeout(600);
  await hoverAndClick(page, digestTrigger);
  await page.waitForTimeout(4000);
  await hoverAndClick(page, digestTrigger); // collapse

  // ── 5. Turn 1 — The Crisis Check-in ────────────────────────────────────

  await page.route('**/api/checkin/stream', async (route) => {
    await simulatedDelay(3200); // parser + three-agent orchestration + liaison stream
    const sse =
      createSSE('agents', CRISIS_HEALTH_RESPONSE) +
      createSSE('token', {
        text: 'Jordan, the data is unambiguous — activating cross-domain triage. ',
      }) +
      createSSE('token', {
        text: 'Bio-Metric Archivist confirms CRITICAL status: 4.5h sleep debt requires 9h recovery tonight. ',
      }) +
      createSSE('token', {
        text: 'Logistics Fixer has broken the laundry backlog into steps and flagged outsourcing as highest ROI.',
      }) +
      createSSE('done', STREAM_DONE_PAYLOAD);
    await route.fulfill({ status: 200, contentType: 'text/event-stream', body: sse });
  });

  await scrollToTop(page, 1200);
  const chatInput = page.getByPlaceholder(/what's your status/i);
  await chatInput.click();

  // Hover over the disabled Send button with an empty input — shows T-4 empty-input guard
  const sendBtn = page.getByRole('button', { name: /^send$/i });
  const sendBox = await sendBtn.first().boundingBox();
  if (sendBox) {
    await page.mouse.move(sendBox.x + sendBox.width / 2, sendBox.y + sendBox.height / 2, {
      steps: 15,
    });
  }
  await page.waitForTimeout(1600);

  await page.keyboard.type(
    "I'm completely overwhelmed. Four hours sleep, laundry six days overdue, haven't talked to Marcus in weeks.",
    { delay: 42 }
  );
  await page.waitForTimeout(900);
  await chatInput.press('Enter');

  // Verify crisis dashboard populates; hover bio card so viewer sees forecast + charts
  await expect(page.getByText('CRITICAL: High burnout risk')).toBeVisible({ timeout: 20000 });
  const forecastEl = page.getByText('CRITICAL: High burnout risk');
  const forecastBox = await forecastEl.first().boundingBox();
  if (forecastBox) {
    await page.mouse.move(
      forecastBox.x + forecastBox.width / 2,
      forecastBox.y + forecastBox.height / 2,
      { steps: 15 }
    );
  }
  await page.waitForTimeout(4000);

  // Scroll to logistics card — show subtask breakdown
  await smoothScrollToElement(
    page,
    page.getByRole('heading', { name: /logistics fixer/i }).first(),
    1200
  );
  await expect(page.getByText('Laundry Protocol')).toBeVisible();
  await page.waitForTimeout(4500);

  // ── 6. Turn 2 — Multi-turn: ROI follow-up ──────────────────────────────

  await page.route('**/api/checkin/stream', async (route) => {
    await simulatedDelay(2400); // follow-up with conversation context is faster
    const sse =
      createSSE('agents', CRISIS_HEALTH_RESPONSE) +
      createSSE('token', {
        text: 'Outsourcing laundry to a local "Wash-N-Fold" service reclaims 120 minutes of focus time this week. ',
      }) +
      createSSE('token', {
        text: 'Combined with the sleep protocol, this projects a 15.5-point burnout reduction.',
      }) +
      createSSE('done', STREAM_DONE_PAYLOAD);
    await route.fulfill({ status: 200, contentType: 'text/event-stream', body: sse });
  });

  await scrollToTop(page, 1200);
  await chatInput.click();
  await chatInput.fill('How much time do I save if I outsource the laundry?');
  await page.waitForTimeout(800);
  await chatInput.press('Enter');
  await expect(page.getByText('reclaims 120 minutes')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(4000);

  // ── 7. Task check-off — live dashboard update ───────────────────────────

  // Prime history mock with post-completion state BEFORE clicking the checkbox
  await page.context().route('**/api/history', async (route) => {
    await route.fulfill({ json: { health: RECOVERY_HEALTH_RESPONSE, messages: [] } });
  });

  const triageHeader = page.getByRole('heading', { name: /prioritized triage/i });
  await smoothScrollToElement(page, triageHeader, 1200);
  await page.waitForTimeout(2000);

  const laundryCheckbox = page.getByLabel(/Mark Laundry Protocol complete/i);
  await expect(laundryCheckbox).toBeVisible({ timeout: 5000 });
  await hoverAndClick(page, laundryCheckbox);
  await page.waitForTimeout(3000);

  // ── 8. Turn 3 — Recovery confirmation ──────────────────────────────────

  await page.route('**/api/checkin/stream', async (route) => {
    await simulatedDelay(2200);
    const sse =
      createSSE('agents', RECOVERY_HEALTH_RESPONSE) +
      createSSE('token', {
        text: 'Logistics sector stabilised. ROI confirmed: 120 minutes reclaimed. ',
      }) +
      createSSE('token', {
        text: "You're back in the Yellow zone, Jordan. Focus now shifts to sleep recovery.",
      }) +
      createSSE('done', STREAM_DONE_PAYLOAD);
    await route.fulfill({ status: 200, contentType: 'text/event-stream', body: sse });
  });

  await scrollToTop(page, 1200);
  await chatInput.click();
  await chatInput.fill("I've outsourced the laundry. What's my status now?");
  await chatInput.press('Enter');
  await expect(page.getByText('22% reclaimed')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(3500);

  // ── 9. Error resilience — 503 failure + retry (T-4 + Advanced tier) ────
  //
  // Both the SSE stream endpoint AND the non-streaming fallback (/api/checkin)
  // are mocked to 503 so the client's _fallback() path also fails and the
  // error banner is rendered. Routes are registered BEFORE the message fires.

  await page.route('**/api/checkin/stream', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Analysis engine temporarily unavailable.' }),
    });
  });
  await page.route('**/api/checkin', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Analysis engine temporarily unavailable.' }),
    });
  });

  await scrollToTop(page, 1000);
  await chatInput.click();
  await chatInput.fill('Can you give me a read on my sleep trajectory?');
  await page.waitForTimeout(800);
  await chatInput.press('Enter');

  // Verify error banner with meaningful message (never a raw stack trace)
  await expect(page.getByRole('alert')).toBeVisible({ timeout: 12000 });
  await expect(page.getByText('Analysis unavailable')).toBeVisible();
  await page.waitForTimeout(3000);

  // Register recovery routes, then click Retry — app recovers without reload
  await page.route('**/api/checkin/stream', async (route) => {
    await simulatedDelay(1600); // reconnect feels faster than a cold start
    const sse =
      createSSE('agents', RECOVERY_HEALTH_RESPONSE) +
      createSSE('token', {
        text: 'Connection restored. Analysis engine back online. Jordan, your recovery trajectory is holding.',
      }) +
      createSSE('done', STREAM_DONE_PAYLOAD);
    await route.fulfill({ status: 200, contentType: 'text/event-stream', body: sse });
  });

  await hoverAndClick(page, page.getByRole('button', { name: /retry/i }));
  await expect(page.getByRole('alert')).not.toBeVisible({ timeout: 10000 });
  await expect(page.getByText('recovery trajectory is holding')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(4500);

  // ── 10. Agent Dispatch Log — AI routing history ─────────────────────────

  const logTrigger = page.getByRole('button', { name: /agent dispatch log/i });
  await expect(logTrigger).toBeVisible({ timeout: 10000 });
  await logTrigger.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);
  await hoverAndClick(page, logTrigger);

  // Wait for the collapsible panel to open and the entry list to render
  const checkInHistory = page.getByRole('list', { name: /check-in history/i });
  await expect(checkInHistory).toBeVisible({ timeout: 8000 });
  await page.waitForTimeout(1000);

  const firstLogEntry = checkInHistory.locator('button').first();
  await expect(firstLogEntry).toBeVisible({ timeout: 5000 });
  await hoverAndClick(page, firstLogEntry);
  await smoothScroll(page, 5000, 1500);
  await page.waitForTimeout(8000);

  // ── 11. Mobile responsive proof (T-5) ──────────────────────────────────────
  // Briefly resize to an iPhone-class viewport to show the responsive stacked layout,
  // then restore desktop before the final scroll.

  await scrollToTop(page, 800);
  await page.waitForTimeout(500);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(3500); // let viewer see chat panel on top, dashboard below
  await smoothScroll(page, 900, 2500); // scroll down to reveal stacked sector cards
  await page.waitForTimeout(3000);
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.waitForTimeout(800);

  // ── 12. Final credits scroll ────────────────────────────────────────────

  await scrollToTop(page, 1500);
  await smoothScroll(page, 5000, 9000);
  await page.waitForTimeout(3000);
});
