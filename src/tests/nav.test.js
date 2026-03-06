import { describe, it, expect, beforeEach } from 'vitest';
import { initNav } from '../js/nav.js';

const DOM = `
  <div id="SiteNav" data-jb-transition="SiteNav"></div>
  <a id="nav-button" data-jb-action="OpenSiteNav">
    <span id="nav-button-child"></span>
  </a>
  <div id="other-element"></div>
`;

function fireTransitionEnd(element) {
  const event = new Event('transitionend', { bubbles: true });
  element.dispatchEvent(event);
}

describe('Nav', () => {

  beforeEach(() => {
    document.body.className = 'theme';
    document.body.innerHTML = DOM;
    initNav();
  });

  describe('Opening', () => {

    it('adds site-nav-open to body when nav button is clicked', () => {
      document.getElementById('nav-button').click();
      expect(document.body.classList.contains('site-nav-open')).toBe(true);
    });

    it('adds prevent-scroll to body when nav opens', () => {
      document.getElementById('nav-button').click();
      expect(document.body.classList.contains('prevent-scroll')).toBe(true);
    });

    it('triggers correctly when clicking a child element inside the nav button', () => {
      document.getElementById('nav-button-child').click();
      expect(document.body.classList.contains('site-nav-open')).toBe(true);
    });

  });

  describe('Closing', () => {

    beforeEach(() => {
      document.getElementById('nav-button').click(); // open
    });

    it('removes site-nav-open from body on second click', () => {
      document.getElementById('nav-button').click();
      expect(document.body.classList.contains('site-nav-open')).toBe(false);
    });

    it('does not add a second prevent-scroll class when already open', () => {
      document.getElementById('nav-button').click(); // close
      const count = Array.from(document.body.classList).filter(c => c === 'prevent-scroll').length;
      expect(count).toBeLessThanOrEqual(1);
    });

    it('removes prevent-scroll after transitionend fires on SiteNav when closed', () => {
      document.getElementById('nav-button').click(); // close
      fireTransitionEnd(document.getElementById('SiteNav'));
      expect(document.body.classList.contains('prevent-scroll')).toBe(false);
    });

    it('keeps prevent-scroll if transitionend fires while nav is still open', () => {
      // Nav is open (from beforeEach), don't close — fire transitionend anyway
      fireTransitionEnd(document.getElementById('SiteNav'));
      expect(document.body.classList.contains('prevent-scroll')).toBe(true);
    });

  });

  describe('Unrelated interactions', () => {

    it('does nothing when clicking an element with no data-jb-action', () => {
      document.getElementById('other-element').click();
      expect(document.body.classList.contains('site-nav-open')).toBe(false);
      expect(document.body.classList.contains('prevent-scroll')).toBe(false);
    });

    it('does not remove prevent-scroll when transitionend fires on a non-nav element', () => {
      document.getElementById('nav-button').click(); // open
      document.getElementById('nav-button').click(); // close — prevent-scroll still set
      fireTransitionEnd(document.getElementById('other-element'));
      expect(document.body.classList.contains('prevent-scroll')).toBe(true);
    });

  });

});
