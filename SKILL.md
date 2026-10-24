---
name: openapi-compat-audit
description: Detect likely breaking changes between two local OpenAPI 3.x contracts before merging an API change. Use for API schema PR reviews, release readiness, SDK compatibility checks, or regression-risk triage when old and new JSON/YAML specs are available.
license: MIT
compatibility: Python 3.10+; for YAML input, optional PyYAML. Offline and read-only unless --out is supplied.
metadata:
  author: Areazero Open Source Lab
  version: "1.0.0"
---

# OpenAPI Compatibility Audit

## Use when

The user has **old and proposed OpenAPI 3.x specifications** and asks whether a change could break existing API clients, SDKs, or a release. Use only with authorized local files. Describe this tool as a conservative static detector, not a complete compatibility guarantee.

## Don't use when

- You have only runtime responses but no comparable contracts.
- You need to fetch untrusted external schemas or send specs to third parties.
- The API primarily relies on polymorphic `oneOf`/`allOf`/`anyOf` models requiring semantic analysis.
- The API is described exclusively with GraphQL/Proto/AsyncAPI instead of OpenAPI 3.x.

## Workflow

1. Obtain **two explicit local paths**: baseline (old) and candidate (new). Never guess which is authoritative or overwrite either spec.
2. If the documents are in YAML format, check that `PyYAML` is available. Python stdlib is sufficient for JSON. External `$ref` URLs must never be resolved over the network; the script flags them for manual review.
3. Run from the skill directory or use absolute paths:

   ```bash
   python3 scripts/compare_openapi.py --old /path/to/before.json --new /path/to/after.json --format markdown --out /tmp/openapi-compat-report.md
   ```

4. Read the exit code: `0` = no **detected** breaking changes, `2` = at least one detected breaking change, `1` = input/parse error. **Exit 0 is not proof of safety**; the script intentionally lacks full spec-semantic coverage.
5. Inspect every finding with the code/contract owner. Prioritize rule `operation-removed`, newly required parameters/request properties, removed accepted enum values, dropped success responses/media types, and removed required response properties.
6. Treat `review` findings as hypotheses needing manual contract, SDK, and integration tests. For high-risk endpoints, propose consumer-driven contract tests.
7. Return a decision table with evidence, potential consumers, targeted verification, and clear statement of residual uncertainty. Do not modify the user's API or merge code on your own.

## Rules

- **Read-only**; never deploy, change APIs, or send payloads. `--out` writes only the requested report.
- Both directions matter: a **request enum narrowing** may reject old clients, whereas a **response enum expansion** may break exhaustive consumer matches; the script intentionally reports these differently.
- Only HTTP methods present in *both* contracts are schema-compared. Removing an entire operation is a breaking finding; adding operations is normally nonbreaking.
- Preserve machine-readable evidence with `--format json` when handing off to another agent.
- Do not call findings "definitive" when they involve external references, polymorphic schemas, loosely typed schemas or runtime behavior.

## Examples

```bash
# Human-readable report, exits 2 if a breaking finding exists
python3 scripts/compare_openapi.py --old examples/v1.json --new examples/v2.json

# JSON for machine pipelines; fail for review findings too
python3 scripts/compare_openapi.py --old old.json --new new.json --format json --fail-on any > audit.json

# Informational scan; never fail CI based on the output
python3 scripts/compare_openapi.py --old old.yaml --new new.yaml --fail-on none
```

## Edge cases

- `$ref` cycles/external refs: no network fetch. Unresolved or composed schemas are marked for review where encountered.
- YAML without PyYAML: return a helpful error; convert to JSON or install PyYAML with permission.
- OpenAPI 2/Swagger specs: rejected. Convert to 3.x with a reviewed tool first.
- Different base server URL/security scheme: **not audited**, review manually.
- `default` responses and vendor extensions: not full behavior simulation.
- Partial contracts and omitted `properties`: do not automatically infer client breakage.

## References

- [Coverage and caveats](references/COVERAGE.md)
- [CLI implementation](scripts/compare_openapi.py)
- [Regression tests](tests/test_compare_openapi.py)
- [Agent Skills open specification](https://agentskills.io/specification)
