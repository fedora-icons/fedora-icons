import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { renderPixels } from '../scripts/svg_parity.mjs';

const icon = (style, name) => readFile(
  new URL(`../icons/${style}/${name}.svg`, import.meta.url), 'utf8',
);

function commands(path) {
  const tokens = path.match(/[MLCZ]|[-+]?(?:\d*\.?\d+)(?:e[-+]?\d+)?/gi);
  const result = [];
  for (let i = 0; i < tokens.length;) {
    const command = tokens[i++];
    const length = { M: 2, L: 2, C: 6, Z: 0 }[command];
    assert.notEqual(length, undefined, `Unexpected command ${command}`);
    result.push({ command, values: tokens.slice(i, i += length).map(Number) });
  }
  return result;
}

test('image hill endpoints meet the frame centerline with rounded joins', async () => {
  for (const style of ['regular', 'duocolor', 'duotone']) {
    const svg = await icon(style, 'image');
    const paths = [...svg.matchAll(/<path\b[^>]*>/g)]
      .map(match => match[0]).filter(path => /\bstroke=/.test(path));
    const border = commands(paths[0].match(/\bd="([^"]+)"/)[1]);
    const hill = commands(paths.at(-1).match(/\bd="([^"]+)"/)[1]);
    const samples = [];
    let start = border[0].values;
    for (const { command, values: a } of border.slice(1)) {
      if (command !== 'C') continue;
      for (let i = 0; i <= 4096; i++) {
        const t = i / 4096, u = 1 - t;
        samples.push([0, 1].map(axis =>
          u ** 3 * start[axis] + 3 * u ** 2 * t * a[axis]
          + 3 * u * t ** 2 * a[axis + 2] + t ** 3 * a[axis + 4]));
      }
      start = a.slice(4);
    }
    for (const endpoint of [hill[0].values, hill.at(-1).values.slice(-2)]) {
      const gap = Math.min(...samples.map(point =>
        Math.hypot(point[0] - endpoint[0], point[1] - endpoint[1])));
      assert.ok(gap < 0.01, `${style}: hill endpoint is ${gap}px from frame`);
    }
    assert.match(paths.at(-1), /stroke-linecap="round"/);
    assert.match(paths.at(-1), /stroke-linejoin="round"/);
  }
});

test('head-profile Duocolor has a transparent interior and secondary-color ear', async () => {
  const svg = await icon('duocolor', 'head-profile');
  const size = 240;
  const pixels = renderPixels(svg, 'custom', size);
  const pixel = (x, y) => [...pixels.subarray(
    (Math.floor(y * 10) * size + Math.floor(x * 10)) * 4,
    (Math.floor(y * 10) * size + Math.floor(x * 10)) * 4 + 4,
  )];
  assert.equal(pixel(14, 8)[3], 0, 'head interior must not be filled');
  assert.deepEqual(pixel(10.55, 11), [23, 163, 152, 255], 'ear uses secondary color');
});
