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
