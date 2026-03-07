import '../less/main.less';
import { initNav } from './nav.js';
import { initRouter } from './router.js';
import { initBlogFeeds } from './components/blog-feed.js';

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initRouter();
  initBlogFeeds();
});
