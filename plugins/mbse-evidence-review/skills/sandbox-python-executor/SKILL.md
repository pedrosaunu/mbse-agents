---
name: sandbox-python-executor
description: When the MBSE Evidence Review Plugin must deterministically parse, check, compare or validate a user-authorized evidence bundle, execute bounded Python in the host sandbox where available and report real execution evidence.
---

# Sandbox Python Executor — MBSE Evidence Review

Use the current host's Python tool if present. This Skill does **not** grant Python availability, internet access, credentials or permission to execute arbitrary user/repository code.

For the explicitly supplied JSON bundle, inspect the packaged `mbse-evidence-review/scripts/check_traceability.py` before execution when necessary and run it without `--out` (read-only). Only use `--out` when asked to create an output file. Prefer direct file reading for simple lookup questions.

Validate the input file path and size, capture process exit status, parse JSON result, report important finding codes with their source IDs, and preserve the `non_claims`. A script pass establishes **structural parsing and consistency checks only**, not the truth of requirements, results or standards conformity.

If Python is unavailable, proceed with an explicitly manual review without claiming script execution. If the script fails, report the error and do not substitute made-up results.
