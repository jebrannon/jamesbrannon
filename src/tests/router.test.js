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

  it('sets og:type from ogType option', () => {
    applyHead({}, { ogType: 'article' });
    const el = document.querySelector('meta[property="og:type"]');
    expect(el?.getAttribute('content')).toBe('article');
  });

  it('defaults og:type to website when no ogType option given', () => {
    applyHead({});
    const el = document.querySelector('meta[property="og:type"]');
    expect(el?.getAttribute('content')).toBe('website');
  });

  it('sets og:site_name from siteSettings', () => {
    applyHead({}, { siteSettings: { site_name: 'James Brannon' } });
    const el = document.querySelector('meta[property="og:site_name"]');
    expect(el?.getAttribute('content')).toBe('James Brannon');
  });

  it('falls back og:image to hero_thumbnail_url when og_image absent', () => {
    applyHead({ hero_thumbnail_url: 'https://example.com/thumb.jpg' });
    const el = document.querySelector('meta[property="og:image"]');
    expect(el?.getAttribute('content')).toBe('https://example.com/thumb.jpg');
  });

  it('falls back og:image to siteSettings.og_image when neither og_image nor hero_thumbnail_url set', () => {
    applyHead({}, { siteSettings: { og_image: 'https://example.com/default.jpg' } });
    const el = document.querySelector('meta[property="og:image"]');
    expect(el?.getAttribute('content')).toBe('https://example.com/default.jpg');
  });

  it('prefers og_image over hero_thumbnail_url', () => {
    applyHead({ og_image: 'https://example.com/og.jpg', hero_thumbnail_url: 'https://example.com/thumb.jpg' });
    const el = document.querySelector('meta[property="og:image"]');
    expect(el?.getAttribute('content')).toBe('https://example.com/og.jpg');
  });

  it('falls back description to siteSettings.seo_description', () => {
    applyHead({}, { siteSettings: { seo_description: 'Site default description' } });
    const el = document.querySelector('meta[name="description"]');
    expect(el?.getAttribute('content')).toBe('Site default description');
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

// ── route dispatch ────────────────────────────────────────────────────────────

import { route, renderPost, renderBlogListing, renderHomepage, renderCMSPage, render404 } from '../js/router.js';

// Mock footer.js so scrollToFooter is a spy
vi.mock('../js/footer.js', () => ({
  scrollToFooter: vi.fn(),
  renderFooter: vi.fn(),
  initFooter: vi.fn(),
}));

import { scrollToFooter } from '../js/footer.js';

describe('Router > route dispatch', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    document.body.className = '';
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
    vi.clearAllMocks();
  });

  afterEach(() => {
    app.remove();
  });

  it('/ fetches profile settings', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ blog: { limit: 3 } }),
    });
    await route('/');
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/settings/profile'));
  });

  it('/blog fetches posts with limit=100', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    await route('/blog');
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/posts?limit=100'));
  });

  it('/blog with ?page=2 renders page 2', async () => {
    const posts = Array.from({ length: 15 }, (_, i) => ({
      slug: `post-${i + 1}`,
      title: `Post ${i + 1}`,
      date: '2024-01-01',
    }));
    global.fetch.mockResolvedValue({ ok: true, json: async () => posts });
    await route('/blog', '?page=2');
    expect(app.querySelector('.blog-listing__next')).toBeNull();
    expect(app.querySelector('.blog-listing__prev')).not.toBeNull();
  });

  it('/blog/{slug} fetches the correct post', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'My Post', slug: 'my-post', body: '<p>Hello</p>' }),
    });
    await route('/blog/my-post');
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/posts/my-post'));
  });

  it('/contact calls scrollToFooter', async () => {
    await route('/contact');
    expect(scrollToFooter).toHaveBeenCalled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('/{slug} fetches the CMS page by slug', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'About', body: '<p>About me</p>' }),
    });
    await route('/about');
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/pages/about'));
  });

  it('unknown path attempts CMS page lookup', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'Custom', body: '' }),
    });
    await route('/some-custom-page');
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/pages/some-custom-page'));
  });

  it('unknown path renders 404 when CMS returns 404', async () => {
    const err = new Error('HTTP 404');
    err.status = 404;
    global.fetch.mockRejectedValue(err);
    await route('/missing');
    expect(app.querySelector('.error-404')).not.toBeNull();
  });
});

// ── renderBlogListing pagination ──────────────────────────────────────────────

describe('Router > renderBlogListing', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
  });

  afterEach(() => {
    app.remove();
  });

  it('renders a list of posts', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => [{ slug: 'hello', title: 'Hello World', date: '2024-01-01' }],
    });
    await renderBlogListing(1);
    expect(app.querySelector('.blog-listing__posts')).not.toBeNull();
    expect(app.querySelector('a[href="/blog/hello"]')).not.toBeNull();
  });

  it('shows empty state when no posts', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });
    await renderBlogListing(1);
    expect(app.querySelector('.blog-listing__empty')).not.toBeNull();
  });

  it('does not show pagination for 10 or fewer posts', async () => {
    const posts = Array.from({ length: 5 }, (_, i) => ({ slug: `p${i}`, title: `P${i}` }));
    global.fetch.mockResolvedValue({ ok: true, json: async () => posts });
    await renderBlogListing(1);
    expect(app.querySelector('.blog-listing__pagination')).toBeNull();
  });

  it('shows pagination for more than 10 posts', async () => {
    const posts = Array.from({ length: 12 }, (_, i) => ({ slug: `p${i}`, title: `P${i}` }));
    global.fetch.mockResolvedValue({ ok: true, json: async () => posts });
    await renderBlogListing(1);
    expect(app.querySelector('.blog-listing__pagination')).not.toBeNull();
    expect(app.querySelector('.blog-listing__next')).not.toBeNull();
    expect(app.querySelector('.blog-listing__prev')).toBeNull();
  });

  it('shows prev link on page 2', async () => {
    const posts = Array.from({ length: 12 }, (_, i) => ({ slug: `p${i}`, title: `P${i}` }));
    global.fetch.mockResolvedValue({ ok: true, json: async () => posts });
    await renderBlogListing(2);
    expect(app.querySelector('.blog-listing__prev')).not.toBeNull();
    expect(app.querySelector('.blog-listing__next')).toBeNull();
  });

  it('shows error state when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    await renderBlogListing(1);
    expect(app.querySelector('.error')).not.toBeNull();
  });

  it('escapes XSS in post title', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => [{ slug: 'xss', title: '<script>alert(1)</script>' }],
    });
    await renderBlogListing(1);
    expect(app.innerHTML).not.toContain('<script>');
  });
});

// ── renderHomepage ────────────────────────────────────────────────────────────

describe('Router > renderHomepage', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
  });

  afterEach(() => {
    app.remove();
  });

  it('fetches profile settings', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await renderHomepage();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/settings/profile'));
  });

  it('sets document.title to James', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await renderHomepage();
    expect(document.title).toBe('James');
  });

  it('renders summary HTML', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ summary: '<p>About me.</p>' }),
    });
    await renderHomepage();
    expect(app.querySelector('.homepage__summary')).not.toBeNull();
    expect(app.querySelector('.homepage__summary').innerHTML).toBe('<p>About me.</p>');
  });

  it('renders strengths section', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        strengths: { headline: 'Skills', items: [{ name: 'Design', description: 'UI/UX' }] },
      }),
    });
    await renderHomepage();
    expect(app.querySelector('.homepage__strengths')).not.toBeNull();
    expect(app.querySelector('.strengths-list__name').textContent).toBe('Design');
  });

  it('renders experience section', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        experience: {
          headline: 'Work',
          items: [{ job_title: 'Designer', company: 'Acme', dates: '2020–2023' }],
        },
      }),
    });
    await renderHomepage();
    expect(app.querySelector('.homepage__experience')).not.toBeNull();
    expect(app.querySelector('.experience-list__title').textContent).toBe('Designer');
    expect(app.querySelector('.experience-list__company').textContent).toBe('Acme');
  });

  it('skips sections with no data', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await renderHomepage();
    expect(app.querySelector('.homepage__strengths')).toBeNull();
    expect(app.querySelector('.homepage__experience')).toBeNull();
  });

  it('shows error when fetch fails', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    await renderHomepage();
    expect(app.querySelector('.error')).not.toBeNull();
  });

  it('always renders blog feed section', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    await renderHomepage();
    expect(app.querySelector('.homepage__blog')).not.toBeNull();
  });

  it('escapes XSS in strengths name', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        strengths: { items: [{ name: '<script>alert(1)</script>' }] },
      }),
    });
    await renderHomepage();
    expect(app.innerHTML).not.toContain('<script>');
  });
});

// ── renderPost ────────────────────────────────────────────────────────────────

import { renderPost } from '../js/router.js';

describe('Router > renderPost', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
  });

  afterEach(() => {
    app.remove();
  });

  it('renders post article from API response', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'Hello', slug: 'hello', body: '<p>World</p>' }),
    });
    await renderPost('hello');
    expect(app.querySelector('.post__title').textContent).toBe('Hello');
    expect(app.querySelector('.post__body').innerHTML).toBe('<p>World</p>');
  });

  it('renders 404 when post returns 404 error', async () => {
    const err = new Error('HTTP 404');
    err.status = 404;
    global.fetch.mockResolvedValue({ ok: false, status: 404 });
    await renderPost('missing');
    expect(app.querySelector('.error-404')).not.toBeNull();
  });

  it('renders date when present', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'Post', date: '2024-01-01', body: '' }),
    });
    await renderPost('post');
    expect(app.querySelector('time')).not.toBeNull();
  });

  it('renders category when present', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'Post', category: 'design', body: '' }),
    });
    await renderPost('post');
    expect(app.querySelector('.post__category').textContent).toBe('design');
  });

  it('escapes XSS in title', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: '<script>alert(1)</script>', body: '' }),
    });
    await renderPost('xss');
    expect(app.innerHTML).not.toContain('<script>alert');
  });
});

// ── renderCMSPage ─────────────────────────────────────────────────────────────

import { renderCMSPage } from '../js/router.js';

describe('Router > renderCMSPage', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
  });

  afterEach(() => {
    app.remove();
  });

  it('renders CMS page from API response', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: 'About', body: '<p>About me.</p>' }),
    });
    await renderCMSPage('about');
    expect(app.querySelector('.cms-page__title').textContent).toBe('About');
    expect(app.querySelector('.cms-page__body').innerHTML).toBe('<p>About me.</p>');
  });

  it('renders 404 when page returns 404', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404 });
    await renderCMSPage('missing');
    expect(app.querySelector('.error-404')).not.toBeNull();
  });

  it('escapes XSS in page title', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ title: '<script>xss</script>', body: '' }),
    });
    await renderCMSPage('xss');
    expect(app.innerHTML).not.toContain('<script>xss');
  });
});

// ── render404 ─────────────────────────────────────────────────────────────────

import { render404 } from '../js/router.js';

describe('Router > render404', () => {
  let app;

  beforeEach(() => {
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
  });

  afterEach(() => {
    if (document.getElementById('App')) app.remove();
  });

  it('renders the error-404 element', () => {
    render404();
    expect(app.querySelector('.error-404')).not.toBeNull();
    expect(app.querySelector('.error-404').textContent).toContain('not found');
  });

  it('does not throw when App element is absent', () => {
    app.remove();
    expect(() => render404()).not.toThrow();
  });
});

// ── navigate ──────────────────────────────────────────────────────────────────

import { navigate } from '../js/router.js';

describe('Router > navigate', () => {
  let app;

  beforeEach(() => {
    global.fetch = vi.fn();
    app = document.createElement('div');
    app.id = 'App';
    document.body.appendChild(app);
    vi.clearAllMocks();
  });

  afterEach(() => {
    app.remove();
  });

  it('pushes state to history', () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
    const pushSpy = vi.spyOn(history, 'pushState');
    navigate('/blog');
    expect(pushSpy).toHaveBeenCalledWith({}, '', '/blog');
    pushSpy.mockRestore();
  });

  it('triggers a fetch for the target path', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });
    navigate('/blog');
    // navigate() does not await route() — flush microtasks to let async handlers run
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(global.fetch).toHaveBeenCalled();
  });
});
