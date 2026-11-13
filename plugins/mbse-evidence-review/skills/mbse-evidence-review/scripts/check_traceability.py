#!/usr/bin/env python3
"""Read-only, deterministic inspection of an explicitly supplied synthetic/project trace bundle.

This checks structural evidence links, not normative compliance or real-world correctness.
It never executes source code, performs network requests, or modifies input files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_INPUT_BYTES = 512_000
ALLOWED_TOP = {'schema_version', 'system', 'sources', 'requirements', 'architecture', 'verifications'}
SOURCE_KEYS = {'id', 'version', 'locator'}
REQ_KEYS = {'id', 'statement', 'source_id', 'allocation_ids', 'verification_ids', 'safety_relevant'}
ARCH_KEYS = {'id', 'source_id', 'satisfies'}
VER_KEYS = {'id', 'source_id', 'requirement_ids', 'method', 'result', 'evidence_source_id', 'baseline'}
RESULTS = {'passed', 'failed', 'planned', 'unknown', 'not_applicable'}
METHODS = {'test', 'analysis', 'inspection', 'demonstration', 'other'}
MAX_ITEMS = 500


class InvalidBundle(ValueError):
    pass


def error(msg: str) -> None:
    raise InvalidBundle(msg)


def ensure_record(value, name: str, allowed: set[str], required: set[str]):
    if not isinstance(value, dict):
        error(f'{name}: expected an object')
    extra = set(value) - allowed
    if extra:
        error(f'{name}: unsupported field(s): {", ".join(sorted(extra))}')
    missing = required - set(value)
    if missing:
        error(f'{name}: missing field(s): {", ".join(sorted(missing))}')


def nonblank(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 5000:
        error(f'{name}: expected non-empty bounded string')
    return value


def ids(value, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        error(f'{name}: expected a bounded list')
    for i, item in enumerate(value):
        nonblank(item, f'{name}[{i}]')
    if len(set(value)) != len(value):
        error(f'{name}: duplicate links')
    return value


def records(value, name: str, allowed: set[str], required: set[str]):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        error(f'{name}: expected a list of at most {MAX_ITEMS}')
    seen: set[str] = set()
    for i, row in enumerate(value):
        place = f'{name}[{i}]'
        ensure_record(row, place, allowed, required)
        ident = nonblank(row['id'], f'{place}.id')
        if ident in seen:
            error(f'{name}: duplicated ID {ident}')
        seen.add(ident)
    return {row['id']: row for row in value}


def validate(bundle: object) -> tuple[dict, dict, dict, dict]:
    ensure_record(bundle, 'bundle', ALLOWED_TOP, ALLOWED_TOP)
    if bundle['schema_version'] != '1.0':
        error('schema_version: expected 1.0')
    ensure_record(bundle['system'], 'system', {'name', 'baseline'}, {'name', 'baseline'})
    nonblank(bundle['system']['name'], 'system.name')
    nonblank(bundle['system']['baseline'], 'system.baseline')
    sources = records(bundle['sources'], 'sources', SOURCE_KEYS, SOURCE_KEYS)
    req = records(bundle['requirements'], 'requirements', REQ_KEYS,
                  {'id', 'statement', 'source_id', 'allocation_ids', 'verification_ids'})
    arch = records(bundle['architecture'], 'architecture', ARCH_KEYS, ARCH_KEYS)
    verification = records(bundle['verifications'], 'verifications', VER_KEYS, VER_KEYS - {'evidence_source_id'})
    if not sources or not req:
        error('nonempty sources and requirements are required; no evidence review possible')
    all_ids = [*sources, *req, *arch, *verification]
    if len(set(all_ids)) != len(all_ids):
        error('IDs must be unique across source, requirement, architecture, and verification namespaces')
    for r in req.values():
        nonblank(r['statement'], f"requirement {r['id']}.statement")
        nonblank(r['source_id'], f"requirement {r['id']}.source_id")
        ids(r['allocation_ids'], f"requirement {r['id']}.allocation_ids")
        ids(r['verification_ids'], f"requirement {r['id']}.verification_ids")
        if 'safety_relevant' in r and not isinstance(r['safety_relevant'], bool):
            error(f"requirement {r['id']}.safety_relevant: expected boolean")
    for a in arch.values():
        nonblank(a['source_id'], f"architecture {a['id']}.source_id")
        ids(a['satisfies'], f"architecture {a['id']}.satisfies")
    for v in verification.values():
        nonblank(v['source_id'], f"verification {v['id']}.source_id")
        ids(v['requirement_ids'], f"verification {v['id']}.requirement_ids")
        if v['method'] not in METHODS:
            error(f"verification {v['id']}.method: unsupported value")
        if v['result'] not in RESULTS:
            error(f"verification {v['id']}.result: unsupported value")
        nonblank(v['baseline'], f"verification {v['id']}.baseline")
        if 'evidence_source_id' in v and v['evidence_source_id'] is not None:
            nonblank(v['evidence_source_id'], f"verification {v['id']}.evidence_source_id")
    for s in sources.values():
        nonblank(s['version'], f"source {s['id']}.version")
        nonblank(s['locator'], f"source {s['id']}.locator")
    return sources, req, arch, verification


def inspect(bundle: dict) -> dict:
    sources, requirements, architecture, verifications = validate(bundle)
    findings: list[dict] = []
    matrix: list[dict] = []

    def add(code: str, severity: str, entity: str, detail: str, action: str):
        findings.append({'code': code, 'severity': severity, 'entity_id': entity,
                         'detail': detail, 'recommended_action': action})

    for r in requirements.values():
        rid = r['id']
        relevant = r.get('safety_relevant', False)
        severity = 'high' if relevant else 'medium'
        if r['source_id'] not in sources:
            add('UNKNOWN_REQUIREMENT_SOURCE', severity, rid, f"Unresolved source: {r['source_id']}",
                'Provide the source document, revision and locator')
        if not r['allocation_ids']:
            add('NO_ALLOCATION', severity, rid, 'No architecture allocation linked',
                'Provide an architecture allocation or a documented exception')
        if not r['verification_ids']:
            add('NO_VERIFICATION', severity, rid, 'No verification activities linked',
                'Provide planned and executed verification records')
        for aid in r['allocation_ids']:
            if aid not in architecture:
                add('MISSING_ARCHITECTURE', severity, rid, f'Architecture ID {aid} not supplied',
                    'Supply the referenced architecture artifact')
            elif rid not in architecture[aid]['satisfies']:
                add('NON_RECIPROCAL_ALLOCATION', severity, rid,
                    f'Architecture {aid} does not list this requirement',
                    'Reconcile both sides of the allocation link')
        for vid in r['verification_ids']:
            if vid not in verifications:
                add('MISSING_VERIFICATION', severity, rid, f'Verification ID {vid} not supplied',
                    'Supply the referenced verification artifact')
            elif rid not in verifications[vid]['requirement_ids']:
                add('NON_RECIPROCAL_VERIFICATION', severity, rid,
                    f'Verification {vid} does not list this requirement',
                    'Reconcile both sides of the verification link')
        matrix.append({'requirement_id': rid, 'source_id': r['source_id'],
                       'allocation_ids': r['allocation_ids'],
                       'verification_ids': r['verification_ids']})

    for a in architecture.values():
        if a['source_id'] not in sources:
            add('UNKNOWN_ARCHITECTURE_SOURCE', 'medium', a['id'],
                f"Unresolved source: {a['source_id']}", 'Supply the architecture source artifact')
        for rid in a['satisfies']:
            if rid not in requirements:
                add('ORPHAN_ARCHITECTURE_LINK', 'medium', a['id'],
                    f'Unknown requirement {rid}', 'Fix stale or incorrect requirement reference')
            elif a['id'] not in requirements[rid]['allocation_ids']:
                add('NON_RECIPROCAL_ARCHITECTURE', 'medium', a['id'],
                    f'Requirement {rid} does not link back', 'Reconcile both sides of the link')

    for v in verifications.values():
        vid = v['id']
        if v['source_id'] not in sources:
            add('UNKNOWN_VERIFICATION_SOURCE', 'high', vid,
                f"Unresolved source: {v['source_id']}", 'Supply the verification plan or procedure')
        for rid in v['requirement_ids']:
            if rid not in requirements:
                add('ORPHAN_VERIFICATION_LINK', 'medium', vid,
                    f'Unknown requirement {rid}', 'Fix stale or incorrect requirement reference')
            elif vid not in requirements[rid]['verification_ids']:
                add('NON_RECIPROCAL_VERIFICATION_RECORD', 'medium', vid,
                    f'Requirement {rid} does not link back', 'Reconcile verification trace links')
        if v['result'] == 'failed':
            add('FAILED_VERIFICATION', 'high', vid,
                'Recorded verification result is failed', 'Investigate defect and reverify')
        if v['result'] in {'planned', 'unknown'}:
            add('UNFINISHED_VERIFICATION', 'medium', vid,
                f"Verification status is {v['result']}", 'Record performed activity and result')
        if v['result'] == 'passed':
            evidence = v.get('evidence_source_id')
            if not evidence or evidence not in sources:
                add('UNSUPPORTED_PASS', 'high', vid,
                    'Claimed pass lacks an identifiable supplied evidence source',
                    'Supply immutable result record and its version/locator')
        if v['baseline'] != bundle['system']['baseline']:
            add('BASELINE_MISMATCH', 'high', vid,
                f"Verification baseline {v['baseline']} != system baseline {bundle['system']['baseline']}",
                'Reconcile configuration baseline and assess re-verification need')

    findings.sort(key=lambda f: ({'high': 0, 'medium': 1, 'low': 2}[f['severity']], f['entity_id'], f['code']))
    matrix.sort(key=lambda x: x['requirement_id'])
    return {'schema_version': '1.0', 'system': bundle['system'],
            'inspection': {'sources': len(sources), 'requirements': len(requirements),
                           'architecture_elements': len(architecture), 'verification_activities': len(verifications)},
            'status': 'potential_gaps_found' if findings else 'no_structural_gaps_detected',
            'traceability_matrix': matrix, 'findings': findings,
            'non_claims': ['No source document was authenticated or independently verified',
                           'No regulatory compliance, design adequacy or certification approval is asserted',
                           'A structurally complete bundle may contain false or incomplete claims']}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle', type=Path, help='explicit path to JSON evidence bundle')
    p.add_argument('--out', type=Path, help='optional output JSON path (writes only on explicit request)')
    args = p.parse_args(argv)
    try:
        if args.bundle.stat().st_size > MAX_INPUT_BYTES:
            error(f'input exceeds {MAX_INPUT_BYTES} bytes')
        bundle = json.loads(args.bundle.read_text('utf-8'))
        result = inspect(bundle)
    except (OSError, UnicodeError, json.JSONDecodeError, InvalidBundle) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 2
    result['ok'] = True
    output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if args.out:
        try:
            args.out.write_text(output, encoding='utf-8')
        except OSError as exc:
            print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
            return 2
    else:
        sys.stdout.write(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
