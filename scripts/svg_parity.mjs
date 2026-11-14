import { Resvg } from '@resvg/resvg-js';

const palettes = {
  light: { primary: '#245B9E', secondary: '#5B87B7', modifier: '#0F7B0F', 'glyph-color': '#FFFFFF' },
  dark: { primary: '#93C5FD', secondary: '#60A5FA', modifier: '#6CCB5F', 'glyph-color': '#141414' },
  custom: { primary: '#B42370', secondary: '#17A398', modifier: '#E07800', 'glyph-color': '#49328A' },
};

function resolvePaints(svg, theme) {
  const colors = palettes[theme];
  svg = svg.replace(/<\?xml[\s\S]*?\?>/g, '');
  // resvg does not resolve CSS custom properties; exercise every public role.
  while (svg.includes('var(')) {
    const next = svg.replace(/var\(--fos-([\w-]+),\s*([^()]*)\)/g,
      (match, role, fallback) => colors[role] ?? fallback.trim());
    if (next === svg) throw new Error('Unresolved CSS variable in render fixture');
    svg = next;
  }
  const color = theme === 'dark' ? '#F3F3F3' : '#212121';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" color="${color}">${svg}</svg>`;
}

export function renderPixels(svg, theme, size) {
  return new Resvg(resolvePaints(svg, theme), {
    fitTo: { mode: 'width', value: size },
    font: { loadSystemFonts: false },
  }).render().pixels;
}

export function assertVisualParity(before, after, label) {
  for (const theme of Object.keys(palettes)) {
    for (const size of [24, 48]) {
      if (!renderPixels(before, theme, size).equals(renderPixels(after, theme, size))) {
        throw new Error(`Visual change: ${label} (${theme}, ${size}px)`);
      }
    }
  }
}
