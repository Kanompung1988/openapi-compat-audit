# Security policy

This is a local development aid, not an access-control boundary. Report suspected security issues through a private GitHub security advisory or a non-public channel to the maintainers; **do not post real credentials or proprietary logs in public issues**.

- Input files and CI logs stay on your machine unless you choose to upload/share them elsewhere.
- The scripts do not execute embedded commands, modify production systems or call external APIs.
- CI fixtures must be synthetic and contain no real personal information, access tokens or secrets.
- Log redaction is best effort and must be verified by a human before publishing output.
- Never put a personal access token in command-line arguments, Git history, or issue comments.

See the README for tool-specific assumptions and limitations.
