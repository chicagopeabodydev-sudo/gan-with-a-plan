import asyncio, argparse, json, os, re, sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from .types import HarnessConfig
from .harness import run_harness

def main():
    parser = argparse.ArgumentParser(description="GAN-style adversarial code generation harness")
    parser.add_argument("prompt", nargs="?", help="Task description")
    parser.add_argument("--file", help="Read prompt from file instead of CLI arg")
    parser.add_argument("--mode", choices=["implementation", "plan"], default=os.environ.get("GAN_MODE", "implementation"),
        help="GAN variant: 'implementation' (default) or 'plan' (plan-gated loop)")
    parser.add_argument("--work-dir", default="./workspace", help="Working directory for agents")
    parser.add_argument("--max-sprints", type=int, default=3)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--pass-threshold", type=float, default=8.0)
    parser.add_argument("--planner-model",
        default=os.environ.get("PLANNER_MODEL", "claude-sonnet-4-6"))
    parser.add_argument("--generator-model",
        default=os.environ.get("GENERATOR_MODEL", "claude-sonnet-4-6"))
    parser.add_argument("--evaluator-model",
        default=os.environ.get("EVALUATOR_MODEL", "claude-opus-4-7"))
    args = parser.parse_args()

    if not args.prompt and not args.file:
        parser.error("provide a prompt argument or --file")
    prompt = args.prompt or open(args.file).read()
    config = HarnessConfig(
        work_dir=args.work_dir,
        user_prompt=prompt,
        max_sprints=args.max_sprints,
        max_retries_per_sprint=args.max_retries,
        pass_threshold=args.pass_threshold,
        planner_model=args.planner_model,
        generator_model=args.generator_model,
        evaluator_model=args.evaluator_model,
        mode=args.mode,
    )
    run_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    result = asyncio.run(run_harness(config))

    for s in result.sprints:
        status = "PASSED" if s.passed else "FAILED"
        print(f"Sprint {s.sprint_number}: {status} ({s.retries} retries)")
    print(f"Overall: {'SUCCESS' if result.success else 'FAILED'} in {result.total_duration_ms:.0f}ms")

    report = result.log_report
    if report:
        print(f"\n=== Metrics Report (mode={report.get('mode')}) ===")
        print(f"Total tokens : {report['total_tokens']:,}  "
              f"(in={report['total_input_tokens']:,}, out={report['total_output_tokens']:,})")
        print(f"Total turns  : {report['total_turn_count']}")
        print(f"Total time   : {report['total_duration_ms']:.0f}ms")
        print("\nPhase breakdown:")
        for phase, data in report.get("phases", {}).items():
            pr = f"  pass_rate={data['pass_rate']:.0%}" if data["pass_rate"] is not None else ""
            print(f"  {phase:16s} tokens={data['total_tokens']:>8,}  "
                  f"turns={data['turn_count']:>4}  "
                  f"time={data['duration_ms']:>8.0f}ms  "
                  f"calls={data['call_count']}{pr}")

    if result.log_report:
        workdir_slug = re.sub(r"[^a-zA-Z0-9]+", "-", os.path.basename(os.path.abspath(args.work_dir))).strip("-")
        filename = f"{run_ts}_{config.mode}_{workdir_slug}.json"
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        log_path = os.path.join(output_dir, filename)
        with open(log_path, "w") as f:
            json.dump(result.log_report, f, indent=2)
        print(f"\nLog written to: {log_path}")

    sys.exit(0 if result.success else 1)

if __name__ == "__main__":
    main()
