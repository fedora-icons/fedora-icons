import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { optimize } from 'svgo';
import config from '../svgo.config.mjs';
import { assertVisualParity } from './svg_parity.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const digest = value => createHash('sha256').update(value).digest('hex');
const json = value => `${JSON.stringify(value, null, 2)}\n`;

export function optimizeSvg(svg, path = 'icon.svg') {
  return `${optimize(svg, { ...config, path }).data.trimEnd()}\n`;
}

export async function optimizeLibrary(root = ROOT, { check = false } = {}) {
  root = resolve(root);
  const manifestPath = resolve(root, 'manifest.json');
  const modifierPath = resolve(root, 'metadata/modifiers.json');
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  const modifiers = JSON.parse(await readFile(modifierPath, 'utf8'));
  const assets = [];
  for (const row of manifest.icons) {
    for (const style of manifest.styles) {
      assets.push({ relative: row.files[style], hashes: row.sha256, key: style });
    }
  }
  for (const row of modifiers.modifiers) {
    assets.push({ relative: row.file, hashes: row, key: 'sha256' });
  }
  assets.sort((a, b) => a.relative.localeCompare(b.relative, 'en'));
  const staged = new Map();
  const drift = [];
  const seen = new Set();
  let bytesBefore = 0;
  let bytesAfter = 0;
  for (const { relative, hashes, key } of assets) {
    const path = resolve(root, relative);
    if (isAbsolute(relative) || !path.startsWith(`${root}${sep}`) || seen.has(path)) {
      throw new Error(`Invalid or duplicate asset path: ${relative}`);
    }
    seen.add(path);
    const before = await readFile(path, 'utf8');
    const after = optimizeSvg(before, relative);
    if (optimizeSvg(after, relative) !== after) {
      throw new Error(`Non-idempotent optimization: ${relative}`);
    }
    bytesBefore += Buffer.byteLength(before);
    bytesAfter += Buffer.byteLength(after);
    const sha256 = digest(after);
    if (before !== after || hashes[key] !== sha256) drift.push(relative);
    if (before !== after) {
      if (!check) assertVisualParity(before, after, relative);
      staged.set(path, after);
    }
    hashes[key] = sha256;
  }
  if (check && drift.length) {
    throw new Error(`Optimization/hash drift in ${drift.length} assets; run npm run optimize.\n${drift.slice(0, 10).join('\n')}`);
  }
  if (!check) {
    for (const [path, content] of [[manifestPath, json(manifest)], [modifierPath, json(modifiers)]]) {
      if (await readFile(path, 'utf8') !== content) staged.set(path, content);
    }
    // Prepare and verify the entire batch before touching canonical assets.
    for (const [path, content] of staged) await writeFile(path, content);
  }
  return { assets: assets.length, changed: drift.length, bytesBefore, bytesAfter };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length !== 1 || !['--write', '--check'].includes(args[0])) {
    console.error('Usage: node scripts/optimize.mjs --write|--check');
    process.exitCode = 1;
  } else {
    try {
      const report = await optimizeLibrary(ROOT, { check: args[0] === '--check' });
      const saved = report.bytesBefore - report.bytesAfter;
      console.log(`${report.assets} SVGs; ${report.changed} changed; ${saved} bytes saved (${(100 * saved / report.bytesBefore).toFixed(2)}%).`);
    } catch (error) {
      console.error(error.message);
      process.exitCode = 1;
    }
  }
}
