import sys
import json
import asyncio
from pathlib import Path
from lexismetric.reporter import LexisReporter
from lexismetric.evaluator import LexisMetric


async def run_eval():
    """Command to execute the API calls and generate raw logs."""
    evaluator = LexisMetric()
    await evaluator.run()


def run_report():
    """Command to generate HTML visualizations from the latest JSON log."""
    log_dir = Path("./logs")

    # Find the most recent JSON log file
    logs = sorted(log_dir.glob("eval_*.json"), reverse=True)

    if not logs:
        print("Error: No log files found in ./logs. Run an evaluation first.")
        return

    latest_log = logs[0]
    print(f"Generating report from: {latest_log}")

    with open(latest_log, "r") as f:
        data = json.load(f)

    reporter = LexisReporter(output_dir="./docs")
    report_path = reporter.generate(data)
    print(f"Report successfully generated at: {report_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: lm [run|report]")
        return

    command = sys.argv[1].lower()

    if command == "run":
        asyncio.run(run_eval())
    elif command == "report":
        run_report()
    else:
        print(f"Unknown command: {command}")
        print("Usage: lm [run|report]")


if __name__ == "__main__":
    main()
