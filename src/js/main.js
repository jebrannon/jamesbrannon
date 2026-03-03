import '../less/main.less';

document.addEventListener('DOMContentLoaded', function () {

  // Nav open/close toggle
  document.body.addEventListener('click', function (e) {
    const trigger = e.target.closest('[data-jb-action]');
    if (!trigger) return;

    if (trigger.dataset.jbAction === 'OpenSiteNav') {
      if (!document.body.classList.contains('site-nav-open')) {
        document.body.classList.add('prevent-scroll');
      }
      document.body.classList.toggle('site-nav-open');
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

});
