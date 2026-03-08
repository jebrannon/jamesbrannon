import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderBlogFeed } from '../js/components/blog-feed.js';

global.fetch = vi.fn();

function makePost(overrides = {}) {
  return {
    slug: 'test-post',
    title: 'Test Post',
    date: '2026-01-15',
    excerpt: 'A short excerpt.',
    ...overrides,
  };
}

describe('renderBlogFeed', () => {
  let container;

  beforeEach(() => {
    container = document.createElement('div');
    vi.clearAllMocks();
  });

  it('renders a list of posts', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ slug: 'post-1', title: 'Post One' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    expect(container.innerHTML).toContain('Post One');
    expect(container.innerHTML).toContain('/blog/post-1');
  });

  it('renders excerpt when present', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ excerpt: 'My excerpt here.' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    expect(container.innerHTML).toContain('My excerpt here.');
  });

  it('renders date when present', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ date: '2026-01-15' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    expect(container.querySelector('time')).not.toBeNull();
  });

  it('shows empty state when no posts returned', async () => {
    global.fetch.mockResolvedValue({ json: async () => [] });
    await renderBlogFeed(container, { limit: 3 });
    expect(container.innerHTML).toContain('No posts yet');
  });

  it('shows error state on fetch failure', async () => {
    global.fetch.mockRejectedValue(new Error('Network error'));
    await renderBlogFeed(container, { limit: 3 });
    expect(container.innerHTML).toContain('Could not load posts');
  });

  it('escapes XSS in title', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ title: '<script>alert(1)</script>' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    // No actual <script> element injected into the DOM — happy-dom doesn't
    // re-escape text nodes in innerHTML, so we test via DOM queries
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('.blog-feed__title').textContent).toContain('<script>alert(1)</script>');
  });

  it('escapes XSS in slug', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ slug: '"><script>alert(1)</script>' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    // No actual <script> element injected into the DOM
    expect(container.querySelector('script')).toBeNull();
  });

  it('escapes XSS in excerpt', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ excerpt: '<img src=x onerror="alert(1)">' })],
    });
    await renderBlogFeed(container, { limit: 1 });
    // No <img> with an event handler should be injected
    expect(container.querySelector('img[onerror]')).toBeNull();
    expect(container.querySelector('.blog-feed__excerpt').textContent).toContain('<img src=x');
  });

  it('includes limit in request URL', async () => {
    global.fetch.mockResolvedValue({ json: async () => [] });
    await renderBlogFeed(container, { limit: 5 });
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('limit=5'));
  });

  it('omits excerpt element when excerpt is absent', async () => {
    global.fetch.mockResolvedValue({
      json: async () => [makePost({ excerpt: undefined })],
    });
    await renderBlogFeed(container);
    expect(container.querySelector('.blog-feed__excerpt')).toBeNull();
  });
});
