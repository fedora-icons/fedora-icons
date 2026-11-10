// Run in the source file's plugin context, then save exportFedoraDuo() as JSON.
async function exportFedoraDuo() {
  const core = await figma.getNodeByIdAsync("45:36965");
  const state = JSON.parse((await figma.getNodeByIdAsync("48:36638")).getPluginData("duoProof"));
  const presetState = JSON.parse((await figma.getNodeByIdAsync("49:47102")).getPluginData("namedPresetMigration"));
  const presetNames = new Set(presetState.records.map(r => r.name));
  const sets = core.findAll(n => n.type === "COMPONENT_SET" && n.getPluginData("duoExpansion"));
  if (sets.length !== 1228) throw new Error("Incomplete native expansion");
  const roles = { primary: "#123456", secondary: "#654321" };
  const section = figma.createSection();
  (await figma.getNodeByIdAsync("35:142772")).appendChild(section);
  section.name = "Temporary duo export";
  section.x = 9064;
  section.y = 0;
  section.resizeWithoutConstraints(704, 4000);
  try {
    const sheet = figma.createFrame();
    section.appendChild(sheet);
    sheet.name = "Duo export";
    sheet.fills = [];
    sheet.clipsContent = false;
    sheet.resize(640, 4000);
    const records = [];
    let index = 0;
    for (const set of sets) {
      const authored = JSON.parse(set.getPluginData("duoExpansion"));
      if (authored.authoringVersion !== 2) throw new Error(`Stale duo geometry: ${set.name}`);
      const record = {
        name: set.name, componentSet: set.id, source: authored.source,
        duoAuthoring: {
          version: 2, approvedPrototype: authored.approvedPrototype,
          duocolor: authored.duocolor, duotone: authored.duotone,
        },
        positions: {},
      };
      for (const style of ["regular", "filled", "duocolor", "duotone"]) {
        const source = await figma.getNodeByIdAsync(record.source[style]);
        if (source?.type !== "COMPONENT" || source.parent.id !== set.id ||
            source.width !== 24 || source.height !== 24 ||
            source.variantProperties?.Style?.toLowerCase() !== style) {
          throw new Error(`Source identity mismatch: ${set.name}/${style}`);
        }
        if (["regular", "filled"].includes(style) || presetNames.has(set.name)) continue;
        const clone = source.clone();
        sheet.appendChild(clone);
        clone.name = `export--${style}--${set.name}`;
        clone.x = (index % 20) * 32;
        clone.y = Math.floor(index / 20) * 32;
        index++;
        record.positions[style] = { x: clone.x, y: clone.y, id: clone.name };
        for (const node of [clone, ...clone.findAll(n => "fills" in n || "strokes" in n)]) {
          for (const field of ["fills", "strokes"]) {
            if (!Array.isArray(node[field])) continue;
            node[field] = node[field].map(paint => {
              if (paint.type !== "SOLID" || paint.visible === false || paint.opacity === 0) return paint;
              const variable = paint.boundVariables?.color?.id;
              const role = variable === state.primary ? "primary" :
                variable === state.secondary ? "secondary" : null;
              if (!role) throw new Error(`Unrecognized ${set.name}/${style} paint: ${variable}`);
              const channels = roles[role].slice(1).match(/../g).map(x => parseInt(x, 16) / 255);
              const { boundVariables, ...literal } = paint;
              return { ...literal, color: { r: channels[0], g: channels[1], b: channels[2] } };
            });
          }
        }
      }
      records.push(record);
    }
    const svg = await sheet.exportAsync({
      format: "SVG_STRING", svgIdAttribute: true, svgSimplifyStroke: false,
    });
    const collection = await figma.variables.getVariableCollectionByIdAsync("VariableCollectionId:1:1427");
    const palette = [];
    for (const preset of state.palette) {
      const current = { ...preset };
      for (const [theme, mode] of [["light", "1:0"], ["dark", "1:1"]]) {
        sheet.setExplicitVariableModeForCollection(collection, mode);
        current[theme] = {};
        for (const role of ["primary", "secondary"]) {
          const value = (await figma.variables.getVariableByIdAsync(preset[role])).resolveForConsumer(sheet).value;
          current[theme][role] = "#" + ["r", "g", "b"].map(
            channel => Math.round(value[channel] * 255).toString(16).padStart(2, "0"),
          ).join("").toUpperCase();
        }
      }
      palette.push(current);
    }
    return {
      records, svg, paintRoles: roles, palette, custom: state.custom,
      exportedOn: new Date().toISOString().slice(0, 10),
    };
  } finally {
    section.remove();
  }
}
