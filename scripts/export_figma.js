// Run in a Figma plugin context; supply the current repository manifest object.
function countFedoraComponentPairs(pages) {
  return pages.reduce((count, page) => count + page.findAll(node =>
    node.type === "COMPONENT_SET" &&
    node.variantGroupProperties.Size?.values.includes("24") &&
    node.variantGroupProperties.Style?.values.includes("Regular") &&
    node.variantGroupProperties.Style?.values.includes("Filled")
  ).length, 0);
}

async function exportFedoraIcons(manifest) {
  if (manifest.grid !== 24 || manifest.iconCount !== manifest.icons.length) {
    throw new Error("Invalid 24px manifest");
  }
  const page = await figma.getNodeByIdAsync("35:142772");
  if (!page || page.type !== "PAGE") {
    throw new Error("Open the Fedora Icons source file");
  }
  const rightEdge = Math.max(0, ...page.children.map(node => node.x + node.width));
  const section = figma.createSection();
  page.appendChild(section);
  section.name = "Temporary SVG export";
  section.x = rightEdge + 200;
  section.y = 0;
  try {
    const sheet = figma.createFrame();
    section.appendChild(sheet);
    sheet.name = "Export";
    sheet.fills = [];
    sheet.clipsContent = false;
    const columns = 20;
    const height = Math.ceil(manifest.icons.length * manifest.styles.length / columns) * 32;
    sheet.resize(columns * 32, height);
    section.resizeWithoutConstraints(columns * 32 + 32, height + 32);
    const records = [];
    let index = 0;
    for (const icon of manifest.icons) {
      if (manifest.source.excludedBrands.includes(icon.name)) {
        throw new Error(`Excluded brand in core: ${icon.name}`);
      }
      const { files, sha256, ...metadata } = icon;
      const record = { ...metadata, positions: {} };
      for (const style of manifest.styles) {
        const source = await figma.getNodeByIdAsync(icon.source[style]);
        if (source?.type !== "COMPONENT" || source.width !== 24 ||
            source.height !== 24 || source.parent.id !== icon.componentSet ||
            source.parent.name !== icon.name) {
          throw new Error(`Source no longer matches manifest: ${icon.name}/${style}`);
        }
        if (style === "regular") {
          record.keyline = JSON.parse(source.getPluginData("keyline24"));
        }
        if (["duocolor", "duotone"].includes(style) && icon.composition) continue;
        const clone = source.clone();
        sheet.appendChild(clone);
        clone.name = `export--${style}--${icon.name}`;
        clone.x = (index % columns) * 32;
        clone.y = Math.floor(index / columns) * 32;
        index++;
        record.positions[style] = { x: clone.x, y: clone.y, id: clone.name };
        if (["duocolor", "duotone"].includes(style)) {
          for (const node of [clone, ...clone.findAll(n => "fills" in n || "strokes" in n)]) {
            for (const field of ["fills", "strokes"]) {
              if (!Array.isArray(node[field])) continue;
              node[field] = node[field].map(paint => {
                if (paint.type !== "SOLID" || paint.visible === false || paint.opacity === 0) return paint;
                const variable = paint.boundVariables?.color?.id;
                const color = variable === "VariableID:48:36636" ? "#123456" :
                  variable === "VariableID:48:36637" ? "#654321" : null;
                if (!color) throw new Error(`Unknown duo paint: ${icon.name}/${style}`);
                const channels = color.slice(1).match(/../g).map(x => parseInt(x, 16) / 255);
                const { boundVariables, ...literal } = paint;
                return { ...literal, color: { r: channels[0], g: channels[1], b: channels[2] } };
              });
            }
          }
        }
      }
      records.push(record);
    }
    const svg = await sheet.exportAsync({
      format: "SVG_STRING",
      svgIdAttribute: true,
      svgSimplifyStroke: false,
    });
    const brandPages = figma.root.children.filter(node => node.name === "Brands");
    for (const brandPage of brandPages) await brandPage.loadAsync();
    const componentPairs = countFedoraComponentPairs([page, ...brandPages]);
    return {
      records,
      svg,
      styles: manifest.styles,
      paintRoles: { primary: "#123456", secondary: "#654321" },
      componentPairs,
      exportedOn: new Date().toISOString().slice(0, 10),
    };
  } finally {
    section.remove();
  }
}
