import argparse
import json
import sys

from rich.console import Console
from rich.table import Table

from .pipeline import run_pipeline
from .project import project
from .schema import validate_output

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", help="Path to recruiter CSV export")
    parser.add_argument("--json", help="Path to ATS JSON blob")
    parser.add_argument("--resume", action="append", default=[], help="Path to a resume PDF (repeatable)")
    parser.add_argument("--config", help="Path to a runtime output config JSON file")
    parser.add_argument("--out", help="Write JSON output to this file instead of stdout")
    args = parser.parse_args()

    if not (args.csv or args.json or args.resume):
        console.print("[red]Error:[/red] provide at least one of --csv, --json, --resume")
        sys.exit(1)

    results = run_pipeline(csv_path=args.csv, json_path=args.json, resume_paths=args.resume)

    config = None
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            config = json.load(f)

    final_output = []
    for canonical in results:
        shaped = project(canonical, config)
        errors = validate_output(shaped) if config is None else []
        final_output.append(shaped)
        console.print(f"\nCandidate: {canonical.get('candidate_id')}")
        console.print_json(data=shaped)
        if errors:
            console.print(f"[yellow]Validation warnings:[/yellow] {errors}")

    output_json = json.dumps(final_output, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output_json)
        console.print(f"\n[green]Output written to {args.out}[/green]")
    else:
        console.print("\n[bold]Full JSON output:[/bold]")
        print(output_json)


if __name__ == "__main__":
    main()
