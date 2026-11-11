async function exportFedoraPresets() {
  const section = await figma.getNodeByIdAsync("49:47102");
  if (!section) throw new Error("Missing named preset section");
  const state = JSON.parse(section.getPluginData("namedPresetMigration"));
  for (const preset of state.records) {
    for (const [style, id] of Object.entries(preset.source)) {
      const component = await figma.getNodeByIdAsync(id);
      if (component?.type !== "COMPONENT" ||
          component.width !== 24 || component.height !== 24 ||
          component.children.length !== 1) {
        throw new Error(`Invalid named preset: ${preset.name}/${style}`);
      }
      const wrapper = component.children[0];
      const base = wrapper.findOne(n => n.type === "INSTANCE" &&
        n.parent.name === "Masked base / transparent clearance");
      const badge = wrapper.children.find(n => n.type === "INSTANCE");
      const label = Object.keys(state.badges).find(
        name => name.toLowerCase().replaceAll(" ", "-") === preset.modifier,
      );
      if (!base || !badge || !wrapper.findOne(n => n.isMask) ||
          (await base.getMainComponentAsync()).id !== state.base[preset.base][style] ||
          (await badge.getMainComponentAsync()).id !== state.badges[label] ||
          Math.abs(base.width - 24 * (preset.fit?.scale ?? 1)) > 0.015 ||
          component.parent.id !== preset.componentSet) {
        throw new Error(`Named preset composition changed: ${preset.name}/${style}`);
      }
    }
  }
  return {
    schemaVersion: 1,
    source: {
      type: "figma",
      fileKey: "5zcUV9E4Bu8FSssDfhyOWw",
      section: section.id,
      exportedOn: new Date().toISOString().slice(0, 10),
    },
    audit: state.audit,
    baseSources: state.base,
    presets: state.records,
  };
}

// Run in the Fedora Icons plugin context, then save the returned JSON snapshot.
async function exportFedoraModifiers() {
  const sections = {
    actions: "48:40523",
    extended: "48:45301",
    files: "48:44405",
    presets: "49:47102",
  };
  const load = async (id, key) => {
    const node = await figma.getNodeByIdAsync(id);
    if (!node) throw new Error(`Missing modifier source section: ${id}`);
    return JSON.parse(node.getPluginData(key));
  };
  const actions = await load(sections.actions, "modifierProof");
  const extended = await load(sections.extended, "extendedModifierProof");
  const files = await load(sections.files, "fileTypeProof");
  const presets = await load(sections.presets, "namedPresetMigration");
  const collection = await figma.variables.getVariableCollectionByIdAsync(
    "VariableCollectionId:1:1427",
  );
  const variables = await figma.variables.getLocalVariablesAsync("COLOR");
  const warning = variables.find(v => v.name === "color/modifier-warning");
  const hex = color => {
    if (!color || !("r" in color)) throw new Error("Unresolved modifier color");
    return "#" + ["r", "g", "b"].map(
      key => Math.round(color[key] * 255).toString(16).padStart(2, "0"),
    ).join("").toUpperCase();
  };
  const definitions = [
    ["Add", actions, "actions", "Top left", "VariableID:48:40521"],
    ["Delete", actions, "actions", "Bottom right", "VariableID:48:40522"],
    ["Warning", extended, "status", null, warning?.id],
    ["Check", extended, "status", null, "VariableID:48:40521"],
    ...["Key", "Lock", "User", "Clip"].map(
      name => [name, extended, "access-identity", null, "VariableID:48:36636"],
    ),
    ...Object.keys(files.badges).map(
      name => [name, files, "file-types", "Bottom left", "VariableID:48:36636"],
    ),
    ...Object.entries(presets.glyphVariables).map(
      ([name, variable]) => [name, presets, "actions", null, variable],
    ),
  ];
  const page = await figma.getNodeByIdAsync("35:142772");
  const section = figma.createSection();
  page.appendChild(section);
  section.name = "Temporary modifier export";
  section.x = 9064;
  section.y = 0;
  section.resizeWithoutConstraints(64, 64);
  const records = [];
  try {
    for (const [label, proof, group, defaultPosition, colorId] of definitions) {
      const sourceId = proof.badges[label];
      const source = await figma.getNodeByIdAsync(sourceId);
      if (source?.type !== "COMPONENT") {
        throw new Error(`Missing native modifier component: ${label}`);
      }

      const instance = source.createInstance();
      section.appendChild(instance);
      instance.x = instance.y = 8;
      try {
        const colors = {};
        const primary = await figma.variables.getVariableByIdAsync(colorId);
        const glyph = await figma.variables.getVariableByIdAsync("VariableID:1:1428");
        for (const [theme, mode] of [["light", "1:0"], ["dark", "1:1"]]) {
          instance.setExplicitVariableModeForCollection(collection, mode);
          colors[theme] = {
            primary: hex(primary.resolveForConsumer(instance).value),
            glyph: hex(glyph.resolveForConsumer(instance).value),
          };
        }

        instance.setExplicitVariableModeForCollection(collection, "1:0");
        const paintRoles = { primary: "#123456", glyph: "#FEDCBA" };
        for (const node of instance.findAll(n => "fills" in n || "strokes" in n)) {
          for (const attr of ["fills", "strokes"]) {
            if (!Array.isArray(node[attr])) continue;
            node[attr] = node[attr].map(paint => {
              if (paint.type !== "SOLID") return paint;
              const variable = paint.boundVariables?.color?.id;
              const role = variable === "VariableID:1:1428" ? "glyph" : "primary";
              if (role === "primary" && variable !== colorId) {
                throw new Error(`Unrecognized modifier paint binding: ${label}`);
              }
              const rgb = paintRoles[role].slice(1).match(/../g).map(
                channel => parseInt(channel, 16) / 255,
              );
              const { boundVariables, ...literal } = paint;
              return { ...literal, color: { r: rgb[0], g: rgb[1], b: rgb[2] } };
            });
          }
        }
        const positions = {};
        const allowed = group === "file-types"
          ? ["Bottom left"]
          : ["Top left", "Top right", "Bottom left", "Bottom right"];
        for (const position of allowed) {
          const wrapper = await figma.getNodeByIdAsync(proof.variants[label][position]);
          const mask = wrapper.findOne(n => n.isMask);
          const badge = wrapper.children.find(n => n.type === "INSTANCE");
          if (!mask || mask.type !== "VECTOR" ||
              [mask.x, mask.y, mask.width - 24, mask.height - 24].some(
                value => Math.abs(value) > 0.015,
              ) || mask.strokes.length ||
              !badge || (await badge.getMainComponentAsync()).id !== sourceId) {
            throw new Error(`Invalid composition geometry: ${label}/${position}`);
          }
          positions[position.toLowerCase().replaceAll(" ", "-")] = {
            x: badge.x,
            y: badge.y,
            clearance: mask.vectorPaths,
          };
        }
        records.push({
          name: label.toLowerCase().replaceAll(" ", "-"),
          label,
          group,
          source: sourceId,
          sourceGlyph: proof.sources?.[label] ?? null,
          width: source.width,
          height: source.height,
          defaultPosition: defaultPosition?.toLowerCase().replaceAll(" ", "-") ?? null,
          ...(group === "file-types" ? { allowedPositions: ["bottom-left"] } : {}),
          clearance: 1.25,
          colors,
          paintRoles,
          positions,
          svg: await instance.exportAsync({
            format: "SVG_STRING",
            svgSimplifyStroke: false,
          }),
        });
      } finally {
        instance.remove();
      }
    }
    return {
      schemaVersion: 1,
      source: {
        type: "figma",
        fileKey: "5zcUV9E4Bu8FSssDfhyOWw",
        sections,
        exportedOn: new Date().toISOString().slice(0, 10),
      },
      records,
    };
  } finally {
    section.remove();
  }
}
