# Coverage and caveats

## Contract comparison strategy

The analyzer differentiates request permissiveness from response shape because client compatibility depends on direction. For example, a new required **request** field forces old callers to change, while an additional **response** field usually does not. A removed required response field is treated as breaking because callers had a documented guarantee. Optional response field removal is review rather than breaking: documentation alone cannot establish whether anyone uses it.

## Known limitations (explicit)

1. Only local OpenAPI 3.x JSON/YAML, and local JSON pointers of the form `#/...`; external reference links are never fetched.
2. No full JSON Schema 2020-12 evaluation, discriminator handling, composition merging, regex, formats, nullable edge cases, or custom vendor extensions.
3. No live API calls or SDK compilation; cannot verify undocumented clients.
4. No auth, server, pagination, rate limits, errors other than old 2xx/default, or custom status semantics.
5. Content types and nested properties are compared only where corresponding schemas exist on both sides.
6. Static analysis may over/under-report depending on OpenAPI author's strictness.

## Manual follow-up questions

- Which published API clients/SDK versions consume this endpoint?
- Can consumer-driven contract tests reproduce the report's findings?
- Have authentication, error codes, server base URLs, headers, and rate limits changed?
- Are composed schemas, `$ref` inheritance, discriminators, and special nullable formats present?
- Is there a deprecation/migration plan for confirmed breaks?
