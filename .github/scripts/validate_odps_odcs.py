#!/usr/bin/env python3
"""
ODPS/ODCS Validation Script
Validates dataproduct.yaml against official ODPS v4.0 schema
and contract files against ODCS schema.
"""

import json
import yaml
import jsonschema
import requests
import sys
import os
from pathlib import Path

def load_yaml_file(file_path):
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error in {file_path}: {e}")
        return None

def load_local_odps_schema():
    """Load local ODPS schema from .github/scripts/."""
    schema_path = Path(__file__).parent / "odps-schema-v4.0.json"
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema = json.load(file)
            print(f"✅ Local ODPS schema loaded: {schema_path.name}")
            return schema
    except FileNotFoundError:
        print(f"❌ ODPS schema file not found: {schema_path}")
        print("💡 Please download from: https://opendataproducts.org/v4.0/schema/odps.yaml")
        print("   Convert to JSON and save as odps-schema-v4.0.json")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error in ODPS schema: {e}")
        return None

def load_local_odcs_schema():
    """Load local ODCS schema from .github/scripts/."""
    # Try bitol-io ODCS first (more comprehensive)
    bitol_schema_path = Path(__file__).parent / "odcs-bitol-schema-v3.0.json"
    #datacontract_schema_path = Path(__file__).parent / "odcs-datacontract-schema.json"
    
    #for schema_path in [bitol_schema_path, datacontract_schema_path]:
    for schema_path in [bitol_schema_path]:        
        try:
            with open(schema_path, 'r', encoding='utf-8') as file:
                schema = json.load(file)
                print(f"✅ Local ODCS schema loaded: {schema_path.name}")
                return schema
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error in {schema_path}: {e}")
            continue
    
    print("❌ No ODCS schema file found. Please download one of:")
    print("   - ODCS bitol-io: https://raw.githubusercontent.com/bitol-io/open-data-contract-standard/main/schema/odcs-json-schema-latest.json")
    print("   - Data Contract: https://raw.githubusercontent.com/datacontract/datacontract-specification/main/definition.schema.json")
    print("   Save as: odcs-bitol-schema-v3.0.json or odcs-datacontract-schema.json")
    return None

def validate_odps_file(odps_file_path, odps_schema):
    """Validate ODPS file against schema."""
    print(f"🔍 Validating ODPS file: {odps_file_path}")
    
    odps_data = load_yaml_file(odps_file_path)
    if odps_data is None:
        return False
    
    try:
        jsonschema.validate(instance=odps_data, schema=odps_schema)
        print(f"✅ ODPS validation successful: {odps_file_path}")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ ODPS validation error in {odps_file_path}:")
        print(f"   Error: {e.message}")
        print(f"   Failed path: {' -> '.join(str(p) for p in e.absolute_path)}")
        
        # Show missing required fields more clearly
        if "required" in str(e.message):
            print("💡 Tip: Check if all required fields are present and correctly named")
        
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error: {e.message}")
        return False

def validate_odcs_contracts(contracts_dir, odcs_schema):
    """Validate all ODCS contract files against the loaded schema."""
    contracts_path = Path(contracts_dir)
    
    if not contracts_path.exists():
        print(f"❌ Contracts directory not found: {contracts_dir}")
        return False
    
    yaml_files = list(contracts_path.glob("*.yaml")) + list(contracts_path.glob("*.yml"))
    
    if not yaml_files:
        print(f"⚠️  No YAML files found in {contracts_dir}")
        return True
    
    all_valid = True
    for contract_file in yaml_files:
        print(f"🔍 Validating ODCS contract: {contract_file}")
        
        contract_data = load_yaml_file(contract_file)
        if contract_data is None:
            all_valid = False
            continue
        
        # Schema validation if available
        if odcs_schema:
            try:
                jsonschema.validate(instance=contract_data, schema=odcs_schema)
                print(f"✅ ODCS schema validation passed: {contract_file}")
            except jsonschema.ValidationError as e:
                print(f"❌ ODCS schema validation error in {contract_file}:")
                print(f"   Error: {e.message}")
                print(f"   Failed path: {' -> '.join(str(p) for p in e.absolute_path)}")
                all_valid = False
                continue
        
        # Additional structure validation
        if not validate_odcs_structure(contract_data, contract_file):
            all_valid = False
        else:
            print(f"✅ ODCS contract structure valid: {contract_file}")
    
    return all_valid

def validate_odcs_structure(contract_data, file_path):
    """Basic validation of ODCS contract structure."""
    required_sections = ['dataContractSpecification', 'id', 'info']
    
    for section in required_sections:
        if section not in contract_data:
            print(f"❌ Missing required section '{section}' in {file_path}")
            return False
    
    # Validate version format if present
    if 'info' in contract_data and 'version' in contract_data['info']:
        version = contract_data['info']['version']
        if not isinstance(version, str) or not version.startswith('v'):
            print(f"⚠️  Version should follow semantic versioning format 'vX.Y.Z' in {file_path}")
    
    return True

def check_file_naming_conventions(base_dir):
    """Check if files follow the defined naming conventions."""
    print("🔍 Checking naming conventions...")
    
    issues = []
    base_path = Path(base_dir)
    
    # Check YAML files in contracts/
    contracts_dir = base_path / "contracts"
    if contracts_dir.exists():
        for yaml_file in contracts_dir.glob("*.yaml"):
            filename = yaml_file.name
            # Expected format: name-with-dashes-vX.Y.Z.yaml
            if not ('-v' in filename and filename.count('-') >= 2):
                issues.append(f"Contract file naming: {filename} should follow 'name-with-dashes-vX.Y.Z.yaml'")
    
    # Check root level YAML files
    for yaml_file in base_path.glob("*.yaml"):
        filename = yaml_file.name
        if not filename.islower():
            issues.append(f"Root YAML file: {filename} should be lowercase")
    
    if issues:
        print("⚠️  Naming convention issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Naming conventions are consistent")
        return True

def main():
    """Main validation function."""
    print("🚀 Starting ODPS/ODCS validation")
    print("=" * 50)
    
    # Set base directory (repository root)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    
    # File paths
    odps_file = repo_root / "dataproduct.yaml"
    contracts_dir = repo_root / "contracts"
    
    validation_success = True
    
    # 1. Load schemas from local files
    odps_schema = load_local_odps_schema()
    if odps_schema is None:
        print("❌ Could not load ODPS schema. Aborting.")
        sys.exit(1)
    
    odcs_schema = load_local_odcs_schema()
    if odcs_schema is None:
        print("⚠️  No ODCS schema found. Using basic structure validation only.")
    
    # 2. Validate ODPS file
    if not odps_file.exists():
        print(f"❌ ODPS file not found: {odps_file}")
        validation_success = False
    else:
        if not validate_odps_file(odps_file, odps_schema):
            validation_success = False
    
    print("-" * 50)
    
    # 3. Validate ODCS contracts
    if not validate_odcs_contracts(contracts_dir, odcs_schema):
        validation_success = False
    
    print("-" * 50)
    
    # 4. Check naming conventions
    if not check_file_naming_conventions(repo_root):
        validation_success = False
    
    print("=" * 50)
    
    # Final result
    if validation_success:
        print("🎉 All validations passed successfully!")
        sys.exit(0)
    else:
        print("❌ Validation failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()