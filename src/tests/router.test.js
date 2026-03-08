import { beforeEach, describe, expect, it, vi } from 'vitest';
import { applyTheme } from '../js/router.js';

// router.js uses fetch and import.meta.env — stub them
global.fetch = vi.fn();

describe('Router > applyTheme', () => {
  beforeEach(() => {
    document.body.className = '';
  });

  it('defaults to dark + professional when called with empty object', () => {
    applyTheme({});
    expect(document.body.classList.contains('dark')).toBe(true);
    expect(document.body.classList.contains('professional')).toBe(true);
  });

  it('defaults to dark + professional when called with null', () => {
    applyTheme(null);
    expect(document.body.classList.contains('dark')).toBe(true);
    expect(document.body.classList.contains('professional')).toBe(true);
  });

  it('applies light mode', () => {
    applyTheme({ theme_mode: 'light', theme_style: 'professional' });
    expect(document.body.classList.contains('light')).toBe(true);
    expect(document.body.classList.contains('dark')).toBe(false);
  });

  it('applies thoughts style', () => {
    applyTheme({ theme_mode: 'dark', theme_style: 'thoughts' });
    expect(document.body.classList.contains('thoughts')).toBe(true);
    expect(document.body.classList.contains('professional')).toBe(false);
  });

  it('applies light + thoughts', () => {
    applyTheme({ theme_mode: 'light', theme_style: 'thoughts' });
    expect(document.body.classList.contains('light')).toBe(true);
    expect(document.body.classList.contains('thoughts')).toBe(true);
  });

  it('replaces previous mode class', () => {
    document.body.classList.add('dark', 'professional');
    applyTheme({ theme_mode: 'light', theme_style: 'professional' });
    expect(document.body.classList.contains('dark')).toBe(false);
    expect(document.body.classList.contains('light')).toBe(true);
  });

  it('replaces previous style class', () => {
    document.body.classList.add('dark', 'professional');
    applyTheme({ theme_mode: 'dark', theme_style: 'thoughts' });
    expect(document.body.classList.contains('professional')).toBe(false);
    expect(document.body.classList.contains('thoughts')).toBe(true);
  });

  it('preserves unrelated body classes', () => {
    document.body.classList.add('site-nav-open', 'prevent-scroll');
    applyTheme({ theme_mode: 'dark', theme_style: 'professional' });
    expect(document.body.classList.contains('site-nav-open')).toBe(true);
    expect(document.body.classList.contains('prevent-scroll')).toBe(true);
  });

  it('never adds both mode classes simultaneously', () => {
    applyTheme({ theme_mode: 'light', theme_style: 'thoughts' });
    expect(document.body.classList.contains('dark')).toBe(false);
    expect(document.body.classList.contains('light')).toBe(true);
  });

  it('never adds both style classes simultaneously', () => {
    applyTheme({ theme_mode: 'dark', theme_style: 'professional' });
    expect(document.body.classList.contains('thoughts')).toBe(false);
    expect(document.body.classList.contains('professional')).toBe(true);
  });
});


// ── applyHead ─────────────────────────────────────────────────────────────────

import { applyHead, fetchJSON } from '../js/router.js';

describe('Router > applyHead', () => {
  beforeEach(() => {
    document.title = '';
    // Remove any meta/link tags added by previous tests
    document.querySelectorAll('meta[name="description"], meta[property^="og:"], meta[name="robots"], link[rel="canonical"]')
      .forEach(el => el.remove());
  });

  it('sets document.title from seo_title', () => {
    applyHead({ seo_title: 'My SEO Title' });
    expect(document.title).toBe('My SEO Title');
  });

  it('falls back to title when seo_title absent', () => {
    applyHead({ title: 'Page Title' });
    expect(document.title).toBe('Page Title');
  });

  it('sets meta description', () => {
    applyHead({ seo_description: 'A page description.' });
    const el = document.querySelector('meta[name="description"]');
    expect(el?.getAttribute('content')).toBe('A page description.');
  });

  it('sets og:title', () => {
    applyHead({ seo_title: 'OG Title' });
    const el = document.querySelector('meta[property="og:title"]');
    expect(el?.getAttribute('content')).toBe('OG Title');
  });

  it('sets og:type', () => {
    applyHead({ og_type: 'article' });
    const el = document.querySelector('meta[property="og:type"]');
    expect(el?.getAttribute('content')).toBe('article');
  });

  it('sets robots to noindex when no_index is true', () => {
    applyHead({ no_index: true });
    const el = document.querySelector('meta[name="robots"]');
    expect(el?.getAttribute('content')).toBe('noindex,nofollow');
  });

  it('sets robots to index,follow when no_index is false', () => {
    applyHead({ no_index: false });
    const el = document.querySelector('meta[name="robots"]');
    expect(el?.getAttribute('content')).toBe('index,follow');
  });

  it('adds canonical link when canonical_url provided', () => {
    applyHead({ canonical_url: 'https://jamesbrannon.co.uk/about' });
    const el = document.querySelector('link[rel="canonical"]');
    expect(el?.href).toBe('https://jamesbrannon.co.uk/about');
  });

  it('handles empty data object without throwing', () => {
    expect(() => applyHead({})).not.toThrow();
  });
});

// ── fetchJSON ─────────────────────────────────────────────────────────────────

describe('Router > fetchJSON', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('returns parsed JSON on 200 response', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'Hello' }),
    });
    const data = await fetchJSON('/api/posts/hello');
    expect(data.title).toBe('Hello');
  });

  it('throws with status on non-ok response', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404 });
    await expect(fetchJSON('/api/posts/missing')).rejects.toMatchObject({ status: 404 });
  });

  it('throws on 500', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 500 });
    await expect(fetchJSON('/api/posts/error')).rejects.toMatchObject({ status: 500 });
  });
});
