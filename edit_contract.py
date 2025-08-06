import yaml
import json
import questionary
from pathlib import Path
from jsonschema import validate, ValidationError

# Paths (adjust if needed)
SCHEMA_PATH = Path(".github/scripts/odcs-bitol-schema-v3.0.json")
DEFAULT_CONTRACT_PATH = Path("contracts/bestandsdaten-kg-estg-v1.0.0.yaml")

# Load JSON schema
def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Load or initialize contract data
def load_contract(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            print(f"✅ Loaded existing contract: {path}")
            return yaml.safe_load(f)
    else:
        print(f"⚠️  No existing contract found at {path}, starting fresh.")
        return {}

# Interactive editing
def edit_contract(data, schema):
    properties = schema.get("properties", {})

    for key, props in properties.items():
        current = data.get(key, "")
        if isinstance(props.get("type"), str):
            new_val = questionary.text(
                f"{props.get('description', key)} [{current}]:",
                default=str(current) if current else ""
            ).ask()

            if new_val:
                if props["type"] == "string":
                    data[key] = new_val
                elif props["type"] == "number":
                    data[key] = float(new_val)
                elif props["type"] == "integer":
                    data[key] = int(new_val)
                elif props["type"] == "boolean":
                    data[key] = new_val.lower() in ["true", "yes", "1"]
        elif props.get("type") == "array":
            print(f"Editing list field '{key}':")
            if current:
                print(f"Current items: {current}")
            items = questionary.text(f"Enter comma-separated values for '{key}':").ask()
            if items:
                data[key] = [item.strip() for item in items.split(",")]

    return data

# Validate contract against schema
def validate_contract(data, schema):
    try:
        validate(instance=data, schema=schema)
        print("✅ Contract is valid according to schema.")
        return True
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        print(f"   at {' -> '.join(map(str, e.absolute_path))}")
        return False

# Save YAML
def save_contract(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False)
    print(f"💾 Contract saved to: {path}")

def main():
    schema = load_schema(SCHEMA_PATH)
    
    # Ask for file
    file_path = questionary.text(
        f"Enter path to data contract file",
        default=str(DEFAULT_CONTRACT_PATH)
    ).ask()
    
    path = Path(file_path)
    data = load_contract(path)
    
    updated_data = edit_contract(data, schema)

    if validate_contract(updated_data, schema):
        save_contract(path, updated_data)
    else:
        print("⚠️  Contract is invalid. Changes not saved.")

if __name__ == "__main__":
    main()
