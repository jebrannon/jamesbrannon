import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderFooter, scrollToFooter, initFooter } from '../js/footer.js';

global.fetch = vi.fn();

// ── renderFooter ──────────────────────────────────────────────────────────────

describe('renderFooter', () => {
  let el;

  beforeEach(() => {
    el = document.createElement('footer');
    document.body.appendChild(el);
  });

  afterEach(() => {
    el.remove();
  });

  it('renders linkedin link with custom text', () => {
    renderFooter(el, { linkedin: 'https://linkedin.com/in/james', linkedin_text: 'Find me on LinkedIn' });
    const link = el.querySelector('.footer__link--linkedin');
    expect(link).not.toBeNull();
    expect(link.getAttribute('href')).toBe('https://linkedin.com/in/james');
    expect(link.textContent).toBe('Find me on LinkedIn');
  });

  it('falls back to "LinkedIn" when linkedin_text not set', () => {
    renderFooter(el, { linkedin: 'https://linkedin.com/in/james' });
    expect(el.querySelector('.footer__link--linkedin').textContent).toBe('LinkedIn');
  });

  it('renders instagram link with custom text', () => {
    renderFooter(el, { instagram: 'https://instagram.com/james', instagram_text: '@james' });
    const link = el.querySelector('.footer__link--instagram');
    expect(link).not.toBeNull();
    expect(link.getAttribute('href')).toBe('https://instagram.com/james');
    expect(link.textContent).toBe('@james');
  });

  it('falls back to "Instagram" when instagram_text not set', () => {
    renderFooter(el, { instagram: 'https://instagram.com/james' });
    expect(el.querySelector('.footer__link--instagram').textContent).toBe('Instagram');
  });

  it('renders email as mailto link', () => {
    renderFooter(el, { email: 'james@example.com', email_text: 'Email me' });
    const link = el.querySelector('.footer__link--email');
    expect(link).not.toBeNull();
    expect(link.getAttribute('href')).toBe('mailto:james@example.com');
    expect(link.textContent).toBe('Email me');
  });

  it('falls back to email address as text when email_text not set', () => {
    renderFooter(el, { email: 'james@example.com' });
    expect(el.querySelector('.footer__link--email').textContent).toBe('james@example.com');
  });

  it('renders all three links', () => {
    renderFooter(el, {
      linkedin: 'https://linkedin.com/in/james',
      instagram: 'https://instagram.com/james',
      email: 'james@example.com',
    });
    expect(el.querySelectorAll('.footer__link').length).toBe(3);
  });

  it('renders only the links that have values', () => {
    renderFooter(el, { linkedin: 'https://linkedin.com/in/james' });
    expect(el.querySelectorAll('.footer__link').length).toBe(1);
    expect(el.querySelector('.footer__link--instagram')).toBeNull();
    expect(el.querySelector('.footer__link--email')).toBeNull();
  });

  it('renders only copyright when no brand fields are set', () => {
    renderFooter(el, {});
    expect(el.querySelector('.footer__copyright')).not.toBeNull();
    expect(el.querySelector('.footer__nav')).toBeNull();
  });

  it('renders only copyright when called with no argument', () => {
    renderFooter(el);
    expect(el.querySelector('.footer__copyright')).not.toBeNull();
    expect(el.querySelector('.footer__nav')).toBeNull();
  });

  it('sets target="_blank" and rel="noopener noreferrer" on external links', () => {
    renderFooter(el, { linkedin: 'https://linkedin.com/in/james' });
    const link = el.querySelector('.footer__link--linkedin');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
  });

  it('wraps links in a nav with aria-label', () => {
    renderFooter(el, { email: 'james@example.com' });
    const nav = el.querySelector('nav.footer__nav');
    expect(nav).not.toBeNull();
    expect(nav.getAttribute('aria-label')).toBe('Contact links');
  });

  it('escapes XSS in linkedin URL — prevents attribute injection', () => {
    // Attacker tries to break out of href with a quote to inject an onclick handler
    renderFooter(el, { linkedin: 'https://example.com/" onclick="alert(1)' });
    const link = el.querySelector('.footer__link--linkedin');
    expect(link.getAttribute('onclick')).toBeNull();
  });

  it('escapes XSS in linkedin_text', () => {
    renderFooter(el, { linkedin: 'https://linkedin.com', linkedin_text: '<img onerror=alert(1)>' });
    expect(el.querySelector('.footer__link--linkedin').textContent).toBe('<img onerror=alert(1)>');
    expect(el.innerHTML).not.toContain('<img');
  });

  it('escapes XSS in email address — prevents attribute injection', () => {
    // Attacker tries to inject an event handler via the mailto href
    renderFooter(el, { email: 'test@example.com" onmouseover="alert(1)' });
    const link = el.querySelector('.footer__link--email');
    expect(link.getAttribute('onmouseover')).toBeNull();
  });
});

// ── scrollToFooter ────────────────────────────────────────────────────────────

describe('scrollToFooter', () => {
  it('calls scrollIntoView with smooth behaviour on the Footer element', () => {
    const footer = document.createElement('footer');
    footer.id = 'Footer';
    const mockScroll = vi.fn();
    footer.scrollIntoView = mockScroll;
    document.body.appendChild(footer);

    scrollToFooter();
    expect(mockScroll).toHaveBeenCalledWith({ behavior: 'smooth' });

    footer.remove();
  });

  it('does not throw when Footer element is absent', () => {
    expect(() => scrollToFooter()).not.toThrow();
  });
});

// ── initFooter ────────────────────────────────────────────────────────────────

describe('initFooter', () => {
  let el;

  beforeEach(() => {
    el = document.createElement('footer');
    el.id = 'Footer';
    document.body.appendChild(el);
    vi.resetAllMocks();
  });

  afterEach(() => {
    el.remove();
  });

  it('fetches /api/settings/brand', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await initFooter();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/settings/brand'));
  });

  it('renders footer after successful fetch', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ linkedin: 'https://linkedin.com/in/james', linkedin_text: 'LinkedIn' }),
    });
    await initFooter();
    expect(el.querySelector('.footer__link--linkedin')).not.toBeNull();
  });

  it('does not throw when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    await expect(initFooter()).resolves.not.toThrow();
    expect(el.querySelector('.footer__copyright')).toBeNull();
  });

  it('does nothing when response is not ok', async () => {
    global.fetch.mockResolvedValue({ ok: false });
    await initFooter();
    expect(el.querySelector('.footer__copyright')).toBeNull();
  });

  it('does nothing when Footer element is absent', async () => {
    el.remove();
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await expect(initFooter()).resolves.not.toThrow();
  });
});
