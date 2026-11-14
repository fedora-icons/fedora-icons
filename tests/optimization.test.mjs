import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { optimizeLibrary, optimizeSvg } from '../scripts/optimize.mjs';
import { assertVisualParity, renderPixels } from '../scripts/svg_parity.mjs';

const fixture = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
<!-- removable metadata -->
<defs>
  <mask id="fos-fixture-mask" mask-type="luminance">
    <rect width="24" height="24" fill="white"/>
    <circle cx="12" cy="12" r="4" fill="black"/>
  </mask>
  <clipPath id="fos-fixture-clip"><rect width="24" height="24"/></clipPath>
</defs>
<g><g mask="url(#fos-fixture-mask)" clip-path="url(#fos-fixture-clip)">
  <g opacity="0.16"><path d="M2 2H22V22H2Z" fill="var(--fos-secondary, #5B87B7)"/></g>
</g></g>
<svg x="2" y="2" width="20" height="20" viewBox="0 0 24 24" fill="none">
  <path d="M2 2H22V22H2Z" stroke="currentColor" stroke-width="1.5"/>
</svg>
</svg>`;

test('optimization preserves masks, cutouts, roles, tints, and optical viewports exactly', () => {
  const optimized = optimizeSvg(fixture);
  assert.ok(optimized.length < fixture.length);
  assert.equal(optimizeSvg(optimized), optimized);
  assert.doesNotMatch(optimized, /removable metadata/);
  for (const fragment of [
    'viewBox="0 0 24 24"', 'width="24"', 'height="24"',
    'id="fos-fixture-mask"', 'mask="url(#fos-fixture-mask)"',
    'clip-path="url(#fos-fixture-clip)"', 'mask-type="luminance"',
    'fill="white"', 'fill="black"', 'opacity="0.16"',
    'var(--fos-secondary, #5B87B7)', 'stroke="currentColor"',
    'stroke-width="1.5"', 'width="20"', 'height="20"', 'd="M2 2H22V22H2Z"',
  ]) assert.ok(optimized.includes(fragment), fragment);
  assertVisualParity(fixture, optimized, 'semantic fixture');
  const pixels = renderPixels(optimized, 'light', 24);
  assert.equal(pixels[(12 * 24 + 12) * 4 + 3], 0, 'cutout must remain transparent');
  assert.ok(pixels[(5 * 24 + 5) * 4 + 3] > 0, 'tint must remain visible');
});

test('pixel parity gate detects geometry and tint regressions', () => {
  assert.throws(() => assertVisualParity(fixture,
    fixture.replace('r="4"', 'r="2"'), 'cutout'), /Visual change/);
  assert.throws(() => assertVisualParity(fixture,
    fixture.replace('opacity="0.16"', 'opacity="1"'), 'tint'), /Visual change/);
});

test('library optimization refreshes both hash contracts; check mode never writes', async t => {
  const root = await mkdtemp(join(tmpdir(), 'fos-svgo-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(join(root, 'icons/regular'), { recursive: true });
  await mkdir(join(root, 'modifiers'));
  await mkdir(join(root, 'metadata'));
  const iconPath = join(root, 'icons/regular/fixture.svg');
  const modifierPath = join(root, 'modifiers/fixture.svg');
  const manifestPath = join(root, 'manifest.json');
  const metadataPath = join(root, 'metadata/modifiers.json');
  await writeFile(iconPath, fixture);
  await writeFile(modifierPath, fixture);
  await writeFile(manifestPath, JSON.stringify({
    styles: ['regular'],
    icons: [{ name: 'fixture', files: { regular: 'icons/regular/fixture.svg' },
      sha256: { regular: 'stale' } }],
  }));
  await writeFile(metadataPath, JSON.stringify({
    modifiers: [{ name: 'fixture', file: 'modifiers/fixture.svg', sha256: 'stale' }],
  }));
  const paths = [iconPath, modifierPath, manifestPath, metadataPath];
  const before = await Promise.all(paths.map(path => readFile(path)));
  await assert.rejects(optimizeLibrary(root, { check: true }), /Optimization\/hash drift/);
  assert.deepEqual(await Promise.all(paths.map(path => readFile(path))), before);
  const report = await optimizeLibrary(root);
  assert.equal(report.assets, 2);
  assert.equal(report.changed, 2);
  assert.ok(report.bytesAfter < report.bytesBefore);
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  const modifiers = JSON.parse(await readFile(metadataPath, 'utf8'));
  const sha256 = value => createHash('sha256').update(value).digest('hex');
  assert.equal(manifest.icons[0].sha256.regular, sha256(await readFile(iconPath)));
  assert.equal(modifiers.modifiers[0].sha256, sha256(await readFile(modifierPath)));
  const optimized = await Promise.all(paths.map(path => readFile(path)));
  assert.equal((await optimizeLibrary(root, { check: true })).changed, 0);
  assert.equal((await optimizeLibrary(root)).changed, 0);
  assert.deepEqual(await Promise.all(paths.map(path => readFile(path))), optimized);
  manifest.icons[0].sha256.regular = 'tampered';
  await writeFile(manifestPath, JSON.stringify(manifest));
  await assert.rejects(optimizeLibrary(root, { check: true }), /Optimization\/hash drift/);
});
