/**
 * brandContext — loads site-wide brand settings from /api/settings/brand
 * and applies favicons. Call loadBrand() once on init; getBrand() anywhere.
 */

const BASE = import.meta.env?.VITE_API_BASE ?? '';

let _brand = null;

/**
 * Fetch brand settings from the CMS and apply favicons.
 * Called once on DOMContentLoaded; safe to call again if needed.
 */
export async function loadBrand() {
  try {
    const res = await fetch(`${BASE}/api/settings/brand`);
    if (res.ok) {
      _brand = await res.json();
      _applyFavicons(_brand);
    }
  } catch (e) {
    console.warn('[brand] Failed to load brand settings:', e);
  }
}

/**
 * Return the cached brand settings object, or an empty object if not loaded.
 */
export function getBrand() {
  return _brand || {};
}

// ── Internal helpers ───────────────────────────────────────────────────────────

function _applyFavicons(brand) {
  if (!brand?.favicon_url) return;

  // Upsert <link rel="icon"> — the SVG handles light/dark via its own @media rule
  let link = document.querySelector('link[rel="icon"]');
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = brand.favicon_url;

  // Set apple-touch-icon to the 192px PNG variant (generated server-side from the SVG)
  const png192 = brand.favicon_url.replace(/\.svg$/, '-192.png');
  let apple = document.querySelector('link[rel="apple-touch-icon"]');
  if (!apple) {
    apple = document.createElement('link');
    apple.rel = 'apple-touch-icon';
    document.head.appendChild(apple);
  }
  apple.href = png192;
}
