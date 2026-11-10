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

    def test_duo_export_accepts_expansion_growth_but_rejects_missing_sources(self):
        result = subprocess.run(["node", "-e", """
            const fs = require('node:fs');
            const vm = require('node:vm');
            const assert = require('node:assert/strict');
            (async () => {
                for (const [actual, total, done, expected] of [
                    [1228, 1228, 1228, 'ready'],
                    [1234, 1234, 1234, 'ready'],
                    [1228, 1234, 1234, 'Incomplete native expansion'],
                    [1234, 1234, 1228, 'Incomplete native expansion'],
                ]) {
                    const context = vm.createContext({figma: {
                        getNodeByIdAsync: async id => id === '45:36965' ? {
                            findAll: () => Array(actual).fill({}),
                            getPluginData: () => JSON.stringify({total, done}),
                        } : {getPluginData: key => JSON.stringify(
                            key === 'namedPresetMigration' ? {records: []} : {}
                        )},
                        createSection: () => {throw new Error('ready');},
                    }});
                    new vm.Script(fs.readFileSync(
                        'scripts/export_duo_figma.js', 'utf8'
                    )).runInContext(context);
                    await assert.rejects(context.exportFedoraDuo(),
                        error => error.message === expected);
                }
            })().catch(error => {console.error(error); process.exitCode = 1;});
        """], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
