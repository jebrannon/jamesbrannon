import '../less/main.less';
import { initNav } from './nav.js';
import { initRouter } from './router.js';
import { initFooter } from './footer.js';
import { loadBrand } from './brand.js';

document.addEventListener('DOMContentLoaded', () => {
  loadBrand();    // Fetch brand settings + apply favicons (non-blocking)
  initFooter();  // Populate footer with contact links from Brand settings
  initNav();
  initRouter();
});
