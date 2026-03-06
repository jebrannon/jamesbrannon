import { describe, it, expect, beforeAll } from 'vitest';
import { execSync } from 'child_process';
import { existsSync, readdirSync, readFileSync } from 'fs';
import path from 'path';

const projectRoot = process.cwd();
const distDir = path.join(projectRoot, 'dist');

beforeAll(() => {
  execSync('npm run build', { cwd: projectRoot, stdio: 'pipe' });
}, 60000);

describe('Build integrity', () => {

  it('creates the dist directory', () => {
    expect(existsSync(distDir)).toBe(true);
  });

  it('dist contains index.html', () => {
    expect(existsSync(path.join(distDir, 'index.html'))).toBe(true);
  });

  it('dist contains an assets directory', () => {
    expect(existsSync(path.join(distDir, 'assets'))).toBe(true);
  });

  it('dist assets include a CSS file', () => {
    const assets = readdirSync(path.join(distDir, 'assets'));
    expect(assets.some(f => f.endsWith('.css'))).toBe(true);
  });

  it('dist assets include a JS file', () => {
    const assets = readdirSync(path.join(distDir, 'assets'));
    expect(assets.some(f => f.endsWith('.js'))).toBe(true);
  });

  it('built index.html references the hashed CSS and JS assets', () => {
    const content = readFileSync(path.join(distDir, 'index.html'), 'utf-8');
    expect(content).toMatch(/\.css/);
    expect(content).toMatch(/\.js/);
  });

});
