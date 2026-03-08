/**
 * Shared utilities for router.js and blog-feed.js.
 */

/**
 * Escape a string for safe insertion into HTML.
 * Use for all user/CMS-supplied text that isn't intended to be rendered as HTML.
 */
export function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Format an ISO 8601 date string for display.
 */
export function formatDate(iso) {
  const d = new Date(iso);
  if (!iso || isNaN(d.getTime())) return String(iso ?? '');
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}
