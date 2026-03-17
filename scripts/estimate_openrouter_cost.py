#!/usr/bin/env python3
"""Estimate BullshitBench run cost for a config using OpenRouter model pricing.

Uses OpenRouter's public model catalog endpoint (`/api/v1/models`) to read
`pricing.prompt` and `pricing.completion` values, then multiplies by expected
average tokens per response and per judge grade call.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import urllib.error
import urllib.request

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def _load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_openrouter_models() -> dict[str, dict]:
    with urllib.request.urlopen(OPENROUTER_MODELS_URL, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    result: dict[str, dict] = {}
    for item in payload.get("data", []):
        model_id = str(item.get("id", "")).strip()
        if model_id:
            result[model_id] = item
    return result


def _price_per_million(model_data: dict) -> tuple[float, float]:
    pricing = model_data.get("pricing") if isinstance(model_data.get("pricing"), dict) else {}
    prompt = float(pricing.get("prompt", 0.0)) * 1_000_000
    completion = float(pricing.get("completion", 0.0)) * 1_000_000
    return prompt, completion


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.qwen-openrouter.json")
    parser.add_argument("--avg-collect-input", type=float, default=900)
    parser.add_argument("--avg-collect-output", type=float, default=350)
    parser.add_argument("--avg-judge-input", type=float, default=1300)
    parser.add_argument("--avg-judge-output", type=float, default=120)
    args = parser.parse_args()

    config = _load_json(pathlib.Path(args.config))
    questions_path = pathlib.Path(config["collect"]["questions"])
    questions = _load_json(questions_path)
    q_count = len(questions)

    collect_models = config["collect"].get("models", [])
    judge_models = config.get("grade_panel", {}).get("judge_models", [])

    try:
        model_catalog = _fetch_openrouter_models()
    except urllib.error.URLError as exc:
        print(f"Unable to fetch OpenRouter model catalog: {exc}")
        print("Check network egress to https://openrouter.ai/api/v1/models and retry.")
        return 1

    missing = [m for m in [*collect_models, *judge_models] if m not in model_catalog]
    if missing:
        print("Missing from OpenRouter catalog:")
        for m in missing:
            print(f"  - {m}")
        return 2

    def est_cost(model_id: str, in_tok: float, out_tok: float, calls: int) -> float:
        p_in, p_out = _price_per_million(model_catalog[model_id])
        return calls * ((in_tok / 1_000_000) * p_in + (out_tok / 1_000_000) * p_out)

    total_collect_calls = q_count
    total_judge_calls = q_count * len(collect_models)

    collect_total = 0.0
    for m in collect_models:
        collect_total += est_cost(m, args.avg_collect_input, args.avg_collect_output, total_collect_calls)

    judge_total = 0.0
    for j in judge_models:
        judge_total += est_cost(j, args.avg_judge_input, args.avg_judge_output, total_judge_calls)

    total = collect_total + judge_total

    print(f"Config: {args.config}")
    print(f"Questions: {q_count}")
    print(f"Collect models: {len(collect_models)}")
    print(f"Panel judges: {len(judge_models)}")
    print(f"Estimated collect cost (USD): {collect_total:.4f}")
    print(f"Estimated judge-panel cost (USD): {judge_total:.4f}")
    print(f"Estimated total benchmark cost (USD): {total:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
