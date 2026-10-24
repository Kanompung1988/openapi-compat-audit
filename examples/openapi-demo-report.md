# OpenAPI Compatibility Audit

Old: `/mnt/data/areazero_lab/2026-10-24/agent-skills/examples/openapi-before.json`  
New: `/mnt/data/areazero_lab/2026-10-24/agent-skills/examples/openapi-after.json`

**3 breaking change(s); 0 manual-review finding(s).**

| Severity | Rule | Location | Evidence |
|---|---|---|---|
| breaking | new-required-request-property | POST /v1/payments request application/json.reference | Property is now required in request data. |
| breaking | request-enum-narrowed | POST /v1/payments request application/json.currency | Previously accepted enum value(s) removed: ['USD'] |
| breaking | response-status-removed | POST /v1/payments response 201 | Previously documented successful/default response status removed. |

Review composed/external schemas and runtime behavior separately; results are static-document checks only.
