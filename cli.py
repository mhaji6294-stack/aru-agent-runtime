import os, sys, json, argparse
from datetime import datetime, timezone
from agent import run
WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
LOGS_DIR = os.path.join(WORKSPACE, "logs")
def log_run(task, result):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "task": task, **result}) + "\n")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--steps", action="store_true")
    args = parser.parse_args()
    if not args.task: print("Usage: python cli.py \"your task\""); sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"): print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
    if not os.environ.get("ARU_API_KEY"): print("Error: ARU_API_KEY not set."); sys.exit(1)
    print(f"[ARU Runtime] Task: {args.task}\n")
    result = run(args.task)
    log_run(args.task, result)
    if args.json: print(json.dumps(result, indent=2))
    else:
        print("=== Output ==="); print(result["output"])
        if args.steps:
            print("\n=== Steps ===")
            for i, s in enumerate(result.get("steps", []), 1):
                print(f"{i}. [{'OK' if s['approved'] else 'REJECTED'}] {s['tool']}({s['input']})")
if __name__ == "__main__": main()
