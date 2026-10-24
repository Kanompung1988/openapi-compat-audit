"""Verify documented synthetic fixture output without external services."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
cmd=[sys.executable,'scripts/compare_openapi.py',*'--old examples/openapi-before.json --new examples/openapi-after.json --format json'.split()]
result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False)
if result.returncode!=2:
    raise SystemExit(f'CLI exit was {result.returncode} instead of 2: {result.stderr}')
obj=json.loads(result.stdout)
assert obj['summary']['breaking']==3, obj['summary']
assert len(obj['findings'])==3, len(obj['findings'])
print('PASS: 3 synthetic OpenAPI breaking findings (CLI exit 2)')
