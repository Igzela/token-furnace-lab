#!/bin/bash
# Distill knowledge from a completed run

set -e

if [ -z "$1" ]; then
    echo "Usage: ./distill.sh <run-directory>"
    echo "Example: ./distill.sh runs/2026-05-27-hermes-perm-audit-001"
    exit 1
fi

RUN_DIR="$1"

if [ ! -d "$RUN_DIR" ]; then
    echo "Error: Run directory not found: $RUN_DIR"
    exit 1
fi

echo "=== Knowledge Distillation ==="
echo "Run: $RUN_DIR"

# Check required files
REQUIRED_FILES=("task.md" "cost_estimate.md" "failure_analysis.md")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$RUN_DIR/$file" ]; then
        echo "Warning: Missing $file"
    fi
done

# Check for model outputs
OUTPUT_COUNT=$(ls -1 "$RUN_DIR/model_outputs/" 2>/dev/null | wc -l)
echo "Model outputs found: $OUTPUT_COUNT"

# Check for wiki notes
WIKI_COUNT=$(ls -1 "$RUN_DIR/distilled_wiki_notes/" 2>/dev/null | wc -l)
echo "Wiki notes created: $WIKI_COUNT"

# Generate summary
echo ""
echo "=== Distillation Checklist ==="
echo "[ ] Wiki notes moved to knowledge/wiki/"
echo "[ ] Rules extracted to knowledge/evaluator-rules/"
echo "[ ] Failures documented in knowledge/failures/"
echo "[ ] Decision recorded in knowledge/decisions/"
echo "[ ] Next experiment defined"

echo ""
echo "Run 'ls $RUN_DIR' to review outputs."
