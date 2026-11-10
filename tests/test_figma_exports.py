import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is needed to check Figma JavaScript entry points")
class FigmaExportTests(unittest.TestCase):
    def test_documented_exporters_are_callable_in_plugin_scope(self):
        result = subprocess.run(["node", "-e", """
            const fs = require('node:fs');
            const vm = require('node:vm');
            const assert = require('node:assert/strict');
            const scripts = {
                'export_figma.js': ['exportFedoraIcons'],
                'export_duo_figma.js': ['exportFedoraDuo'],
                'export_modifiers_figma.js': ['exportFedoraModifiers', 'exportFedoraPresets'],
            };
            for (const [file, names] of Object.entries(scripts)) {
                const context = vm.createContext({});
                new vm.Script(fs.readFileSync('scripts/' + file, 'utf8')).runInContext(context);
                for (const name of names) {
                    assert.equal(typeof context[name], 'function', file + ': ' + name);
                }
            }
        """], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
