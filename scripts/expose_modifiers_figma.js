async function exposeFosModifierProperties() {
  const section = await figma.getNodeByIdAsync("49:47102");
  const state = JSON.parse(section.getPluginData("namedPresetMigration"));
  const updated = [];
  for (const preset of state.records) {
    for (const [style, id] of Object.entries(preset.source)) {
      const component = await figma.getNodeByIdAsync(id);
      const wrapper = component?.children[0];
      if (component?.type !== "COMPONENT" || wrapper?.type !== "INSTANCE") {
        throw new Error(`Missing composition: ${preset.name}/${style}`);
      }
      const main = await wrapper.getMainComponentAsync();
      const owner = main.parent.type === "COMPONENT_SET" ? main.parent : main;
      if (!owner.componentPropertyDefinitions.Modifier &&
          !owner.componentPropertyDefinitions["File type"]) {
        const badge = main.children.find(node => node.type === "INSTANCE");
        if (!badge?.componentProperties.Glyph) {
          throw new Error(`Missing optical-fit modifier: ${preset.name}/${style}`);
        }
        badge.isExposedInstance = true;
      }
      wrapper.name = "Modifier";
      wrapper.isExposedInstance = true;
      updated.push({ name: preset.name, style, component: id, instance: wrapper.id });
    }
  }
  section.setPluginData("exposedModifierProperties", JSON.stringify({
    schemaVersion: 1,
    updated,
  }));
  return updated;
}

// Run in the Fos Icons plugin context.
