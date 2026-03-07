import '../less/main.less';
import { initNav } from './nav.js';
import { initRouter } from './router.js';
import { initBlogFeeds } from './components/blog-feed.js';
import { loadBrand } from './brand.js';

document.addEventListener('DOMContentLoaded', () => {
  loadBrand();   // Fetch brand settings + apply favicons (non-blocking)
  initNav();
  initRouter();
  initBlogFeeds();
});
