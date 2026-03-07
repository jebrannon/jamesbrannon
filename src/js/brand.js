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
  if (!brand) return;

  // Choose favicon variant based on user's colour-scheme preference
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const faviconUrl = prefersDark
    ? (brand.favicon_dark_url || brand.favicon_light_url)
    : (brand.favicon_light_url || brand.favicon_dark_url);

  if (!faviconUrl) return;

  // Upsert the <link rel="icon"> in <head>
  let link = document.querySelector('link[rel="icon"]');
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = faviconUrl;

  // Also set the apple-touch-icon to the 192px PNG variant if available
  const png192 = faviconUrl.replace(/\.svg$/, '-192.png');
  let apple = document.querySelector('link[rel="apple-touch-icon"]');
  if (!apple) {
    apple = document.createElement('link');
    apple.rel = 'apple-touch-icon';
    document.head.appendChild(apple);
  }
  apple.href = png192;
}
