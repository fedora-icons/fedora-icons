// Run in the source file's plugin context, then call buildFosDuoBatch().
async function buildFosDuoBatch(limit = 50) {
  const core = await figma.getNodeByIdAsync("45:36965");
  const proof = JSON.parse((await figma.getNodeByIdAsync("48:36638")).getPluginData("duoProof"));
  const presets = JSON.parse((await figma.getNodeByIdAsync("49:47102")).getPluginData("namedPresetMigration"));
  const excluded = new Set(["chrome-cast", "figma", "framer", "google-chrome", "youtube"]);
  const primary = await figma.variables.getVariableByIdAsync(proof.primary);
  const secondary = await figma.variables.getVariableByIdAsync(proof.secondary);
  const paint = variable => figma.variables.setBoundVariableForPaint(
    { type: "SOLID", color: { r: 0.14, g: 0.36, b: 0.62 } }, "color", variable,
  );
  const bind = (node, variable) => {
    for (const field of ["fills", "strokes"]) {
      if (Array.isArray(node[field])) node[field] = node[field].map(p =>
        p.type === "SOLID" ? { ...paint(variable), opacity: p.opacity, visible: p.visible } : p);
    }
  };
  const paths = vector => vector.vectorPaths.flatMap(p =>
    (p.data.match(/M[^M]*/g) || []).map(data => ({ ...p, data: data.trim() })));
  const visible = (node, root) => {
    for (let p = node; p && p !== root; p = p.parent) if (!p.visible) return false;
    return true;
  };
  const score = node => {
    const network = node.vectorNetwork;
    return network.segments.reduce((total, segment) => {
      const a = network.vertices[segment.start], b = network.vertices[segment.end];
      const c = { x: a.x + (segment.tangentStart?.x || 0), y: a.y + (segment.tangentStart?.y || 0) };
      const d = { x: b.x + (segment.tangentEnd?.x || 0), y: b.y + (segment.tangentEnd?.y || 0) };
      let previous = a;
      for (let i = 1; i <= 16; i++) {
        const t = i / 16, u = 1 - t;
        const point = {
          x: u ** 3 * a.x + 3 * u ** 2 * t * c.x + 3 * u * t ** 2 * d.x + t ** 3 * b.x,
          y: u ** 3 * a.y + 3 * u ** 2 * t * c.y + 3 * u * t ** 2 * d.y + t ** 3 * b.y,
        };
        total += Math.hypot(point.x - previous.x, point.y - previous.y);
        previous = point;
      }
      return total;
    }, 0);
  };
  const slash = node => node.vectorNetwork.segments.length === 1 &&
    node.width > 2 && node.height > 8;
  const flatten = root => {
    const old = [...root.children];
    const origin = root.absoluteTransform;
    const snapshots = root.findAll(n => n.type === "VECTOR" && visible(n, root)).map(node => ({
      node, transform: node.absoluteTransform.map(row => [...row]),
    }));
    for (const { node, transform } of snapshots) {
      const clone = node.clone();
      root.appendChild(clone);
      clone.relativeTransform = [
        [transform[0][0], transform[0][1], transform[0][2] - origin[0][2]],
        [transform[1][0], transform[1][1], transform[1][2] - origin[1][2]],
      ];
    }
    for (const child of old) child.remove();
  };
  const existing = new Map(proof.records.map(r => [r.name, r]));
  for (const [name, source] of Object.entries(presets.base)) existing.set(name, { name, ...source });
  for (const r of presets.records) existing.set(r.name, { name: r.name, ...r.source });
  const sets = core.findAll(n => n.type === "COMPONENT_SET" && !excluded.has(n.name));
  const output = [];
  for (const set of sets) {
    const saved = JSON.parse(set.getPluginData("duoExpansion") || "null");
    if (saved?.authoringVersion === 2) continue;
    const regular = set.children.find(n => n.variantProperties?.Style === "Regular");
    const filled = set.children.find(n => n.variantProperties?.Style === "Filled");
    if (!regular || !filled) throw new Error(`Missing base styles: ${set.name}`);
    const record = {
      name: set.name, componentSet: set.id,
      source: { regular: regular.id, filled: filled.id },
      authoringVersion: 2,
    };
    const adopted = existing.get(set.name);
    const created = [];
    try {
      for (const style of ["duocolor", "duotone"]) {
        let component;
        if (adopted) {
          component = await figma.getNodeByIdAsync(adopted[style]);
          if (component?.type !== "COMPONENT") throw new Error(`Missing approved ${set.name}/${style}`);
          set.appendChild(component);
          for (const frame of component.findAll(n => n.type === "FRAME" && Math.abs(n.opacity - 0.16) < 0.001)) {
            frame.blendMode = "NORMAL";
          }
        } else {
          component = regular.clone();
          created.push(component);
          set.appendChild(component);
          flatten(component);
          if (style === "duocolor") {
            const units = [];
            for (const v of component.findAll(n => n.type === "VECTOR" && !n.isMask)) {
              if (!visible(v, component)) continue;
              const subpaths = paths(v);
              const hasFill = v.fills.some(p => p.visible !== false && p.opacity !== 0);
              if (subpaths.length > 1 && !hasFill) {
                for (const path of subpaths) {
                  const part = v.clone();
                  v.parent.appendChild(part);
                  part.vectorPaths = [path];
                  part.strokeCap = typeof v.strokeCap === "string" ? v.strokeCap : "ROUND";
                  part.strokeJoin = typeof v.strokeJoin === "string" ? v.strokeJoin : "ROUND";
                  units.push(part);
                }
                v.remove();
              } else units.push(v);
            }
            const dominant = Math.max(0, ...units.map(score));
            const slashAccent = /-(off|not)$/.test(set.name) && units.some(slash);
            let accents = 0;
            for (const n of units) {
              const accent = slashAccent ? slash(n) :
                units.length > 1 && score(n) < dominant * 0.62;
              bind(n, accent ? secondary : primary);
              n.setPluginData("duoPaintRole", accent ? "secondary" : "primary");
              accents += Number(accent);
            }
            record.duocolor = { contours: units.length, accents, policy: "dominant-contours-and-details" };
          } else {
            for (const n of component.findAll(n => n.type === "VECTOR" && !n.isMask)) bind(n, primary);
            const instance = regular.createInstance();
            component.insertChild(0, instance);
            instance.x = 0;
            instance.y = 0;
            const tint = instance.detachInstance();
            flatten(tint);
            tint.name = "Tint / closed contours only / 16%";
            tint.fills = [];
            tint.opacity = 0.16;
            tint.blendMode = "NORMAL";
            let regions = 0;
            for (const v of tint.findAll(n => n.type === "VECTOR" && !n.isMask)) {
              if (!visible(v, tint)) continue;
              const hasFill = v.fills.some(p => p.visible !== false && p.opacity !== 0);
              const closed = paths(v).filter(p => /[zZ]\s*$/.test(p.data));
              if (!closed.length && !hasFill) {
                v.remove();
                continue;
              }
              if (!hasFill) {
                v.vectorPaths = [{ windingRule: "EVENODD", data: closed.map(p => p.data).join(" ") }];
              }
              v.fills = [paint(primary)];
              v.strokes = [];
              regions += hasFill ? 1 : closed.length;
            }
            if (!regions) tint.remove();
            record.duotone = { regions, opacity: 0.16, policy: "explicit-closed-contours" };
          }
          if (saved) {
            const original = await figma.getNodeByIdAsync(saved.source[style]);
            const old = [...original.children];
            for (const child of [...component.children]) {
              const transform = child.relativeTransform;
              original.appendChild(child);
              child.relativeTransform = transform;
            }
            for (const child of old) child.remove();
            component.remove();
            component = original;
          }
        }
        component.name = `Style=${style === "duocolor" ? "Duocolor" : "Duotone"}, Size=24`;
        component.x = style === "duocolor" ? 16 : 64;
        component.y = 68;
        if (component.width !== 24 || component.height !== 24) throw new Error(`Invalid dimensions: ${set.name}/${style}`);
        record.source[style] = component.id;
      }
      record.approvedPrototype = Boolean(adopted);
      set.resizeWithoutConstraints(112, 112);
      set.setPluginData("duoExpansion", JSON.stringify(record));
      output.push(record);
    } catch (error) {
      for (const node of created) if (!node.removed) node.remove();
      throw error;
    }
    if (output.length >= limit) break;
  }
  let y = 48;
  for (const family of core.children.filter(n => n.type === "FRAME")) {
    const children = family.children.filter(n => n.type === "COMPONENT_SET");
    children.forEach((set, i) => { set.x = 16 + (i % 10) * 128; set.y = 32 + Math.floor(i / 10) * 136; });
    family.resize(1312, 48 + Math.ceil(children.length / 10) * 136);
    family.y = y;
    y += family.height + 48;
  }
  core.resizeWithoutConstraints(1360, y);
  const done = sets.filter(n =>
    JSON.parse(n.getPluginData("duoExpansion") || "null")?.authoringVersion === 2).length;
  core.setPluginData("fourStyleExpansion", JSON.stringify({
    schemaVersion: 1, total: sets.length, done, singleContourDuocolor: "primary-only",
    tintOpacity: 0.16, tintBlendMode: "NORMAL",
  }));
  return { processed: output.length, done, total: sets.length, records: output };
}
