#!/usr/bin/env python3
"""
Deterministic validator for artifact schemas.

Extracts JSON blocks from markdown artifacts and validates against JSON Schema.
Checks:
- JSON block exists in artifact
- JSON is valid and parseable
- Validates against the appropriate schema
- Required fields present
- Field types correct
- Enums matched
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts"


def extract_json_blocks(text: str) -> List[Dict[str, Any]]:
    """Extract all JSON code blocks from markdown text."""
    blocks = []
    pattern = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)
    for match in pattern.finditer(text):
        try:
            data = json.loads(match.group(1).strip())
            blocks.append(data)
        except json.JSONDecodeError:
            continue
    return blocks


def extract_json_block_by_type(text: str, block_type: str) -> Optional[Dict[str, Any]]:
    """Extract a specific JSON block by looking for type hints in comments."""
    blocks = extract_json_blocks(text)
    # If only one block, return it
    if len(blocks) == 1:
        return blocks[0]
    # Look for type hints in the block or preceding text
    for block in blocks:
        if block.get("artifact_type") or block.get("review_id") or block.get("status"):
            return block
    # Return first block if any
    return blocks[0] if blocks else None


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    # Try both naming conventions: name.json and name.schema.json
    for suffix in [".json", ".schema.json"]:
        schema_path = SCHEMA_DIR / f"{schema_name}{suffix}"
        if schema_path.exists():
            return json.loads(schema_path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Schema not found: {SCHEMA_DIR}/{schema_name}*.json")


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate data against a JSON schema. Returns list of error strings."""
    errors = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"CRITICAL: Missing required field '{field}'")

    # Check properties
    properties = schema.get("properties", {})
    for field, value in data.items():
        if field not in properties:
            if not schema.get("additionalProperties", True):
                errors.append(f"HIGH: Unexpected field '{field}'")
            continue

        prop_schema = properties[field]
        expected_type = prop_schema.get("type")

        # Handle nullable types
        if isinstance(expected_type, list):
            if value is None and "null" in expected_type:
                continue
            expected_type = [t for t in expected_type if t != "null"]
            if len(expected_type) == 1:
                expected_type = expected_type[0]
            else:
                continue  # Complex union type, skip type check

        # Type check
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"HIGH: Field '{field}' should be string, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"HIGH: Field '{field}' should be integer, got {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"HIGH: Field '{field}' should be boolean, got {type(value).__name__}")
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"HIGH: Field '{field}' should be array, got {type(value).__name__}")
            elif "items" in prop_schema:
                item_schema = prop_schema["items"]
                for i, item in enumerate(value):
                    if item_schema.get("type") == "object" and isinstance(item, dict):
                        item_errors = validate_against_schema(item, item_schema)
                        for ie in item_errors:
                            errors.append(f"MEDIUM: {field}[{i}]: {ie}")

        # Enum check
        if "enum" in prop_schema and value not in prop_schema["enum"]:
            errors.append(f"HIGH: Field '{field}' value '{value}' not in {prop_schema['enum']}")

        # Min/max check
        if "minimum" in prop_schema and isinstance(value, (int, float)):
            if value < prop_schema["minimum"]:
                errors.append(f"HIGH: Field '{field}' value {value} < minimum {prop_schema['minimum']}")
        if "maximum" in prop_schema and isinstance(value, (int, float)):
            if value > prop_schema["maximum"]:
                errors.append(f"HIGH: Field '{field}' value {value} > maximum {prop_schema['maximum']}")
        if "minLength" in prop_schema and isinstance(value, str):
            if len(value) < prop_schema["minLength"]:
                errors.append(f"HIGH: Field '{field}' length {len(value)} < minLength {prop_schema['minLength']}")

    return errors


def detect_schema_type(data: Dict[str, Any]) -> Optional[str]:
    """Detect which schema type the data matches."""
    if "review_id" in data or ("score" in data and "verdict" in data and "findings" in data):
        return "review_artifact"
    if "artifact_id" in data and "artifact_type" in data:
        return "agent_artifact"
    if "status" in data and "next_action" in data:
        return "gate_result"
    if "completed" in data and isinstance(data.get("completed"), dict):
        return "run_state"
    return None


def validate_artifact_schema(artifact_path: Path, schema_type: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Run schema validation on an artifact. Returns (passed, errors)."""
    content = artifact_path.read_text(encoding="utf-8")
    errors = []

    # Extract JSON blocks
    blocks = extract_json_blocks(content)
    if not blocks:
        errors.append("CRITICAL: No JSON code block found in artifact")
        return False, errors

    # Use first block or detect type
    data = blocks[0]
    if not schema_type:
        schema_type = detect_schema_type(data)

    if not schema_type:
        errors.append("CRITICAL: Cannot determine schema type from JSON block")
        return False, errors

    # Load schema
    try:
        schema = load_schema(schema_type)
    except FileNotFoundError as e:
        errors.append(f"CRITICAL: {e}")
        return False, errors

    # Validate
    schema_errors = validate_against_schema(data, schema)
    errors.extend(schema_errors)

    has_critical = any("CRITICAL" in e for e in errors)
    has_high = any("HIGH" in e for e in errors)
    passed = not has_critical and not has_high

    return passed, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_artifact_schema.py <artifact.md> [--type <schema_type>]")
        sys.exit(1)

    artifact_path = Path(sys.argv[1])
    if not artifact_path.exists():
        print(f"File not found: {artifact_path}")
        sys.exit(1)

    schema_type = None
    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        if idx + 1 < len(sys.argv):
            schema_type = sys.argv[idx + 1]

    passed, errors = validate_artifact_schema(artifact_path, schema_type)

    if passed:
        print(f"PASS: {artifact_path.name} (schema: {schema_type or 'auto'})")
    else:
        print(f"FAIL: {artifact_path.name}")

    for error in sorted(errors):
        print(f"  {error}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
