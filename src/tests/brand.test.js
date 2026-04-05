import { beforeEach, describe, expect, it, vi } from 'vitest';

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

  it('applies favicon when favicon_url is set', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ favicon_url: '/static/favicons/favicon.svg' }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon?.href).toContain('favicon.svg');
  });

  it('sets apple-touch-icon to 192px PNG variant', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ favicon_url: '/static/favicons/favicon.svg' }),
    });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const apple = document.querySelector('link[rel="apple-touch-icon"]');
    expect(apple?.href).toContain('favicon-192.png');
  });

  it('does not throw when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    const { loadBrand } = await import('../js/brand.js');
    await expect(loadBrand()).resolves.not.toThrow();
  });

  it('does not set favicon when favicon_url is absent', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    const { loadBrand } = await import('../js/brand.js');
    await loadBrand();
    const icon = document.querySelector('link[rel="icon"]');
    expect(icon).toBeNull();
  });
});

describe('getBrand', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    vi.resetModules();
    document.querySelectorAll('link[rel="icon"], link[rel="apple-touch-icon"]').forEach(el => el.remove());
  });

  it('returns empty object before loadBrand is called', async () => {
    const { getBrand } = await import('../js/brand.js');
    expect(getBrand()).toEqual({});
  });

  it('returns cached brand data after loadBrand succeeds', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ favicon_url: '/static/favicons/favicon.svg', linkedin: 'https://linkedin.com' }),
    });
    const { loadBrand, getBrand } = await import('../js/brand.js');
    await loadBrand();
    const brand = getBrand();
    expect(brand.favicon_url).toBe('/static/favicons/favicon.svg');
    expect(brand.linkedin).toBe('https://linkedin.com');
  });

  it('returns empty object when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    const { loadBrand, getBrand } = await import('../js/brand.js');
    await loadBrand();
    expect(getBrand()).toEqual({});
  });
});
