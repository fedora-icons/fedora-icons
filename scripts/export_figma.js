// Run in a Figma plugin context; supply the current repository manifest object.
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
    const height = Math.ceil(manifest.icons.length * 2 / columns) * 32;
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
        const clone = source.clone();
        sheet.appendChild(clone);
        clone.name = `export--${style}--${icon.name}`;
        clone.x = (index % columns) * 32;
        clone.y = Math.floor(index / columns) * 32;
        index++;
        record.positions[style] = { x: clone.x, y: clone.y, id: clone.name };
      }
      records.push(record);
    }
    const svg = await sheet.exportAsync({
      format: "SVG_STRING",
      svgIdAttribute: true,
      svgSimplifyStroke: false,
    });
    const componentPairs = page.findAll(node => node.type === "COMPONENT_SET" &&
      node.variantGroupProperties.Size?.values.includes("24") &&
      node.variantGroupProperties.Style?.values.includes("Regular") &&
      node.variantGroupProperties.Style?.values.includes("Filled")).length;
    return {
      records,
      svg,
      componentPairs,
      exportedOn: new Date().toISOString().slice(0, 10),
    };
  } finally {
    section.remove();
  }
}
