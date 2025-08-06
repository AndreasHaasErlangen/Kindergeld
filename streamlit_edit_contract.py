import streamlit as st
import json
import os

def render_field(key, schema, data):
    field_type = schema.get("type")
    description = schema.get("description", "")
    default = data.get(key, schema.get("default"))

    if field_type == "string":
        if "enum" in schema:
            data[key] = st.selectbox(f"{description}", schema["enum"], index=schema["enum"].index(default) if default in schema["enum"] else 0)
        else:
            data[key] = st.text_input(f"{description}", value=default or "")
    elif field_type == "array":
        item_type = schema.get("items", {}).get("type", "string")
        st.text(f"{description} (comma-separated values)")
        raw = st.text_input(key, value=", ".join(map(str, default)) if isinstance(default, list) else "")
        data[key] = [x.strip() for x in raw.split(",")] if raw else []
    elif field_type == "object":
        st.markdown(f"**{key}**: {description}")
        with st.expander(f"Details for {key}", expanded=True):
            if "properties" in schema:
                data[key] = data.get(key, {})
                for subkey, subschema in schema["properties"].items():
                    render_field(subkey, subschema, data[key])
    else:
        st.warning(f"Unsupported field type: {field_type} for '{key}'")

def main():
    st.title("Open Data Contract Editor")

    # Load schema
    with open(".github/scripts/odcs-bitol-schema-v3.0.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Load or start new contract
    existing_contract = None
    uploaded = st.file_uploader("Load existing data contract (JSON)", type=["json"])
    if uploaded:
        existing_contract = json.load(uploaded)
    else:
        existing_contract = {}

    contract_data = existing_contract.copy()

    st.header("Fill in the data contract fields")

    for key, subschema in schema.get("properties", {}).items():
        render_field(key, subschema, contract_data)

    if st.button("Save Data Contract"):
        json_data = json.dumps(contract_data, indent=2, ensure_ascii=False)
        st.download_button("Download JSON", json_data, file_name="data_contract.json", mime="application/json")

if __name__ == "__main__":
    main()
