const BASE = import.meta.env?.VITE_API_BASE ?? '';

/**
 * Render a blog feed into a container element.
 * @param {HTMLElement} container
 * @param {{ limit?: number, published?: boolean }} options
 */
export async function renderBlogFeed(container, options = {}) {
  const { limit = 3, published = true } = options;
  try {
    const params = new URLSearchParams({ limit });
    if (published !== null) params.set('published', published);
    const posts = await fetch(`${BASE}/api/posts?${params}`).then((r) => r.json());

    if (!posts.length) {
      container.innerHTML = '<p class="blog-feed__empty">No posts yet.</p>';
      return;
    }

    container.innerHTML = posts
      .map(
        (post) => `
      <article class="blog-feed__item">
        <h3 class="blog-feed__title">
          <a href="/blog/${post.slug}">${post.title}</a>
        </h3>
        ${post.date ? `<time class="blog-feed__date" datetime="${post.date}">${formatDate(post.date)}</time>` : ''}
        ${post.excerpt ? `<p class="blog-feed__excerpt">${post.excerpt}</p>` : ''}
      </article>`
      )
      .join('');
  } catch (e) {
    console.error('Blog feed error:', e);
    container.innerHTML = '<p class="blog-feed__error">Could not load posts.</p>';
  }
}

/**
 * Auto-initialise all [data-jb-blog-feed] elements on the page.
 * Usage: <div data-jb-blog-feed data-limit="3"></div>
 */
export function initBlogFeeds() {
  document.querySelectorAll('[data-jb-blog-feed]').forEach((el) => {
    const limit = parseInt(el.dataset.limit || '3', 10);
    renderBlogFeed(el, { limit });
  });
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch (_) { return iso; }
}
