import { beforeEach, describe, expect, it, vi } from 'vitest';

// Mock window.matchMedia before importing brand.js
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: query.includes('dark'),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

global.fetch = vi.fn();

describe('loadBrand', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    // Reset the module cache so _brand is null again
    vi.resetModules();
    // Clear any link elements added in previous tests
    document.querySelectorAll('link[rel="icon"], link[rel="apple-touch-icon"]').forEach(el => el.remove());
  });

  it('fetches from /api/settings/brand', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/settings/brand'));
  });

  it('applies light favicon when light URL is set and no dark preference', async () => {
    // Override matchMedia to return light preference
    window.matchMedia = vi.fn().mockReturnValue({ matches: false });
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        favicon_light_url: '/static/favicons/favicon-light.svg',
        favicon_dark_url: '/static/favicons/favicon-dark.svg',
      }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon?.href).toContain('favicon-light.svg');
  });

  it('applies dark favicon when dark preference is set', async () => {
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        favicon_light_url: '/static/favicons/favicon-light.svg',
        favicon_dark_url: '/static/favicons/favicon-dark.svg',
      }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon?.href).toContain('favicon-dark.svg');
  });

  it('falls back to light favicon when dark URL is missing', async () => {
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ favicon_light_url: '/static/favicons/favicon-light.svg' }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon?.href).toContain('favicon-light.svg');
  });

  it('sets apple-touch-icon to 192px PNG variant', async () => {
    window.matchMedia = vi.fn().mockReturnValue({ matches: false });
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ favicon_light_url: '/static/favicons/favicon-light.svg' }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const apple = document.querySelector('link[rel="apple-touch-icon"]');
    expect(apple?.href).toContain('favicon-light-192.png');
  });

  it('does not throw when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    const { loadBrand } = await import('../js/brand.js');
    await expect(loadBrand()).resolves.not.toThrow();
  });

  it('does not set favicon when no URL is available', async () => {
    window.matchMedia = vi.fn().mockReturnValue({ matches: false });
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    // Should not add an icon link if no URLs set
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon).toBeNull();
  });
});
