import { escapeHtml } from './utils.js';

const BASE = import.meta.env?.VITE_API_BASE ?? '';

/**
 * Fetch brand settings and render the footer.
 * Called once on init; safe to call again if needed.
 */
export async function initFooter() {
  const el = document.getElementById('Footer');
  if (!el) return;
  try {
    const res = await fetch(`${BASE}/api/settings/brand`);
    if (res.ok) {
      const brand = await res.json();
      renderFooter(el, brand);
    }
  } catch (e) {
    console.warn('[footer] Failed to load brand settings:', e);
  }
}

/**
 * Render contact links into a footer element from brand settings.
 * @param {HTMLElement} el
 * @param {object} brand
 */
export function renderFooter(el, brand = {}) {
  const links = [];

  if (brand.linkedin) {
    const text = escapeHtml(brand.linkedin_text || 'LinkedIn');
    const href = escapeHtml(brand.linkedin);
    links.push(`<a href="${href}" class="footer__link footer__link--linkedin" target="_blank" rel="noopener noreferrer">${text}</a>`);
  }

  if (brand.instagram) {
    const text = escapeHtml(brand.instagram_text || 'Instagram');
    const href = escapeHtml(brand.instagram);
    links.push(`<a href="${href}" class="footer__link footer__link--instagram" target="_blank" rel="noopener noreferrer">${text}</a>`);
  }

  if (brand.email) {
    const text = escapeHtml(brand.email_text || brand.email);
    const addr = escapeHtml(brand.email);
    links.push(`<a href="mailto:${addr}" class="footer__link footer__link--email">${text}</a>`);
  }

  const nav = links.length
    ? `<nav class="footer__nav" aria-label="Contact links">${links.join('')}</nav>`
    : '';
  const year = new Date().getFullYear();
  el.innerHTML = `${nav}<p class="footer__copyright">&copy; ${year} James Brannon</p>`;
}

/**
 * Smoothly scroll the Footer element into view.
 * Used by the /contact route.
 */
export function scrollToFooter() {
  const el = document.getElementById('Footer');
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}
