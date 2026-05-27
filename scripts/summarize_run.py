#!/usr/bin/env python3
"""Generate a summary report from a run directory."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return "(not found)"


def main():
    parser = argparse.ArgumentParser(description="Summarize a run")
    parser.add_argument("run_dir", help="Path to run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)

    # Load run metadata
    run_yaml = run_dir / "run.yaml"
    meta = {}
    if run_yaml.exists():
        with open(run_yaml) as f:
            meta = yaml.safe_load(f) or {}

    experiment_id = meta.get("experiment_id", "unknown")
    timestamp = meta.get("timestamp", "unknown")
    operator = meta.get("operator", "unknown")
    target = meta.get("target_repo", "unknown")
    status = meta.get("status", "unknown")

    # Collect model outputs
    model_outputs = {}
    model_dir = run_dir / "model-outputs"
    if model_dir.exists():
        for f in sorted(model_dir.glob("*.md")):
            model_outputs[f.stem] = f.read_text()

    # Collect synthesis
    synthesis = {}
    synth_dir = run_dir / "synthesis"
    if synth_dir.exists():
        for f in sorted(synth_dir.glob("*.md")):
            synthesis[f.stem] = f.read_text()

    # Collect metrics
    metrics = {}
    metrics_dir = run_dir / "metrics"
    if metrics_dir.exists():
        for f in sorted(metrics_dir.glob("*.md")):
            metrics[f.stem] = f.read_text()

    # Generate report
    report = []
    report.append(f"# Run Summary: {experiment_id}")
    report.append(f"")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append(f"")
    report.append(f"## Metadata")
    report.append(f"- Experiment: {experiment_id}")
    report.append(f"- Timestamp: {timestamp}")
    report.append(f"- Operator: {operator}")
    report.append(f"- Target: {target}")
    report.append(f"- Status: {status}")
    report.append(f"")

    report.append(f"## Model Outputs ({len(model_outputs)}/3)")
    for name, content in model_outputs.items():
        lines = content.strip().split("\n")
        word_count = len(content.split())
        report.append(f"- **{name}**: {len(lines)} lines, {word_count} words")
    report.append(f"")

    report.append(f"## Synthesis ({len(synthesis)} files)")
    for name in synthesis:
        report.append(f"- {name}")
    report.append(f"")

    report.append(f"## Metrics ({len(metrics)} files)")
    for name in metrics:
        report.append(f"- {name}")
    report.append(f"")

    # Write report
    report_path = run_dir / "summary.md"
    report_path.write_text("\n".join(report))
    print(f"Summary written to: {report_path}")
    print(f"Model outputs: {len(model_outputs)}/3")
    print(f"Synthesis files: {len(synthesis)}")
    print(f"Metric files: {len(metrics)}")


if __name__ == "__main__":
    main()
