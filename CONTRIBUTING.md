# Contributing

Contributions with **minimal reproducible fixtures and regression tests** are welcome. Please open an issue first for large scope changes.

1. Search existing issues and describe a specific developer pain point.
2. Include sanitized or synthetic inputs; do not commit proprietary API contracts, credentials or real user logs.
3. Keep pull requests small and ensure each behavior change has tests.
4. Re-run: `python3 -m unittest discover -s tests -v` and `python3 qa/smoke.py`.
5. Update `SKILL.md`, references and README when inputs/outputs/limitations change.
6. Do not weaken checks, invent benchmark numbers or bypass GitHub Actions failures.

Contributors must preserve the [MIT code license](LICENSE). The Area Zero logos and marks are excluded from MIT; see [BRAND.md](BRAND.md).
