/**
 * Generates high-resolution brand assets for Kinetic.
 *
 * Usage:
 *   cd frontend && npm run brand
 *
 * For the landing page screenshot, start the dev server first:
 *   npm run dev   (in a separate terminal)
 *   npm run brand
 *
 * Override the dev server URL:
 *   LANDING_URL=http://localhost:5173 npm run brand
 */

import { chromium } from '@playwright/test';
import { mkdir } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dir, '..', '..', 'assets', 'brand');
const LANDING_URL = process.env.LANDING_URL ?? 'http://localhost:5173';

// ── Shared ───────────────────────────────────────────────────────────────────

const FONT = `
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
`;

const BASE_CSS = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #09090b;
    color: #fafafa;
    overflow: hidden;
  }
`;

/** Returns inline SVG markup for the Kinetic K-mark at the given pixel size. */
function kMark(size, filterId = 'g') {
  return `<svg width="${size}" height="${size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="20" fill="#09090b"/>
  <defs>
    <filter id="${filterId}" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <line x1="10" y1="8"  x2="20" y2="20" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="10" y1="32" x2="20" y2="20" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="31" y1="13" x2="20" y2="20" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="20" cy="20" r="2.5" fill="#10b981" filter="url(#${filterId})"/>
</svg>`;
}

// ── Templates ────────────────────────────────────────────────────────────────

/** Social card template — shared by og-card.png and twitter-card.png. */
function socialCardHtml(width, height) {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  ${FONT}
  <style>${BASE_CSS}</style>
</head>
<body style="width:${width}px;height:${height}px;position:relative;">

  <!-- Subtle grid texture -->
  <div style="
    position:absolute;inset:0;
    background-image:
      linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size:60px 60px;">
  </div>

  <!-- Emerald ambient glow (top-left) -->
  <div style="
    position:absolute;left:-120px;top:-200px;
    width:720px;height:720px;
    background:radial-gradient(circle, rgba(16,185,129,0.07) 0%, transparent 65%);
    pointer-events:none;">
  </div>

  <!-- Decorative oversized K-mark (top-right, very faint) -->
  <div style="position:absolute;right:-56px;top:-72px;opacity:0.055;pointer-events:none;">
    ${kMark(440, 'bg')}
  </div>

  <!-- Content -->
  <div style="
    position:relative;z-index:1;
    padding:56px 72px;height:100%;
    display:flex;flex-direction:column;justify-content:space-between;">

    <!-- Header row -->
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <div style="display:flex;align-items:center;gap:14px;">
        ${kMark(48, 'hd')}
        <span style="font-size:15px;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#fafafa;">
          KINETIC
        </span>
      </div>
      <div style="
        background:#18181b;border:1px solid #27272a;border-radius:6px;
        padding:8px 14px;display:flex;align-items:center;gap:9px;">
        <span style="
          width:7px;height:7px;border-radius:50%;background:#10b981;flex-shrink:0;
          box-shadow:0 0 7px rgba(16,185,129,0.8);">
        </span>
        <span style="
          font-family:'Courier New',monospace;font-size:11px;
          color:#a1a1aa;letter-spacing:0.12em;text-transform:uppercase;">
          System Active
        </span>
      </div>
    </div>

    <!-- Headline block -->
    <div>
      <p style="
        font-family:'Courier New',monospace;font-size:12px;color:#10b981;
        letter-spacing:0.18em;text-transform:uppercase;margin-bottom:20px;">
        [SYSTEM v1.8.0]
      </p>
      <h1 style="
        font-size:68px;font-weight:800;line-height:1.06;
        letter-spacing:-0.025em;color:#ffffff;">
        Your infrastructure<br>is showing.
      </h1>
      <p style="
        margin-top:24px;font-size:20px;color:#71717a;
        line-height:1.55;max-width:640px;">
        Monitors your biology, time, and relationships —<br>
        and surfaces what to act on, right now.
      </p>
    </div>

    <!-- Domain agent badges -->
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
      <div style="
        border:1px solid rgba(16,185,129,0.35);background:rgba(16,185,129,0.07);
        border-radius:6px;padding:9px 16px;display:flex;align-items:center;gap:8px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#10b981;flex-shrink:0;"></span>
        <span style="font-size:13px;color:#10b981;letter-spacing:0.04em;">Bio Archivist</span>
      </div>
      <div style="
        border:1px solid rgba(245,158,11,0.35);background:rgba(245,158,11,0.07);
        border-radius:6px;padding:9px 16px;display:flex;align-items:center;gap:8px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#f59e0b;flex-shrink:0;"></span>
        <span style="font-size:13px;color:#f59e0b;letter-spacing:0.04em;">Logistics Fixer</span>
      </div>
      <div style="
        border:1px solid rgba(96,165,250,0.35);background:rgba(96,165,250,0.07);
        border-radius:6px;padding:9px 16px;display:flex;align-items:center;gap:8px;">
        <span style="width:6px;height:6px;border-radius:50%;background:#60a5fa;flex-shrink:0;"></span>
        <span style="font-size:13px;color:#60a5fa;letter-spacing:0.04em;">Relational Diplomat</span>
      </div>
    </div>

  </div>
</body>
</html>`;
}

/** Square icon at any size — K-mark centered on zinc-950. */
function iconHtml(size) {
  const markSize = Math.round(size * 0.62);
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    ${BASE_CSS}
    body {
      width:${size}px;height:${size}px;
      display:flex;align-items:center;justify-content:center;
      position:relative;
    }
  </style>
</head>
<body>
  <!-- Subtle radial glow centred behind mark -->
  <div style="
    position:absolute;inset:0;
    background:radial-gradient(circle at 50% 50%, rgba(16,185,129,0.09) 0%, transparent 60%);
    pointer-events:none;">
  </div>
  <div style="position:relative;z-index:1;">
    ${kMark(markSize, 'ic')}
  </div>
</body>
</html>`;
}

/** Horizontal wordmark lockup — icon + name + tagline. */
function wordmarkHtml() {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  ${FONT}
  <style>
    ${BASE_CSS}
    body {
      width:900px;height:200px;
      display:flex;align-items:center;
      padding:0 56px;gap:28px;
    }
  </style>
</head>
<body>
  ${kMark(72, 'wm')}
  <div style="width:1px;height:60px;background:#27272a;flex-shrink:0;"></div>
  <div>
    <div style="
      font-size:28px;font-weight:700;
      letter-spacing:0.22em;text-transform:uppercase;
      color:#fafafa;">
      KINETIC
    </div>
    <div style="
      font-family:'Courier New',monospace;font-size:13px;
      color:#52525b;letter-spacing:0.06em;text-transform:uppercase;
      margin-top:8px;">
      Bio-Operational Triage Engine
    </div>
  </div>
</body>
</html>`;
}

// ── Asset manifest ────────────────────────────────────────────────────────────

const STANDALONE = [
  { file: 'og-card.png',      w: 1200, h: 630,  html: socialCardHtml(1200, 630)  },
  { file: 'twitter-card.png', w: 1200, h: 675,  html: socialCardHtml(1200, 675)  },
  { file: 'icon-512.png',     w: 512,  h: 512,  html: iconHtml(512)               },
  { file: 'icon-192.png',     w: 192,  h: 192,  html: iconHtml(192)               },
  { file: 'wordmark.png',     w: 900,  h: 200,  html: wordmarkHtml()              },
];

// ── Runner ────────────────────────────────────────────────────────────────────

async function main() {
  await mkdir(OUT, { recursive: true });

  const browser = await chromium.launch();
  console.log('\nGenerating Kinetic brand assets…\n');

  // Standalone templates — no dev server required
  for (const asset of STANDALONE) {
    const page = await browser.newPage({ viewport: { width: asset.w, height: asset.h } });
    await page.setContent(asset.html, { waitUntil: 'networkidle' });
    await page.screenshot({ path: join(OUT, asset.file), type: 'png' });
    await page.close();
    console.log(`  ✓  ${asset.file.padEnd(22)} ${asset.w}×${asset.h}`);
  }

  // Landing page — requires running dev server
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    await page.goto(`${LANDING_URL}/`, { waitUntil: 'networkidle', timeout: 12_000 });
    await page.waitForSelector('h1', { timeout: 8_000 });
    await page.screenshot({ path: join(OUT, 'landing-1920x1080.png'), type: 'png', fullPage: false });
    await page.close();
    console.log(`  ✓  ${'landing-1920x1080.png'.padEnd(22)} 1920×1080`);
  } catch {
    console.warn(`\n  ⚠  landing-1920x1080.png skipped`);
    console.warn(`     Start the dev server first, then re-run:`);
    console.warn(`       npm run dev   (separate terminal)`);
    console.warn(`       npm run brand`);
  }

  await browser.close();
  console.log(`\n  Assets written to  assets/brand/\n`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
