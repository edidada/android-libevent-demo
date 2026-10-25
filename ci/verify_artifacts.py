"""Reject empty output or archives for the build host instead of Android."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--ndk', required=True)
p.add_argument('--triplet', required=True)
p.add_argument('--abi', required=True)
args = p.parse_args()
expected = {'arm64-v8a': 'elf64-littleaarch64', 'armeabi-v7a': 'elf32-littlearm',
            'x86': 'elf32-i386', 'x86_64': 'elf64-x86-64'}[args.abi]
tool = next(Path(args.ndk).glob('toolchains/llvm/prebuilt/*/bin/llvm-readobj' +
                               ('.exe' if os.name == 'nt' else '')))
prefix = Path('out/installed') / args.triplet
assert (prefix / 'include').is_dir(), 'Missing installed headers'
libs = list((prefix / 'lib').rglob('*.a'))
assert libs, 'No static libraries installed'
extras = json.loads(Path('out/extra/results.json').read_text())
assert all(v['status'] == 'success' for v in extras.values()), extras
for name in extras:
    libs += list((Path('out/extra') / name).rglob('*.a'))
results = []
for lib in libs:
    output = subprocess.check_output([str(tool), '--file-headers', str(lib)], text=True)
    formats = set(re.findall(r'^Format: (.+)$', output, re.MULTILINE))
    assert formats == {expected}, f'{lib}: wrong or empty archive: {formats}'
    results.append({'path': str(lib), 'format': expected, 'bytes': lib.stat().st_size})
Path('out/artifact-verification.json').write_text(json.dumps(results, indent=2))
summary = f'Android {args.abi}: verified {len(results)} static archives ({expected}).\n'
print(summary)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
        f.write(summary)
