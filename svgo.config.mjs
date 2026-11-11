export default {
  multipass: true,
  js2svg: { pretty: false },
  // Deliberately omit numeric, path, transform, color, ID, and viewport rewrites.
  plugins: [
    'removeDoctype',
    'removeXMLProcInst',
    'removeComments',
    'removeMetadata',
    'removeEditorsNSData',
    'cleanupAttrs',
    'removeEmptyAttrs',
    'removeEmptyText',
    'removeEmptyContainers',
    'collapseGroups',
    'sortAttrs',
  ],
};
