import os
import yaml
import jsonschema
from pathlib import Path

# === ODCS Validation Schema (simplified) ===
ODCS_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "version", "schema"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "version": {"type": "string"},
        "schema": {"type": "object"}
    }
}

# === Load YAML ===
def load_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# === Validate ODCS Contract File ===
def validate_odcs_file(odcs_file):
    print(f"🧪 Validating ODCS file: {odcs_file}")
    odcs_data = load_yaml(odcs_file)
    try:
        jsonschema.validate(instance=odcs_data, schema=ODCS_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"❌ ODCS validation error in {odcs_file}:\n{e.message}")
    print(f"✅ {odcs_file.name} is ODCS-valid")

# === Validate ODPS File ===
def validate_odps_file(odps_file, odps_schema_path):
    print(f"🔍 Validating ODPS file: {odps_file}")
    odps_data = load_yaml(odps_file)
    odps_schema = load_yaml(odps_schema_path)

    try:
        jsonschema.validate(instance=odps_data, schema=odps_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"❌ ODPS validation error in {odps_file}:\n{e.message}")
    print("✅ ODPS file is schema-valid")

    # Check referenced ODCS contracts
    referenced_contracts = []
    for comp in odps_data.get("components", []):
        for contract in comp.get("contracts", []):
            referenced_contracts.append(contract)

    for contract_file in referenced_contracts:
        contract_path = Path("contracts") / contract_file
        if not contract_path.exists():
            raise FileNotFoundError(f"🚫 Referenced contract not found: {contract_path}")
        validate_odcs_file(contract_path)

# === Main Logic ===
def main():
    odps_file = Path("dataproduct.yaml")
    odps_schema_file = Path(".github/scripts/odps_schema.json")
    if not odps_file.exists():
        raise FileNotFoundError("ODPS file 'dataproduct.yaml' not found in root directory.")
    if not odps_schema_file.exists():
        raise FileNotFoundError("ODPS schema file not found.")

    validate_odps_file(odps_file, odps_schema_file)

    # Validate all ODCS contracts in contracts/
    for odcs_file in Path("contracts").glob("*.yaml"):
        validate_odcs_file(odcs_file)

    print("🎉 All validations passed successfully.")

if __name__ == "__main__":
    main()
