import { escapeHtml, formatDate } from './utils.js';
import { renderBlogFeed } from './components/blog-feed.js';
import { scrollToFooter } from './footer.js';

const BASE = import.meta.env?.VITE_API_BASE ?? '';
const POSTS_PER_PAGE = 10;

// ── Theme ─────────────────────────────────────────────────────────────────────

export function applyTheme(data) {
  document.body.classList.remove('dark', 'light', 'professional', 'thoughts');
  document.body.classList.add(
    data?.theme_mode || 'dark',
    data?.theme_style || 'professional'
  );
}

// ── SEO / <head> ──────────────────────────────────────────────────────────────

/**
 * Update <title> and meta/og tags for the current page.
 * Falls back to data.title when seo_title is absent.
 */
export function applyHead(data = {}) {
  const title = data.seo_title || data.title;
  if (title) document.title = title;

  _setMeta('name', 'description', data.seo_description || '');
  _setMeta('property', 'og:title', title || '');
  _setMeta('property', 'og:description', data.seo_description || '');
  _setMeta('property', 'og:image', data.og_image || '');
  _setMeta('property', 'og:type', data.og_type || 'website');

  if (data.canonical_url) _setCanonical(data.canonical_url);
  _setMeta('name', 'robots', data.no_index ? 'noindex,nofollow' : 'index,follow');
}

function _setMeta(attrName, attrValue, content) {
  let el = document.querySelector(`meta[${attrName}="${attrValue}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attrName, attrValue);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function _setCanonical(href) {
  let link = document.querySelector('link[rel="canonical"]');
  if (!link) {
    link = document.createElement('link');
    link.rel = 'canonical';
    document.head.appendChild(link);
  }
  link.href = href;
}

// ── Fetch helper ──────────────────────────────────────────────────────────────

export async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// ── Page renderers ────────────────────────────────────────────────────────────

export async function renderHomepage() {
  applyTheme({});
  applyHead({ title: 'James' });
  const app = document.getElementById('App');
  if (!app) return;

  try {
    const profile = await fetchJSON(`${BASE}/api/settings/profile`);
    const blogLimit = profile.blog?.limit ?? 3;

    let html = '<div class="homepage">';

    if (profile.summary) {
      html += `<div class="homepage__summary">${profile.summary}</div>`;
    }

    // Blog feed section
    html += `<section class="homepage__blog">`;
    if (profile.blog?.headline) {
      html += `<h2 class="homepage__section-title">${escapeHtml(profile.blog.headline)}</h2>`;
    }
    html += `<div data-jb-blog-feed data-limit="${blogLimit}"></div>`;
    html += `<a href="/blog" class="homepage__blog-more">All posts</a>`;
    html += `</section>`;

    // Strengths section
    if (profile.strengths?.items?.length) {
      html += `<section class="homepage__strengths">`;
      if (profile.strengths.headline) {
        html += `<h2 class="homepage__section-title">${escapeHtml(profile.strengths.headline)}</h2>`;
      }
      html += `<ul class="strengths-list">`;
      for (const item of profile.strengths.items) {
        html += `<li class="strengths-list__item">`;
        html += `<strong class="strengths-list__name">${escapeHtml(item.name)}</strong>`;
        if (item.description) {
          html += `<p class="strengths-list__desc">${escapeHtml(item.description)}</p>`;
        }
        html += `</li>`;
      }
      html += `</ul></section>`;
    }

    // Experience section
    if (profile.experience?.items?.length) {
      html += `<section class="homepage__experience">`;
      if (profile.experience.headline) {
        html += `<h2 class="homepage__section-title">${escapeHtml(profile.experience.headline)}</h2>`;
      }
      html += `<ul class="experience-list">`;
      for (const item of profile.experience.items) {
        html += `<li class="experience-list__item">`;
        html += `<h3 class="experience-list__title">${escapeHtml(item.job_title)}</h3>`;
        if (item.company) html += `<p class="experience-list__company">${escapeHtml(item.company)}</p>`;
        if (item.dates) html += `<p class="experience-list__dates">${escapeHtml(item.dates)}</p>`;
        // item.summary is CMS-authored HTML — intentionally rendered as markup.
        if (item.summary) html += `<div class="experience-list__summary">${item.summary}</div>`;
        html += `</li>`;
      }
      html += `</ul></section>`;
    }

    html += '</div>';
    app.innerHTML = html;

    // Initialise blog feed after inserting into DOM
    const feedEl = app.querySelector('[data-jb-blog-feed]');
    if (feedEl) renderBlogFeed(feedEl, { limit: blogLimit });

  } catch (e) {
    console.error('Homepage error:', e);
    app.innerHTML = '<p class="error">Could not load page content.</p>';
  }
}

export async function renderBlogListing(page = 1) {
  applyTheme({});
  applyHead({ title: 'Blog — James Brannon' });
  const app = document.getElementById('App');
  if (!app) return;

  try {
    const posts = await fetchJSON(`${BASE}/api/posts?limit=100&published=true`);
    const totalPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
    const currentPage = Math.min(Math.max(1, page), totalPages);
    const slice = posts.slice((currentPage - 1) * POSTS_PER_PAGE, currentPage * POSTS_PER_PAGE);

    let html = '<section class="blog-listing"><h1 class="blog-listing__title">Blog</h1>';

    if (!slice.length) {
      html += '<p class="blog-listing__empty">No posts yet.</p>';
    } else {
      html += '<ul class="blog-listing__posts">';
      for (const post of slice) {
        html += `<li class="blog-listing__item">
          <h2 class="blog-listing__post-title">
            <a href="/blog/${escapeHtml(post.slug)}">${escapeHtml(post.title)}</a>
          </h2>
          ${post.date ? `<time class="blog-listing__date" datetime="${escapeHtml(post.date)}">${escapeHtml(formatDate(post.date))}</time>` : ''}
          ${post.excerpt ? `<p class="blog-listing__excerpt">${escapeHtml(post.excerpt)}</p>` : ''}
        </li>`;
      }
      html += '</ul>';
    }

    if (totalPages > 1) {
      html += '<nav class="blog-listing__pagination" aria-label="Blog pagination">';
      if (currentPage > 1) {
        html += `<a href="/blog?page=${currentPage - 1}" class="blog-listing__prev">\u2190 Newer</a>`;
      }
      html += `<span class="blog-listing__page-info">Page ${currentPage} of ${totalPages}</span>`;
      if (currentPage < totalPages) {
        html += `<a href="/blog?page=${currentPage + 1}" class="blog-listing__next">Older \u2192</a>`;
      }
      html += '</nav>';
    }

    html += '</section>';
    app.innerHTML = html;
  } catch (e) {
    console.error('Blog listing error:', e);
    app.innerHTML = '<p class="error">Could not load blog posts.</p>';
  }
}

export async function renderPost(slug) {
  const app = document.getElementById('App');
  if (!app) return;
  try {
    const data = await fetchJSON(`${BASE}/api/posts/${slug}`);
    applyTheme(data);
    applyHead(data);
    // data.body is CMS-authored HTML — intentionally rendered as markup.
    // All other interpolated values are escaped to prevent XSS.
    app.innerHTML = `
      <article class="post">
        <header class="post__header">
          <h1 class="post__title">${escapeHtml(data.title)}</h1>
          ${data.date ? `<time class="post__date" datetime="${escapeHtml(data.date)}">${escapeHtml(formatDate(data.date))}</time>` : ''}
          ${data.category ? `<span class="post__category">${escapeHtml(data.category)}</span>` : ''}
        </header>
        <div class="post__body">${data.body || ''}</div>
      </article>`;
  } catch (e) {
    if (e.status === 404) render404();
    else console.error('Post error:', e);
  }
}

export async function renderCMSPage(slug) {
  const app = document.getElementById('App');
  if (!app) return;
  try {
    const data = await fetchJSON(`${BASE}/api/pages/${slug}`);
    applyTheme(data);
    applyHead(data);
    // data.body is CMS-authored HTML — intentionally rendered as markup.
    app.innerHTML = `
      <section class="cms-page">
        <h1 class="cms-page__title">${escapeHtml(data.title)}</h1>
        <div class="cms-page__body">${data.body || ''}</div>
      </section>`;
  } catch (e) {
    if (e.status === 404) render404();
    else console.error('CMS page error:', e);
  }
}

export function render404() {
  const app = document.getElementById('App');
  if (app) app.innerHTML = '<p class="error-404">Page not found.</p>';
}

// ── Router ────────────────────────────────────────────────────────────────────

export async function route(path, search = '') {
  if (path === '/') return renderHomepage();

  if (path === '/blog') {
    const page = parseInt(new URLSearchParams(search).get('page') || '1', 10);
    return renderBlogListing(page);
  }

  const blogMatch = path.match(/^\/blog\/([^/]+)$/);
  if (blogMatch) return renderPost(blogMatch[1]);

  if (path === '/contact') return scrollToFooter();

  // Dynamic CMS page — strip leading slash and fetch by slug
  try {
    return await renderCMSPage(path.replace(/^\//, ''));
  } catch (e) {
    if (e.status === 404) render404();
    else console.error('Router error:', e);
  }
}

export function navigate(href) {
  history.pushState({}, '', href);
  const url = new URL(href, location.origin);
  route(url.pathname, url.search);
}

export function initRouter() {
  // Intercept same-origin link clicks
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    try {
      const url = new URL(link.href, location.origin);
      if (url.origin === location.origin && !link.dataset.external) {
        e.preventDefault();
        navigate(link.href);
      }
    } catch (_) { /* non-parseable href, let browser handle */ }
  });

  // Browser back / forward
  window.addEventListener('popstate', () => route(location.pathname, location.search));

  // Initial route on page load
  route(location.pathname, location.search);
}
