#!/bin/bash
# Create a new experiment run directory

set -e

if [ -z "$1" ]; then
    echo "Usage: ./new-run.sh <experiment-name>"
    echo "Example: ./new-run.sh hermes-perm-audit-001"
    exit 1
fi

NAME="$1"
DATE=$(date +%Y-%m-%d)
DIR="runs/${DATE}-${NAME}"

if [ -d "$DIR" ]; then
    echo "Error: Run directory already exists: $DIR"
    exit 1
fi

echo "Creating run directory: $DIR"

# Create directory structure
mkdir -p "$DIR"/{model_outputs,traces,cross_audit,distilled_wiki_notes}

# Copy templates
cp config/run-template/task.md "$DIR/"
cp config/run-template/cost_estimate.md "$DIR/"
cp config/run-template/decision_record.md "$DIR/"
cp config/run-template/failure_analysis.md "$DIR/"
cp config/run-template/wiki_note.md "$DIR/distilled_wiki_notes/"
cp config/run-template/next_experiment.md "$DIR/"
cp config/run-template/evaluator_rule.md "$DIR/"

echo "Done! Edit $DIR/task.md to define your experiment."
