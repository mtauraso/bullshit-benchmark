# Continuation Prompt for Next Agent Instance

Read this file and continue from here.

## Goal
Update this repo so BullshitBench can run a **Qwen-only benchmark via OpenRouter** and produce a **cost estimate sourced from OpenRouter pricing** before running.

## User intent (must preserve)
- Benchmark models should be ONLY these families/sizes (small/medium/large style):
  - **Qwen 3.5:** 9B, 27B, 35B-A3B
  - **Qwen 3:** 2–3 similar sizes
  - **Qwen 2.5:** 2–3 similar sizes
- Use **OpenRouter-only routing** for model execution.
- Verify models are actually available on OpenRouter.
- Estimate full benchmark cost from OpenRouter pricing **before asking for API keys**.
- Then request keys and do a dry run.

## Current repo state
A prior agent already added:
- `config.qwen-openrouter.json`
- `scripts/estimate_openrouter_cost.py`
- README quick-start updates for both.

Latest commit before this handoff:
- `482db1f Add Qwen-only OpenRouter benchmark config and cost estimator`

## Blocking issue observed
Environment currently cannot reach OpenRouter through proxy:
- `curl -i https://openrouter.ai` returns `HTTP/1.1 403 Forbidden` and `curl: (56) CONNECT tunnel failed, response 403`.
- `python3 scripts/estimate_openrouter_cost.py --config config.qwen-openrouter.json` fails similarly when fetching `https://openrouter.ai/api/v1/models`.

User noted they likely need a new instance for updated network allowlist settings to take effect.

## What the next agent should do first
1. Re-test connectivity:
   - `curl -i https://openrouter.ai`
   - `curl -sS https://openrouter.ai/api/v1/models | head`
2. If reachable, run:
   - `python3 scripts/estimate_openrouter_cost.py --config config.qwen-openrouter.json`
3. Validate model IDs in `config.qwen-openrouter.json` are present in OpenRouter catalog.
4. If any IDs are unavailable, update config to available equivalents and re-run estimate.
5. Report estimated full benchmark cost with assumptions.
6. Ask user for API keys and run a small dry run command.

## Notes for continuity
- Keep provider routing as OpenRouter for collect/judge unless user asks otherwise.
- Keep judge panel consistent with project conventions unless user asks to change.
- If environment still blocks OpenRouter, provide exact command output and stop short of fake estimates.
- Commit any fixes and create PR message per task harness requirements.

