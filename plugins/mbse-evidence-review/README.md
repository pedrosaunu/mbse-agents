# MBSE Evidence Review Plugin — bounded engineering review

Local / review candidate derived from `pedrosaunu/mbse-agents` at `49e2379f858b05482d7ce1957d08d05ef9d41683` (2026-04-09). The five domain agents are source research material, **not** five independently validated professional authorities. This package is intentionally smaller: one user job, review of an engineering claim-to-evidence chain.

## Included

- Portable Agent Plugins v1 `plugin.json` with OpenAI-specific metadata under `extensions.com.openai`
- One domain review Skill with a fixed reporting and stop contract, plus portable host-workspace/Python execution support Skills
- Read-only optional Python structural cross-link checker, no dependencies
- Synthetic positive/negative fixture regression suite and reviewer test cases
- Square light/dark local brand assets (provisional, not approved publisher identity)

## Run structural inspection on synthetic example

```bash
python skills/mbse-evidence-review/scripts/check_traceability.py tests/fixtures/complete.json
python -m unittest discover -s tests -v
```

`no_structural_gaps_detected` is **not** a certification, correctness, evidence authenticity or compliance verdict. No project data is shipped. The plugin must not invent credentials, professional experience, exact standards editions or regulatory approval.

## Distribution boundary

The package is a pre-release review candidate only. No actual ChatGPT/Codex installation, reviewer decision or verified publisher identity is implied. Before submitting publicly, perform native installation, real use-case evaluations and a professional review of any standards-specific claims. A current Plugin Autopilot validator may need to be updated to accept portable root manifests; do not claim old-format validation covers this package.
