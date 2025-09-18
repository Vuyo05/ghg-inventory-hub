import streamlit as st
import os
import yaml
import pandas as pd
from datetime import datetime, date
import logging

# Try to import supabase client; handle gracefully if missing
SUPABASE_AVAILABLE = True
try:
    from supabase import create_client, Client
except Exception:
    SUPABASE_AVAILABLE = False

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helpers ---
def get_supabase_client():
    """Return a Supabase client or None if not configured/installed."""
    if not SUPABASE_AVAILABLE:
        logger.error("Supabase client not available.")
        return None
    url = os.environ.get("SUPABASE_URL", "https://ahrtfdgutdoghoydyluo.supabase.co")
    key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFocnRmZGd1dGRvZ2hveWR5bHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzNzM4NTQsImV4cCI6MjA2OTk0OTg1NH0.He6WmGiMaP4HJsJr1eMZ5y4of_P_IZq-AtKU1L6B4g4")
    if not url or not key:
        logger.error("Supabase URL or key not configured.")
        return None
    return create_client(url, key)

def load_yaml_file(file_path):
    """Load and parse a YAML file, returning its contents or raising an error."""
    if not os.path.exists(file_path):
        st.error(f"YAML file not found: {file_path}")
        logger.error(f"YAML file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        st.error(f"Error parsing YAML file {file_path}: {e}")
        logger.error(f"Error parsing YAML file {file_path}: {e}")
        return None

def convert_units(value, from_unit, to_unit):
    """Convert units based on simple rules for mass and volume."""
    if from_unit == to_unit:
        return value
    if value is None or value == "":
        return None
    try:
        value = float(value)
        if from_unit in ["kg"] and to_unit in ["tonnes"]:
            return value / 1000
        elif from_unit in ["lb"] and to_unit in ["tonnes"]:
            return value * 0.000453592
        elif from_unit in ["tonnes"] and to_unit in ["kg"]:
            return value * 1000
        elif from_unit in ["lb"] and to_unit in ["kg"]:
            return value * 0.453592
        elif from_unit in ["kg"] and to_unit in ["lb"]:
            return value * 2.20462
        elif from_unit in ["kg C"] and to_unit in ["tonnes C"]:
            return value / 1000
        elif from_unit in ["tonnes C"] and to_unit in ["kg C"]:
            return value * 1000
        else:
            st.warning(f"Conversion from {from_unit} to {to_unit} not supported. Using original value.")
            logger.warning(f"Conversion from {from_unit} to {to_unit} not supported.")
            return value
    except (ValueError, TypeError):
        st.error(f"Invalid value '{value}' for conversion from {from_unit} to {to_unit}")
        logger.error(f"Invalid value '{value}' for conversion from {from_unit} to {to_unit}")
        return None

def render_field(field_config, form_data, key_prefix=""):
    """Render a single field based on its YAML configuration."""
    field_name = field_config['name']
    full_key = f"{key_prefix}{field_name}" if key_prefix else field_name
    value = form_data.get(field_name, field_config.get('default', ''))
    unit_key = f"{full_key}_unit"

    if 'condition' in field_config:
        condition = field_config['condition']
        if not eval(condition, {}, {k: form_data.get(k) for k in form_data.keys()}):
            return

    if field_config['type'] == 'text':
        form_data[field_name] = st.text_input(field_config['label'], value=value, key=full_key)
    elif field_config['type'] == 'number':
        default_value = float(value) if value and value != '' else 0.0
        form_data[field_name] = st.number_input(
            field_config['label'],
            value=default_value,
            key=full_key,
            min_value=field_config.get('validation', {}).get('min', 0.0),
            step=0.01,
            format="%.2f"
        )
        if 'unit_options' in field_config:
            current_unit = form_data.get(unit_key, field_config.get('unit_options', [field_config.get('required_unit', '')])[0])
            form_data[unit_key] = st.selectbox(
                "Unit",
                options=field_config['unit_options'],
                index=field_config['unit_options'].index(current_unit) if current_unit in field_config['unit_options'] else 0,
                key=f"{unit_key}_select"
            )
    elif field_config['type'] == 'date':
        form_data[field_name] = st.date_input(
            field_config['label'],
            value=value if isinstance(value, date) else (datetime.strptime(value, '%Y-%m-%d').date() if isinstance(value, str) and value else datetime.now().date()),
            key=full_key
        )
    elif field_config['type'] == 'select':
        try:
            index = field_config['options'].index(value) if value and value in field_config['options'] else 0
        except ValueError:
            index = 0
            value = field_config['options'][0] if field_config['options'] else ''
            form_data[field_name] = value
        form_data[field_name] = st.selectbox(
            field_config['label'],
            options=field_config['options'],
            index=index,
            key=full_key
        )
    elif field_config['type'] == 'radio':
        form_data[field_name] = st.radio(
            field_config['label'],
            options=field_config['options'],
            index=field_config['options'].index(value) if value and value in field_config['options'] else 0,
            key=full_key
        )
    elif field_config['type'] == 'multiselect':
        valid_default = [v for v in (value if isinstance(value, list) else [value]) if v in field_config['options']] if value else []
        form_data[field_name] = st.multiselect(
            field_config['label'],
            options=field_config['options'],
            default=valid_default,
            key=full_key
        )
    elif field_config['type'] == 'hidden':
        form_data[field_name] = field_config.get('value', '')

    if field_config.get('unit') and 'unit_options' not in field_config:
        st.write(f"Unit: {field_config['unit']}")

def render_table(table_config, form_data, key_prefix=""):
    """Render a table based on its YAML configuration."""
    table_name = table_config['name']
    columns = table_config['columns']
    full_key = f"{key_prefix}{table_name}_table"

    if f"{table_name}_data" not in form_data:
        form_data[f"{table_name}_data"] = [{}]
    table_data = form_data[f"{table_name}_data"]

    edited_data = []
    for row in table_data:
        new_row = row.copy()
        for col in columns:
            col_name = col.get('name')
            if col.get('type', 'text') == 'number' and 'unit_options' in col:
                unit_key = f"{col_name}_unit"
                current_unit = row.get(unit_key, col.get('unit_options', [col.get('required_unit', '')])[0])
                new_row[unit_key] = current_unit
        edited_data.append(new_row)

    column_config = {}
    for col in columns:
        col_name = col.get('name')
        if col.get('type', 'text') == 'number' and 'unit_options' in col:
            column_config[col_name] = st.column_config.NumberColumn(
                col.get('label', col_name),
                help=f"Unit: {col.get('required_unit', col.get('unit_options', [''])[0])}",
                min_value=col.get('validation', {}).get('min', 0.0),
                step=0.01,
                format="%.2f"
            )
        else:
            column_config[col_name] = col.get('label', col_name)

    edited_df = st.data_editor(
        pd.DataFrame(edited_data, columns=[col.get('name') for col in columns] + [f"{col.get('name')}_unit" for col in columns if col.get('type', 'text') == 'number' and 'unit_options' in col]),
        column_config=column_config,
        key=full_key
    )

    form_data[f"{table_name}_data"] = []
    for _, row in edited_df.iterrows():
        new_row = {}
        for col in columns:
            col_name = col.get('name')
            new_row[col_name] = row[col_name]
            if col.get('type', 'text') == 'number' and 'unit_options' in col:
                unit_key = f"{col_name}_unit"
                new_row[unit_key] = row[unit_key] if unit_key in row else col.get('unit_options', [col.get('required_unit', '')])[0]
        form_data[f"{table_name}_data"].append(new_row)

def submit_subcategory_data(subcategory, form_data, form_config, supabase):
    """Submit data for a single subcategory to its validation table."""
    validation_table = {
        "4A1_A_Managed_Landfills": "waste_4a1a_validation",
        "4A1_B_Managed_Controlled_Dumpsites": "waste_4a1b_validation",
        "4A2_Unmanaged_Dumpsites": "waste_4a2_validation",
        "4A3_Uncategorized_Dumpsites": "waste_4a3_validation",
        "4B_Biological_Treatment": "waste_4b_validation",
        "4C1_Waste_Incineration": "waste_4c1_validation",
        "4C2_Open_Burning": "waste_4c2_validation",
        "4D_Wastewater_Treatment": "waste_4d_validation",
        "4E_Other": "waste_4e_validation"
    }.get(subcategory)

    if not validation_table:
        st.error(f"No validation table defined for {subcategory}")
        logger.error(f"No validation table defined for {subcategory}")
        return False

    data_year = form_data.get("data_year")
    if isinstance(data_year, list):
        data_year = [int(data_year[0])] if data_year else [2023]
    elif data_year is None or data_year == '':
        data_year = [2023]
    else:
        data_year = [int(data_year)]

    data = {
        "data_year": data_year,
        "waste_subcategory": subcategory,
        "status": "Pending",
        "submission_date": datetime.now().isoformat()
    }

    general_fields = ['name', 'email', 'data_provider', 'provider_contact_person', 'position', 'contact_email', 'contact_phone', 'data_request_date', 'data_supply_date']
    for field in general_fields:
        if field in form_data:
            value = form_data[field]
            if isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, list):
                value = value[0] if value else None
            data[field] = value

    for field in form_config.get('fields', []) + form_config.get('fields_after_tables', []):
        field_name = field['name']
        prefixed_key = f"{subcategory.replace(' ', '_').replace('–', '_')}_{field_name}"
        if prefixed_key in form_data:
            value = form_data[prefixed_key]
            unit_key = f"{prefixed_key}_unit"
            if field.get('type') == 'number' and 'unit_options' in field:
                current_unit = form_data.get(unit_key, field.get('unit_options', [field.get('required_unit', '')])[0])
                required_unit = field.get('required_unit', field.get('unit_options', [''])[0])
                if current_unit != required_unit:
                    value = convert_units(value, current_unit, required_unit)
            data[field_name] = value

    for table in form_config.get('tables', []):
        table_name = table['name']
        table_data_key = f"{subcategory.replace(' ', '_').replace('–', '_')}_{table_name}_data"
        if table_data_key in form_data:
            for row in form_data[table_data_key]:
                row_data = data.copy()
                for col in table['columns']:
                    col_name = col.get('name')
                    if col_name in row:
                        value = row[col_name]
                        if col.get('type', 'text') == 'number' and 'unit_options' in col:
                            unit_key = f"{col_name}_unit"
                            current_unit = row.get(unit_key, col.get('unit_options', [col.get('required_unit', '')])[0])
                            required_unit = col.get('required_unit', col.get('unit_options', [''])[0])
                            if current_unit != required_unit:
                                value = convert_units(value, current_unit, required_unit)
                        row_data[col_name] = value
                try:
                    response = supabase.table(validation_table).insert(row_data).execute()
                    if response.data:
                        logger.info(f"Data inserted into {validation_table}: {row_data}")
                    else:
                        st.error(f"Failed to insert table row into {validation_table}: {response}")
                        logger.error(f"Failed to insert table row into {validation_table}: {response}")
                        return False
                except Exception as e:
                    st.error(f"Error inserting table row into {validation_table}: {e}")
                    logger.error(f"Error inserting table row into {validation_table}: {e}")
                    return False

    if not form_config.get('tables') or any(field['name'] in data for field in form_config.get('fields', []) + form_config.get('fields_after_tables', [])):
        try:
            response = supabase.table(validation_table).insert(data).execute()
            if response.data:
                logger.info(f"Data inserted into {validation_table}: {data}")
                return True
            else:
                st.error(f"Failed to insert data into {validation_table}: {response}")
                logger.error(f"Failed to insert data into {validation_table}: {response}")
                return False
        except Exception as e:
            st.error(f"Error inserting data into {validation_table}: {e}")
            logger.error(f"Error inserting data into {validation_table}: {e}")
            return False
    return True

def waste_data_form():
    st.title("Waste Data Submission Form")
    supabase = get_supabase_client()

    if not supabase:
        st.error("Supabase client not initialized. Please check environment variables.")
        return

    # Define subcategory_map at function level
    subcategory_map = {
        "4A - Solid Waste Disposal": [
            "4A1_A_Managed_Landfills",
            "4A1_B_Managed_Controlled_Dumpsites",
            "4A2_Unmanaged_Dumpsites",
            "4A3_Uncategorized_Dumpsites"
        ],
        "4B - Biological Treatment of Solid Waste": ["4B_Biological_Treatment"],
        "4C - Incineration and Open Burning of Waste": ["4C1_Waste_Incineration", "4C2_Open_Burning"],
        "4D - Wastewater Treatment and Discharge": ["4D_Wastewater_Treatment"],
        "4E - Other": ["4E_Other"]
    }

    if "page" not in st.session_state:
        st.session_state.page = "provider"
    if "current_step" not in st.session_state:
        st.session_state.current_step = "general_info"
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "all_forms_completed" not in st.session_state:
        st.session_state.all_forms_completed = False
    if "selected_subcategories" not in st.session_state:
        st.session_state.selected_subcategories = []
    if "current_subcategory_index" not in st.session_state:
        st.session_state.current_subcategory_index = 0

    if st.session_state.current_step == "general_info":
        st.subheader("General Information")
        forms_dir = os.path.join(os.path.dirname(__file__), "forms")
        general_yaml_path = os.path.join(forms_dir, "general_w.yaml")  # Updated to general_w.yaml
        general_config = load_yaml_file(general_yaml_path)

        if general_config:
            with st.form("general_info_form"):
                required_fields = [field['name'] for field in general_config['fields'] if field.get('required', False)]
                for field in general_config['fields']:
                    render_field(field, st.session_state.form_data)

                if st.form_submit_button("Next"):
                    if all(st.session_state.form_data.get(f) for f in required_fields):
                        if 'data_year' in st.session_state.form_data:
                            if isinstance(st.session_state.form_data['data_year'], list):
                                st.session_state.form_data['data_year'] = [int(st.session_state.form_data['data_year'][0])] if st.session_state.form_data['data_year'] else [2023]
                        st.session_state.current_step = "subcategory_forms"
                        st.session_state.selected_subcategories = st.session_state.form_data.get('waste_subcategory', [])
                        st.session_state.current_subcategory_index = 0
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields.")
        if st.button("← Back to Sector Selection"):
            st.session_state.page = "provider"
            st.session_state.current_step = "general_info"
            st.session_state.form_data = {}
            st.rerun()

    elif st.session_state.current_step == "subcategory_forms":
        if not st.session_state.selected_subcategories:
            st.error("No subcategories selected. Please go back and select at least one.")
            if st.button("← Back to General Info"):
                st.session_state.current_step = "general_info"
                st.rerun()
        else:
            current_subcategory = st.session_state.selected_subcategories[st.session_state.current_subcategory_index]
            st.subheader(f"{current_subcategory} Data Entry")

            forms_dir = os.path.join(os.path.dirname(__file__), "forms")
            index_yaml_path = os.path.join(forms_dir, "index_w.yaml")  # Updated to index_w.yaml
            index_config = load_yaml_file(index_yaml_path)

            if index_config:
                current_subsubcategory = subcategory_map.get(current_subcategory)
                if isinstance(current_subsubcategory, list):
                    def on_subsubcategory_change():
                        for key in list(st.session_state.form_data.keys()):
                            if key.startswith(current_subcategory.replace(" ", "_").replace("-", "_").lower()):
                                st.session_state.form_data.pop(key)
                    selected_subsubcategory = st.selectbox(
                        "Select Sub-Subcategory",
                        options=current_subsubcategory,
                        key="subsubcategory_select",
                        on_change=on_subsubcategory_change
                    )
                    current_subsubcategory = selected_subsubcategory
                else:
                    current_subsubcategory = current_subsubcategory[0] if current_subsubcategory else current_subcategory.replace(" ", "_").replace("-", "_")

                logger.info(f"Looking up subcategory: {current_subsubcategory}")
                subcategory_config = next((item for item in index_config['forms'] if item['name'] == current_subsubcategory), None)
                if subcategory_config:
                    yaml_path = os.path.join(forms_dir, subcategory_config['path'])
                    form_config = load_yaml_file(yaml_path)
                    logger.info(f"Loaded form config for {current_subsubcategory}: {yaml_path}")

                    if form_config:
                        with st.form(f"form_{current_subsubcategory.replace(' ', '_').replace('–', '_')}"):
                            data_year_value = st.session_state.form_data.get('data_year', [2023])
                            if isinstance(data_year_value, list):
                                data_year_value = int(data_year_value[0]) if data_year_value else 2023
                            st.session_state.form_data['data_year'] = [st.number_input(
                                "Data Year",
                                min_value=2000,
                                max_value=2025,
                                value=data_year_value,
                                key="data_year",
                                step=1
                            )]

                            for field in form_config.get('fields', []):
                                render_field(field, st.session_state.form_data, key_prefix=f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_")

                            for table in form_config.get('tables', []):
                                render_table(table, st.session_state.form_data, key_prefix=f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_")

                            for field in form_config.get('fields_after_tables', []):
                                render_field(field, st.session_state.form_data, key_prefix=f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_")

                            if st.form_submit_button(f"Submit {current_subsubcategory}"):
                                if submit_subcategory_data(current_subsubcategory, st.session_state.form_data, form_config, supabase):
                                    st.success(f"Data submitted successfully to {subcategory_config['name']}!")
                                    for key in list(st.session_state.form_data.keys()):
                                        if key.startswith(current_subsubcategory.replace(' ', '_').replace('–', '_')):
                                            st.session_state.form_data.pop(key)
                                    st.rerun()

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Save and Continue"):
                                    for field in form_config.get('fields', []) + form_config.get('fields_after_tables', []):
                                        if field['type'] == 'number' and 'unit_options' in field and field['name'] in st.session_state.form_data:
                                            unit_key = f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{field['name']}_unit"
                                            current_value = st.session_state.form_data.get(f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{field['name']}")
                                            current_unit = st.session_state.form_data.get(unit_key, field.get('unit_options', [field.get('required_unit', '')])[0])
                                            required_unit = field.get('required_unit', field.get('unit_options', [''])[0])
                                            if current_unit != required_unit:
                                                converted_value = convert_units(current_value, current_unit, required_unit)
                                                st.session_state.form_data[f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{field['name']}"] = converted_value
                                                st.session_state.form_data[unit_key] = required_unit
                                                st.success(f"Converted {field['label']} from {current_unit} to {required_unit}")
                                    for table in form_config.get('tables', []):
                                        for row in st.session_state.form_data.get(f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{table['name']}_data", []):
                                            for col in table['columns']:
                                                if col.get('type', 'text') == 'number' and 'unit_options' in col:
                                                    value_key = col.get('name')
                                                    unit_key = f"{value_key}_unit"
                                                    current_value = row.get(value_key)
                                                    current_unit = row.get(unit_key, col.get('unit_options', [col.get('required_unit', '')])[0])
                                                    required_unit = col.get('required_unit', col.get('unit_options', [''])[0])
                                                    if current_unit != required_unit and current_value is not None:
                                                        converted_value = convert_units(current_value, current_unit, required_unit)
                                                        row[value_key] = converted_value
                                                        row[unit_key] = required_unit
                                                        st.success(f"Converted {col.get('label', value_key)} from {current_unit} to {required_unit} in {table['name']} table")
                                    st.success(f"{current_subsubcategory} data saved to session state with unit conversions applied.")
                                    if st.session_state.current_subcategory_index < len(st.session_state.selected_subcategories) - 1:
                                        st.session_state.current_subcategory_index += 1
                                        st.rerun()
                                    else:
                                        st.session_state.all_forms_completed = True
                                        st.session_state.current_step = "submit"
                                        st.rerun()
                            with col2:
                                if st.session_state.current_subcategory_index == len(st.session_state.selected_subcategories) - 1:
                                    if st.form_submit_button("Submit All"):
                                        st.session_state.all_forms_completed = True
                                        st.session_state.current_step = "submit"
                                        st.rerun()

                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                        with col1:
                            if st.session_state.current_subcategory_index > 0 and st.button("← Previous"):
                                st.session_state.current_subcategory_index -= 1
                                st.rerun()
                            elif st.button("← Back to General Info"):
                                st.session_state.current_step = "general_info"
                                st.rerun()
                        with col2:
                            pass
                        with col3:
                            if st.session_state.current_subcategory_index < len(st.session_state.selected_subcategories) - 1:
                                if st.button("Next"):
                                    st.session_state.current_subcategory_index += 1
                                    st.rerun()
                        with col4:
                            for table in form_config.get('tables', []):
                                if st.button(f"Add Row to {table['name']}", key=f"add_row_{table['name']}_{current_subsubcategory.replace(' ', '_').replace('–', '_')}"):
                                    form_data = st.session_state.form_data
                                    table_name = table['name']
                                    if f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{table_name}_data" not in form_data:
                                        form_data[f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{table_name}_data"] = [{}]
                                    form_data[f"{current_subsubcategory.replace(' ', '_').replace('–', '_')}_{table_name}_data"].append({col.get('name', ''): '' for col in table['columns']})
                                    st.rerun()
                    else:
                        st.error(f"Failed to load form configuration for {current_subsubcategory}")
                else:
                    st.error(f"No matching subcategory configuration found for {current_subsubcategory} in index_w.yaml")
                    logger.error(f"No matching subcategory configuration: {current_subsubcategory}. Available: {[item['name'] for item in index_config['forms']]}")
            else:
                st.error("Failed to load index_w.yaml")

    elif st.session_state.current_step == "submit" or st.session_state.all_forms_completed:
        st.subheader("Submit Data")
        with st.form("final_submit_form"):
            st.write("Please review your data and submit all entries.")
            if st.form_submit_button("Submit All"):
                success = True
                for subcat in st.session_state.selected_subcategories:
                    subsubcat = subcategory_map.get(subcat)
                    if isinstance(subsubcat, list):
                        subsubcat = st.session_state.form_data.get("subsubcategory_select", subsubcat[0])
                    forms_dir = os.path.join(os.path.dirname(__file__), "forms")
                    index_yaml_path = os.path.join(forms_dir, "index_w.yaml")  # Updated to index_w.yaml
                    index_config = load_yaml_file(index_yaml_path)
                    if index_config:
                        subcategory_config = next((item for item in index_config['forms'] if item['name'] == subsubcat), None)
                        if subcategory_config:
                            yaml_path = os.path.join(forms_dir, subcategory_config['path'])
                            form_config = load_yaml_file(yaml_path)
                            if form_config:
                                if not submit_subcategory_data(subsubcat, st.session_state.form_data, form_config, supabase):
                                    success = False
                if success:
                    st.success("All data submitted to validation tables successfully!")
                    st.session_state.form_data = {}
                    st.session_state.current_step = "general_info"
                    st.session_state.selected_subcategories = []
                    st.session_state.current_subcategory_index = 0
                    st.session_state.all_forms_completed = False
                    st.rerun()
                else:
                    st.error("Some data submissions failed. Please check the errors above.")
        # Move Back to Subcategories button outside the form
        if st.button("← Back to Subcategories"):
            st.session_state.current_step = "subcategory_forms"
            st.session_state.all_forms_completed = False
            st.session_state.current_subcategory_index = len(st.session_state.selected_subcategories) - 1
            st.rerun()

if __name__ == "__main__":
    waste_data_form()