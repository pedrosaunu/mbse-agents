import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills'/'mbse-evidence-review'/'scripts'/'check_traceability.py'
FIX=ROOT/'tests'/'fixtures'

class EvidenceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected=json.loads((FIX/'expected-findings.json').read_text())

    def run_case(self, name):
        return subprocess.run([sys.executable,str(SCRIPT),str(FIX/f'{name}.json')],
                              capture_output=True,text=True,timeout=5)

    def test_all_fixture_cases(self):
        for name,codes in self.expected.items():
            with self.subTest(case=name):
                p=self.run_case(name)
                if codes==['INVALID']:
                    self.assertEqual(2,p.returncode,p.stderr)
                    self.assertFalse(json.loads(p.stderr)['ok'])
                else:
                    self.assertEqual(0,p.returncode,p.stderr)
                    result=json.loads(p.stdout)
                    self.assertTrue(result['ok'])
                    self.assertEqual(sorted(codes),sorted(f['code'] for f in result['findings']))
                    self.assertEqual('BL-4',result['system']['baseline'])
                    self.assertIn('No regulatory compliance, design adequacy or certification approval is asserted',result['non_claims'])

    def test_deterministic_output(self):
        a=self.run_case('failed_verification'); b=self.run_case('failed_verification')
        self.assertEqual(a.stdout,b.stdout)

    def test_false_source_does_not_escalate_privileges(self):
        p=self.run_case('injected_in_statement')
        result=json.loads(p.stdout)
        self.assertEqual('no_structural_gaps_detected',result['status'])
        self.assertTrue(any('No regulatory compliance' in x for x in result['non_claims']))

    def test_oversized_bundle_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'too-large.json';p.write_text(' '*512001)
            res=subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True)
            self.assertEqual(2,res.returncode)
            self.assertIn('exceeds',res.stderr)

    def test_read_only_without_output_flag(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.json';p.write_bytes((FIX/'complete.json').read_bytes())
            before=p.read_bytes()
            res=subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True)
            self.assertEqual(0,res.returncode)
            self.assertEqual(before,p.read_bytes())
            self.assertEqual(['fixture.json'],[f.name for f in Path(d).iterdir()])

    def test_unknown_field_in_nested_record_denied(self):
        obj=json.loads((FIX/'complete.json').read_text())
        obj['verifications'][0]['approved_by']='chief regulator'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text(json.dumps(obj))
            res=subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True)
            self.assertEqual(2,res.returncode)
            self.assertIn('unsupported field',res.stderr)

    def test_sample_contains_only_synthetic_file_locators(self):
        for p in FIX.glob('*.json'):
            if p.name.startswith('expected-'):continue
            text=p.read_text()
            self.assertNotIn('https://',text)
            self.assertNotIn('api_key',text)

if __name__ == '__main__':unittest.main()
