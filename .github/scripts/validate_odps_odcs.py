#!/usr/bin/env python3
"""
ODPS/ODCS Validation Script
Validates dataproduct.yaml against official ODPS v4.0 schema
and contract files against ODCS schema.
"""

import json
import yaml
import jsonschema
import sys
from pathlib import Path

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Failed to read or parse YAML file {file_path}: {e}")
        return None

def load_json_schema(schema_path):
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema = json.load(file)
            print(f"✅ Schema loaded: {schema_path.name}")
            return schema
    except Exception as e:
        print(f"❌ Failed to load schema {schema_path}: {e}")
        return None

def validate_file(instance_data, schema, file_path, label):
    try:
        jsonschema.validate(instance=instance_data, schema=schema)
        print(f"✅ {label} validation successful: {file_path}")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ {label} validation error in {file_path}:\n   {e.message}")
        print(f"   Failed path: {' -> '.join(map(str, e.absolute_path))}")
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error in {file_path}: {e.message}")
        return False

def validate_yaml_files_in_dir(directory, schema, label):
    directory = Path(directory)
    files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
    if not files:
        print(f"⚠️  No YAML files found in {directory}")
        return True

    all_valid = True
    for file_path in files:
        print(f"🔍 Validating {label}: {file_path}")
        data = load_yaml_file(file_path)
        if data is None or not validate_file(data, schema, file_path, label):
            all_valid = False
    return all_valid

def check_naming_conventions(repo_root):
    print("🔍 Checking naming conventions...")
    issues = []

    for file in (repo_root / "contracts").glob("*.yaml"):
        name = file.name
        if not ('-v' in name and name.count('-') >= 2):
            issues.append(f"Contract filename '{name}' should match 'name-with-dashes-vX.Y.Z.yaml'")

    for file in repo_root.glob("*.yaml"):
        if not file.name.islower():
            issues.append(f"Root YAML filename '{file.name}' should be lowercase")

    if issues:
        print("⚠️  Naming issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    print("✅ Naming conventions OK")
    return True

def main():
    print("🚀 Starting ODPS/ODCS validation")
    print("=" * 50)

    base_dir = Path(__file__).resolve().parents[2]
    script_dir = Path(__file__).parent

    odps_file = base_dir / "dataproduct.yaml"
    odps_schema = load_json_schema(script_dir / "odps-schema-v4.0.json")

    odcs_dir = base_dir / "contracts"
    odcs_schema = load_json_schema(script_dir / "odcs-bitol-schema-v3.0.json")

    success = True

    if not odps_file.exists():
        print(f"❌ ODPS file not found: {odps_file}")
        success = False
    elif odps_schema:
        odps_data = load_yaml_file(odps_file)
        if odps_data is None or not validate_file(odps_data, odps_schema, odps_file, "ODPS"):
            success = False

    print("-" * 50)

    if odcs_schema:
        if not validate_yaml_files_in_dir(odcs_dir, odcs_schema, "ODCS"):
            success = False
    else:
        print("⚠️  ODCS schema missing — skipping ODCS validation")

    print("-" * 50)

    if not check_naming_conventions(base_dir):
        success = False

    print("=" * 50)

    if success:
        print("🎉 All validations passed successfully!")
        sys.exit(0)
    else:
        print("❌ Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
