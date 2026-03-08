import { describe, expect, it } from 'vitest';
import { escapeHtml, formatDate } from '../js/utils.js';

describe('escapeHtml', () => {
  it('escapes ampersands', () => {
    expect(escapeHtml('a & b')).toBe('a &amp; b');
  });

  it('escapes less-than', () => {
    expect(escapeHtml('<script>')).toBe('&lt;script&gt;');
  });

  it('escapes double quotes', () => {
    expect(escapeHtml('"hello"')).toBe('&quot;hello&quot;');
  });

  it('escapes single quotes', () => {
    expect(escapeHtml("it's")).toBe('it&#39;s');
  });

  it('returns empty string for null', () => {
    expect(escapeHtml(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(escapeHtml(undefined)).toBe('');
  });

  it('passes through safe strings unchanged', () => {
    expect(escapeHtml('hello world')).toBe('hello world');
  });

  it('converts numbers to strings', () => {
    expect(escapeHtml(42)).toBe('42');
  });

  it('blocks XSS payload', () => {
    const xss = '<img src=x onerror="alert(1)">';
    expect(escapeHtml(xss)).not.toContain('<img');
    expect(escapeHtml(xss)).toContain('&lt;img');
  });
});

describe('formatDate', () => {
  it('formats ISO date into readable string', () => {
    const result = formatDate('2026-03-08');
    expect(result).toMatch(/8 March 2026|March 8, 2026/);
  });

  it('returns original string on invalid date', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date');
  });

  it('handles undefined gracefully', () => {
    // Should not throw
    const result = formatDate(undefined);
    expect(typeof result).toBe('string');
  });
});
