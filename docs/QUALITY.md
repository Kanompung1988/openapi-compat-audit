# Evidence and limitations — OpenAPI Compatibility Audit

## Proven baseline (2026-10-24)

- The original skill, before separation into this repository, ran in [AREAZERO Skill Lab EP.01](https://github.com/Kanompung1988/agent-skills/pull/1).
- The combined original quality gate passed 32 unit tests on Python 3.10 and 3.12 at [GitHub Actions run #3](https://github.com/Kanompung1988/agent-skills/actions/runs/40090285727).
- Per-skill original unit suite contains 11 tests, preserved here. An additional standalone distribution/brand test suite and a deterministic demo smoke test are included and run by this repository's independent workflow.
- The included fixture reports are synthetic, not production measurements.
- Official reference `skills-ref` validator: **not run** in the initial release. Independent human audit: **not claimed**.

## Limits of the claims

Heuristics are not an exhaustive OpenAPI semantic solver. External `$ref`, polymorphic schema rules, auth changes and runtime behavior need manual tests. Zero findings does **not** prove client compatibility.

No promises are made about measured real-world accuracy, cross-repository installations, or community adoption. The GitHub Actions matrix and repeatable local commands are the current evidence for this public package.
