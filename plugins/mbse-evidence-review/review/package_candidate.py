#!/usr/bin/env python3
"""Deterministically package this review candidate and reject unsafe paths/files.

No external dependencies; this is NOT the official Plugin Autopilot validator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SECRETS={'auth.json','credentials.json','secret.json','.env','.npmrc','.pypirc'}
FIXED=(1980,1,1,0,0,0)


def files():
    out=[]
    for p in sorted(ROOT.rglob('*'),key=lambda p:p.relative_to(ROOT).as_posix()):
        rel=p.relative_to(ROOT).as_posix()
        if p.is_symlink():raise ValueError(f'symlink forbidden: {rel}')
        if '__pycache__' in p.parts or p.suffix=='.pyc':continue
        if p.is_dir():continue
        if p.name.lower() in SECRETS or (p.name.lower().startswith('.env')):
            raise ValueError(f'potential secrets file: {rel}')
        if len(rel)>1024 or '\\' in rel or len(p.parts)>50:
            raise ValueError(f'unsafe path: {rel}')
        data=p.read_bytes()
        if len(data)>1_000_000:raise ValueError(f'oversized entry: {rel}')
        if (b'-----BEGIN PRIVATE' + b' KEY-----') in data:
            raise ValueError(f'private key in {rel}')
        out.append((rel,data))
    return out


def build(path:Path):
    manifest=json.loads((ROOT/'plugin.json').read_text())
    assert manifest['name']=='mbse-evidence-review'
    listing=files()
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for rel,data in listing:
            info=zipfile.ZipInfo(rel,date_time=FIXED)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(stat.S_IFREG | 0o644)<<16
            archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'entries':len(listing),'path':str(path)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args();print(json.dumps(build(args.output),indent=2))
if __name__=='__main__':main()
