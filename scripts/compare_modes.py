#!/usr/bin/env python3
"""Run the GAN harness in both modes (implementation and plan) and print a comparison."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime


def run_mode(mode: str, work_dir: str, prompt_args: list[str], extra_args: list[str]) -> dict | None:
    cmd = ["gan"] + prompt_args + ["--mode", mode, "--work-dir", work_dir] + extra_args
    print(f"\n{'='*60}")
    print(f"Running mode: {mode}  (work-dir: {work_dir})")
    print(f"{'='*60}")
    result = subprocess.run(cmd, text=True)
    if result.returncode not in (0, 1):
        print(f"[ERROR] gan exited with code {result.returncode}", file=sys.stderr)
        return None

    # Locate the JSON written to output/
    # Derive it from the work-dir slug the same way main.py does:
    #   re.sub(r"[^a-zA-Z0-9]+", "-", os.path.basename(os.path.abspath(work_dir))).strip("-")
    import os
    workdir_slug = re.sub(r"[^a-zA-Z0-9]+", "-", os.path.basename(os.path.abspath(work_dir))).strip("-")
    output_dir = os.path.join(os.getcwd(), "output")
    candidates = sorted(
        [f for f in os.listdir(output_dir) if f"_{mode}_{workdir_slug}" in f],
        reverse=True,
    )
    if not candidates:
        print(f"[WARN] No output JSON found for mode={mode} slug={workdir_slug}", file=sys.stderr)
        return None
    json_path = os.path.join(output_dir, candidates[0])
    with open(json_path) as f:
        data = json.load(f)
    data["_json_path"] = json_path
    data["_exit_code"] = result.returncode
    return data


def fmt_tokens(n: int | None) -> str:
    return f"{n:>10,}" if n is not None else f"{'n/a':>10}"


def fmt_ms(ms: float | None) -> str:
    return f"{ms:>10.0f}" if ms is not None else f"{'n/a':>10}"


def fmt_pct(rate: float | None) -> str:
    return f"{rate:>8.0%}" if rate is not None else f"{'n/a':>8}"


def print_comparison(impl: dict | None, plan: dict | None) -> None:
    print(f"\n{'='*70}")
    print("MODE COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Metric':<30}  {'implementation':>14}  {'plan':>14}")
    print(f"{'-'*70}")

    def row(label: str, impl_val, plan_val, fmt=str) -> None:
        iv = fmt(impl_val) if impl_val is not None else "n/a"
        pv = fmt(plan_val) if plan_val is not None else "n/a"
        print(f"  {label:<28}  {iv:>14}  {pv:>14}")

    def get(d, *keys):
        try:
            v = d
            for k in keys:
                v = v[k]
            return v
        except (KeyError, TypeError):
            return None

    row("total tokens",      get(impl, "total_tokens"),      get(plan, "total_tokens"),      lambda x: f"{x:,}")
    row("  input tokens",    get(impl, "total_input_tokens"), get(plan, "total_input_tokens"), lambda x: f"{x:,}")
    row("  output tokens",   get(impl, "total_output_tokens"), get(plan, "total_output_tokens"), lambda x: f"{x:,}")
    row("total turns",       get(impl, "total_turn_count"),  get(plan, "total_turn_count"),  lambda x: f"{x:,}")
    row("total duration (s)", get(impl, "total_duration_ms"), get(plan, "total_duration_ms"), lambda x: f"{x/1000:.1f}")
    row("exit code",         get(impl, "_exit_code"),        get(plan, "_exit_code"),        str)

    all_phases = list(dict.fromkeys(
        list((get(impl, "phases") or {}).keys()) +
        list((get(plan, "phases") or {}).keys())
    ))

    print(f"\n{'Phase breakdown':}")
    print(f"  {'phase':<14}  {'impl tokens':>11}  {'plan tokens':>11}  {'impl turns':>10}  {'plan turns':>10}  {'impl pass%':>10}  {'plan pass%':>10}")
    print(f"  {'-'*14}  {'-'*11}  {'-'*11}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")
    for phase in all_phases:
        itok = get(impl, "phases", phase, "total_tokens")
        ptok = get(plan,  "phases", phase, "total_tokens")
        itrn = get(impl, "phases", phase, "turn_count")
        ptrn = get(plan,  "phases", phase, "turn_count")
        ipr  = get(impl, "phases", phase, "pass_rate")
        ppr  = get(plan,  "phases", phase, "pass_rate")
        print(f"  {phase:<14}  "
              f"{(str(f'{itok:,}') if itok is not None else 'n/a'):>11}  "
              f"{(str(f'{ptok:,}') if ptok is not None else 'n/a'):>11}  "
              f"{(str(itrn) if itrn is not None else 'n/a'):>10}  "
              f"{(str(ptrn) if ptrn is not None else 'n/a'):>10}  "
              f"{fmt_pct(ipr):>10}  "
              f"{fmt_pct(ppr):>10}")

    print(f"\nOutput files:")
    if impl:
        print(f"  implementation: {impl.get('_json_path', 'unknown')}")
    if plan:
        print(f"  plan:           {plan.get('_json_path', 'unknown')}")
    print(f"{'='*70}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GAN harness in both modes and compare results")
    parser.add_argument("prompt", nargs="?", help="Inline task prompt")
    parser.add_argument("--file", help="Read prompt from file")
    parser.add_argument("--work-dir-base", default="comparison",
                        help="Slug for work dirs; produces workspace/{base}-impl-TS and workspace/{base}-plan-TS")
    parser.add_argument("--max-sprints", type=int, default=1)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--pass-threshold", type=float, default=6.0)
    parser.add_argument("--planner-model", default=None)
    parser.add_argument("--generator-model", default=None)
    parser.add_argument("--evaluator-model", default=None)
    args = parser.parse_args()

    if not args.prompt and not args.file:
        parser.error("provide a prompt argument or --file")

    prompt_args = ["--file", args.file] if args.file else [args.prompt]

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = args.work_dir_base

    extra = [
        "--max-sprints", str(args.max_sprints),
        "--max-retries", str(args.max_retries),
        "--pass-threshold", str(args.pass_threshold),
    ]
    if args.planner_model:
        extra += ["--planner-model", args.planner_model]
    if args.generator_model:
        extra += ["--generator-model", args.generator_model]
    if args.evaluator_model:
        extra += ["--evaluator-model", args.evaluator_model]

    impl_result = run_mode("implementation", f"./workspace/{base}-impl-{ts}", prompt_args, extra)
    plan_result  = run_mode("plan",           f"./workspace/{base}-plan-{ts}", prompt_args, extra)

    print_comparison(impl_result, plan_result)

    impl_ok = impl_result is not None and impl_result.get("_exit_code") == 0
    plan_ok  = plan_result  is not None and plan_result.get("_exit_code")  == 0
    return 0 if (impl_ok and plan_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
