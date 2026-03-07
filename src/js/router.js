const BASE = import.meta.env?.VITE_API_BASE ?? '';

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

  // Canonical URL
  if (data.canonical_url) {
    _setCanonical(data.canonical_url);
  }

  // Robots directive
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

async function renderPost(slug) {
  const data = await fetchJSON(`${BASE}/api/posts/${slug}`);
  applyTheme(data);
  applyHead(data);
  const app = document.getElementById('App');
  if (app) {
    app.innerHTML = `
      <article class="post">
        <header class="post__header">
          <h1 class="post__title">${data.title}</h1>
          ${data.date ? `<time class="post__date" datetime="${data.date}">${formatDate(data.date)}</time>` : ''}
          ${data.tags?.length ? `<ul class="post__tags">${data.tags.map(t => `<li>${t}</li>`).join('')}</ul>` : ''}
        </header>
        <div class="post__body">${data.body}</div>
      </article>`;
  }
}

async function renderPortfolioItem(slug) {
  const data = await fetchJSON(`${BASE}/api/portfolio/${slug}`);
  applyTheme(data);
  applyHead(data);
  const app = document.getElementById('App');
  if (app) {
    app.innerHTML = `
      <article class="portfolio-item">
        <header class="portfolio-item__header">
          <h1 class="portfolio-item__title">${data.title}</h1>
        </header>
        <div class="portfolio-item__body">${data.body}</div>
      </article>`;
  }
}

async function renderCMSPage(slug) {
  const data = await fetchJSON(`${BASE}/api/pages/${slug}`);
  applyTheme(data);
  applyHead(data);
  const app = document.getElementById('App');
  if (app) {
    app.innerHTML = `
      <section class="cms-page">
        <h1 class="cms-page__title">${data.title}</h1>
        <div class="cms-page__body">${data.body || ''}</div>
      </section>`;
  }
}

function render404() {
  const app = document.getElementById('App');
  if (app) app.innerHTML = '<p class="error-404">Page not found.</p>';
}

// ── Router ────────────────────────────────────────────────────────────────────

const STATIC_PATHS = ['/', '/about', '/blog', '/work'];

async function route(path) {
  const blogMatch = path.match(/^\/blog\/([^/]+)$/);
  if (blogMatch) return renderPost(blogMatch[1]);

  const workMatch = path.match(/^\/work\/([^/]+)$/);
  if (workMatch) return renderPortfolioItem(workMatch[1]);

  // Dynamic CMS page — any path not handled statically by the existing HTML
  if (!STATIC_PATHS.includes(path)) {
    try {
      return await renderCMSPage(path.replace(/^\//, ''));
    } catch (e) {
      if (e.status === 404) render404();
      else console.error('Router error:', e);
    }
  }
}

export function navigate(path) {
  history.pushState({}, '', path);
  route(path);
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
        navigate(url.pathname);
      }
    } catch (_) { /* non-parseable href, let browser handle */ }
  });

  // Browser back / forward
  window.addEventListener('popstate', () => route(location.pathname));

  // Initial route on page load
  route(location.pathname);
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch (_) { return iso; }
}
