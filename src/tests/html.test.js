import { describe, it, expect, beforeAll } from 'vitest';
import { readFileSync } from 'fs';
import path from 'path';

let html;

beforeAll(() => {
  html = readFileSync(path.resolve(process.cwd(), 'index.html'), 'utf-8');
});

describe('HTML', () => {

  describe('Head — essentials', () => {

    it('has a title tag', () => {
      expect(html).toMatch(/<title>.+<\/title>/);
    });

    it('has a charset meta tag', () => {
      expect(html).toMatch(/meta[^>]+charset/i);
    });

    it('has a viewport meta tag', () => {
      expect(html).toMatch(/meta[^>]+viewport/i);
    });

    it('has a description meta tag with content', () => {
      expect(html).toMatch(/meta[^>]+name="description"[^>]+content="[^"]+"/);
    });

  });

  describe('Head — Open Graph', () => {

    it('has og:title', () => {
      expect(html).toMatch(/property="og:title"/);
    });

    it('has og:description', () => {
      expect(html).toMatch(/property="og:description"/);
    });

    it('has og:type', () => {
      expect(html).toMatch(/property="og:type"/);
    });

  });

  describe('Head — assets', () => {

    it('loads Google Fonts over HTTPS', () => {
      expect(html).not.toMatch(/http:\/\/fonts\.googleapis\.com/);
      expect(html).toMatch(/https:\/\/fonts\.googleapis\.com/);
    });

    it('has a favicon link', () => {
      expect(html).toMatch(/favicon\.ico/);
    });

  });

  describe('Navigation', () => {

    it('has #SiteNav with data-jb-transition attribute', () => {
      expect(html).toMatch(/id="SiteNav"/);
      expect(html).toMatch(/data-jb-transition="SiteNav"/);
    });

    it('has nav button with data-jb-action="OpenSiteNav"', () => {
      expect(html).toMatch(/data-jb-action="OpenSiteNav"/);
    });

    it('has About and Contact nav links', () => {
      expect(html).toMatch(/href="#about"/);
      expect(html).toMatch(/href="#contact"/);
    });

  });

  describe('Body structure', () => {

    it('has #Body wrapper', () => {
      expect(html).toMatch(/id="Body"/);
    });

    it('has #Header section', () => {
      expect(html).toMatch(/id="Header"/);
    });

    it('has the main tagline', () => {
      expect(html).toMatch(/Draw\s*\.\s*Design\s*\.\s*Code/);
    });

    it('has collapse overlay element', () => {
      expect(html).toMatch(/class="collapse-overlay/);
    });

  });

  describe('Scripts', () => {

    it('loads main.js as an ES module', () => {
      expect(html).toMatch(/type="module"[^>]+src="\/src\/js\/main\.js"/);
    });

    it('does not load jQuery', () => {
      expect(html).not.toMatch(/jquery/i);
    });

    it('does not load AngularJS', () => {
      expect(html).not.toMatch(/angular/i);
    });

  });

});
