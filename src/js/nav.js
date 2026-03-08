export function initNav() {
  const navButton = document.querySelector('[data-jb-action="OpenSiteNav"]');

  function openNav() {
    document.body.classList.add('prevent-scroll', 'site-nav-open');
    if (navButton) navButton.setAttribute('aria-expanded', 'true');
  }

  function closeNav() {
    document.body.classList.remove('site-nav-open');
    if (navButton) navButton.setAttribute('aria-expanded', 'false');
  }

  // Nav open/close toggle via button click
  document.body.addEventListener('click', function (e) {
    const trigger = e.target.closest('[data-jb-action]');
    if (!trigger) return;

    if (trigger.dataset.jbAction === 'OpenSiteNav') {
      if (document.body.classList.contains('site-nav-open')) {
        closeNav();
      } else {
        openNav();
      }
    }
  });

  // Close nav with Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && document.body.classList.contains('site-nav-open')) {
      closeNav();
    }
  });

  // Remove prevent-scroll after nav close transition completes
  document.body.addEventListener('transitionend', function (e) {
    if (
      e.target.dataset.jbTransition === 'SiteNav' &&
      !document.body.classList.contains('site-nav-open')
    ) {
      document.body.classList.remove('prevent-scroll');
    }
  });
}
