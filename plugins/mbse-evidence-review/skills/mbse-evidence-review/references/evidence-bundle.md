# JSON bundle for optional deterministic structural check

This explicit input schema is **not** an industry-standard exchange schema and does not replace SysML v2, ReqIF, OSLC or project-native authorities. It is a bounded, synthetic-friendly evidence-index interchange.

At top level use `schema_version: "1.0"`, `system: {name, baseline}`, `sources`, `requirements`, `architecture`, `verifications`.

- `sources`: list of `{id, version, locator}`. A locator merely identifies supplied data; the checker cannot validate its authenticity.
- `requirements`: list of `{id, statement, source_id, allocation_ids, verification_ids, safety_relevant?}`. `safety_relevant` is optional boolean.
- `architecture`: list of `{id, source_id, satisfies}` where `satisfies` is requirement-ID list.
- `verifications`: list of `{id, source_id, requirement_ids, method, result, evidence_source_id?, baseline}`. Method is `test`, `analysis`, `inspection`, `demonstration` or `other`. Result is `passed`, `failed`, `planned`, `unknown` or `not_applicable`.
- `evidence_source_id` on a passing verification must identify a supplied source document containing the claimed result record. The checker does not verify its content.

All IDs are unique across collections; source and requirement collections must be nonempty; input size is bounded to 512,000 bytes and each collection to 500 entries. Unknown fields are rejected, including any attempted approval or certification fields. The tool checks source IDs, reciprocal links, unfinished/failed verification, unsupported passes and baselines.

Only use the optional script with explicitly authorized bundles, and protect confidential project data according to the applicable project policy. The checker makes no external network calls and writes nothing unless `--out` was explicitly requested.
