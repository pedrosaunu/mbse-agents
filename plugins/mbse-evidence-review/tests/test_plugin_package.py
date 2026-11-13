import json
import re
import unittest
from pathlib import Path
import yaml
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SCHEMA={
    '$schema':'https://json-schema.org/draft/2020-12/schema',
    'type':'object',
    'properties':{
       '$schema':{'const':'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'},
       'name':{'type':'string','minLength':1,'maxLength':64,
               'pattern':r'^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$'},
       'version':{'type':'string'},'description':{'type':'string'},
       'author':{'type':'object','properties':{'name':{'type':'string'},'email':{'type':'string'},'url':{'type':'string'}},'additionalProperties':False},
       'homepage':{'type':'string'},'repository':{'type':'string'},'license':{'type':'string'},
       'keywords':{'type':'array','items':{'type':'string'}},
       'extensions':{'type':'object','additionalProperties':{'type':'object'}}
    },'required':['$schema','name'],'additionalProperties':False
}

class PluginPackageTests(unittest.TestCase):
    def test_portable_manifest_validates(self):
        manifest=json.loads((ROOT/'plugin.json').read_text())
        Draft202012Validator(SCHEMA).validate(manifest)
        self.assertRegex(manifest['version'],r'^\d+\.\d+\.\d+$')
        interface=manifest['extensions']['com.openai']['interface']
        for key in ['logo','composerIcon']:
            v=interface[key];self.assertTrue(v.startswith('./'))
            self.assertNotIn('..',v)
            self.assertTrue((ROOT/v).is_file())
            svg=ET.parse(ROOT/v).getroot();self.assertTrue(svg.tag.endswith('svg'))
            self.assertEqual(svg.get('width'),svg.get('height'))
        self.assertLessEqual(len(interface['defaultPrompt']),3)
        self.assertLessEqual(len(interface['displayName']),30)
        self.assertLessEqual(len(interface['shortDescription']),30)

    def test_skill_metadata(self):
        skill=ROOT/'skills'/'mbse-evidence-review'/'SKILL.md'
        s=skill.read_text(encoding='utf-8');self.assertTrue(s.startswith('---\n'))
        meta=yaml.safe_load(s.split('---\n')[1])
        self.assertEqual('mbse-evidence-review',meta['name'])
        self.assertIn('Use when',meta['description'])
        for heading in ['Inputs and stopping rule','Read-only engineering workflow','Hard boundaries','Completion contract']:
            self.assertIn(heading,s)
        self.assertNotIn('I have personally',s)

    def test_no_unexpected_files(self):
        for p in ROOT.rglob('*'):
            self.assertFalse(p.is_symlink())
            if '__pycache__' in p.parts or p.suffix == '.pyc':
                continue  # runtime cache is excluded during packaging
            self.assertNotEqual('.env',p.name)
            if p.is_file():self.assertLess(p.stat().st_size,512_001)

    def test_reviewer_case_inventory(self):
        cases=json.loads((ROOT/'review'/'reviewer-cases.json').read_text())
        self.assertGreaterEqual(len(cases['positive']),5)
        self.assertGreaterEqual(len(cases['negative']),3)
        for item in cases['positive']+cases['negative']:
            self.assertTrue(item.get('prompt'))
            self.assertTrue(item.get('expected_behavior'))
            self.assertTrue(item.get('reason_or_shape'))
            self.assertTrue(item.get('fixture'))

if __name__=='__main__':unittest.main()
