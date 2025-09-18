import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime
import openpyxl
from postgrest.exceptions import APIError
import logging
import uuid
from data_collation_view import data_collation_view

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TABLE_MAPPING = {
    "2A3 - Glass Production": {"validation": "ipp_2a3_validation", "validated": "2A3 - Glass Production"},
    "2D - Non-Energy Products from Fuels and Solvent Use": {"validation": "ipp_2d_validation", "validated": "2D - Non-Energy Products from Fuels and Solvent Use"},
    "2F – Product Uses as Substitutes for Ozone-Depleting Substances": {"validation": "ipp_2f_validation", "validated": "2F – Product Uses as Substitutes for Ozone-Depleting Substances"},
    "2G1 – Electrical Equipment": {"validation": "ipp_2g1_validation", "validated": "2G1 – Electrical Equipment"},
    "2G2 – SF₆ and PFCs from Other Product Uses": {"validation": "ipp_2g2_validation", "validated": "2G2 – SF₆ and PFCs from Other Product Uses"},
    "2G3 – N₂O from Product Uses": {"validation": "ipp_2g3_validation", "validated": "2G3 – N₂O from Product Uses"},
    "2H1 - Pulp and Paper Industry": {"validation": "ipp_2h1_validation", "validated": "2H1 - Pulp and Paper Industry"},
    "2H2 - Food and Beverages Industry": {"validation": "ipp_2h2_validation", "validated": "2H2 - Food and Beverages Industry"}
}

KEY_FIELDS = {
    "2A3 - Glass Production": ["mass_glass_produced_tonnes", "recycled_glass_fraction", "virgin_material_mass_tonnes", "carbonates_consumed_mass_tonnes", "co2_capture_volume_tonnes", "emissions_factor_tco2"],
    "2D - Non-Energy Products from Fuels and Solvent Use": ["total_mass_motor_oils_tonnes", "total_mass_industrial_oils_tonnes", "total_mass_greases_tonnes", "mass_paraffin_wax_tonnes"],
    "2F – Product Uses as Substitutes for Ozone-Depleting Substances": ["mass_hfcs_supplied_tonnes", "mass_gas_fire_protection_tonnes", "mass_hfcs_aerosols_tonnes", "mass_solvents_hfcs_pfcs_tonnes"],
    "2G1 – Electrical Equipment": ["fluorinated_gases_manufacturing_kg", "fluorinated_gases_installation_kg", "fluorinated_gases_nameplate_capacity_kg"],
    "2G2 – SF₆ and PFCs from Other Product Uses": ["sf6_pfc_sales_other_uses", "awacs_aircraft_count", "research_particle_accelerators_count", "industrial_particle_accelerators_high_voltage_count", "industrial_particle_accelerators_low_voltage_count", "medical_radiotherapy_units_count", "soundproof_windows_sales_volume"],
    "2G3 – N₂O from Product Uses": ["mass_n2o_supplied_kg"],
    "2H1 - Pulp and Paper Industry": ["dry_pulp_produced_tonnes"],
    "2H2 - Food and Beverages Industry": ["food_beverage_produced_tonnes"]
}

def get_supabase_client():
    url = "https://ahrtfdgutdoghoydyluo.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFocnRmZGd1dGRvZ2hveWR5bHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzNzM4NTQsImV4cCI6MjA2OTk0OTg1NH0.He6WmGiMaP4HJsJr1eMZ5y4of_P_IZq-AtKU1L6B4g4"
    if not url or not key:
        st.error("Supabase credentials are invalid.")
        return None
    return create_client(url, key)

def map_activity_data(subcat_df, subcategory):
    activity_data = []
    subcategory_code = subcategory.split(" - ")[0]
    if subcategory_code == "2A3":
        if "mass_glass_produced_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Glass Production",
                "Category": "2A3",
                "Units": "tonnes",
                "Notes": "Total mass of glass produced (IPCC 2006, Tier 1, Volume 3, Chapter 2.3)"
            })
        if "recycled_glass_fraction" in subcat_df.columns:
            activity_data.append({
                "Activity": "Recycled Glass Fraction",
                "Category": "2A3",
                "Units": "fraction",
                "Notes": "Fraction of recycled glass used in production"
            })
        if "co2_capture_volume_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "CO₂ Capture Volume",
                "Category": "2A3",
                "Units": "tonnes",
                "Notes": "CO₂ captured from glass production processes"
            })
        if "virgin_material_mass_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Virgin Material Mass",
                "Category": "2A3",
                "Units": "tonnes",
                "Notes": "Mass of virgin material used in glass production"
            })
        if "carbonates_consumed_mass_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Carbonates Consumed",
                "Category": "2A3",
                "Units": "tonnes",
                "Notes": "Mass of carbonates consumed, key for CO₂ emissions (IPCC 2006)"
            })
        if "emissions_factor_tco2" in subcat_df.columns:
            activity_data.append({
                "Activity": "Emissions Factor",
                "Category": "2A3",
                "Units": "tCO₂/tonne",
                "Notes": "Emissions factor for glass production"
            })
    elif subcategory_code == "2D":
        if "total_mass_motor_oils_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Total Mass Motor Oils",
                "Category": "2D",
                "Units": "tonnes",
                "Notes": "Mass of motor oils used (IPCC 2006, Tier 1, Volume 3, Chapter 5.4)"
            })
        if "total_mass_industrial_oils_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Total Mass Industrial Oils",
                "Category": "2D",
                "Units": "tonnes",
                "Notes": "Mass of industrial oils used"
            })
        if "total_mass_greases_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Total Mass Greases",
                "Category": "2D",
                "Units": "tonnes",
                "Notes": "Mass of greases used"
            })
        if "mass_paraffin_wax_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass Paraffin Wax",
                "Category": "2D",
                "Units": "tonnes",
                "Notes": "Mass of paraffin wax used (IPCC 2006, Tier 1)"
            })
    elif subcategory_code == "2F":
        if "mass_hfcs_supplied_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass HFCs Supplied (Foam Blowing)",
                "Category": "2F",
                "Units": "tonnes",
                "Notes": "HFCs supplied for foam blowing agents (IPCC 2006, Tier 1, Volume 3, Chapter 7.2)"
            })
        if "mass_gas_fire_protection_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass Gas Fire Protection",
                "Category": "2F",
                "Units": "tonnes",
                "Notes": "HFCs/PFCs used in fire protection equipment"
            })
        if "mass_hfcs_aerosols_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass HFCs Aerosols",
                "Category": "2F",
                "Units": "tonnes",
                "Notes": "HFCs used in aerosols"
            })
        if "mass_solvents_hfcs_pfcs_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass Solvents HFCs/PFCs",
                "Category": "2F",
                "Units": "tonnes",
                "Notes": "HFCs/PFCs used in solvents (IPCC 2006, Tier 1)"
            })
    elif subcategory_code == "2G1":
        if "fluorinated_gases_manufacturing_kg" in subcat_df.columns:
            activity_data.append({
                "Activity": "Fluorinated Gases Manufacturing",
                "Category": "2G1",
                "Units": "kg",
                "Notes": "SF6/PFC used in manufacturing electrical equipment (IPCC 2006, Tier 1, Volume 3, Chapter 7.3)"
            })
        if "fluorinated_gases_installation_kg" in subcat_df.columns:
            activity_data.append({
                "Activity": "Fluorinated Gases Installation",
                "Category": "2G1",
                "Units": "kg",
                "Notes": "SF6/PFC used during equipment installation"
            })
        if "fluorinated_gases_nameplate_capacity_kg" in subcat_df.columns:
            activity_data.append({
                "Activity": "Fluorinated Gases Nameplate Capacity",
                "Category": "2G1",
                "Units": "kg",
                "Notes": "Nameplate capacity of SF6/PFC in equipment"
            })
    elif subcategory_code == "2G2":
        if "sf6_pfc_sales_other_uses" in subcat_df.columns:
            activity_data.append({
                "Activity": "SF6/PFC Sales Other Uses",
                "Category": "2G2",
                "Units": "kg",
                "Notes": "SF6/PFC sales for non-electrical uses (IPCC 2006, Tier 1, Volume 3, Chapter 7.3)"
            })
        if "awacs_aircraft_count" in subcat_df.columns:
            activity_data.append({
                "Activity": "AWACS Aircraft Count",
                "Category": "2G2",
                "Units": "count",
                "Notes": "Number of AWACS aircraft using SF6/PFC"
            })
        if "research_particle_accelerators_count" in subcat_df.columns:
            activity_data.append({
                "Activity": "Research Particle Accelerators",
                "Category": "2G2",
                "Units": "count",
                "Notes": "Number of research particle accelerators using SF6/PFC"
            })
        if "industrial_particle_accelerators_high_voltage_count" in subcat_df.columns:
            activity_data.append({
                "Activity": "Industrial Particle Accelerators (High Voltage)",
                "Category": "2G2",
                "Units": "count",
                "Notes": "Number of high-voltage industrial accelerators"
            })
        if "industrial_particle_accelerators_low_voltage_count" in subcat_df.columns:
            activity_data.append({
                "Activity": "Industrial Particle Accelerators (Low Voltage)",
                "Category": "2G2",
                "Units": "count",
                "Notes": "Number of low-voltage industrial accelerators"
            })
        if "medical_radiotherapy_units_count" in subcat_df.columns:
            activity_data.append({
                "Activity": "Medical Radiotherapy Units",
                "Category": "2G2",
                "Units": "count",
                "Notes": "Number of radiotherapy units using SF6/PFC"
            })
        if "soundproof_windows_sales_volume" in subcat_df.columns:
            activity_data.append({
                "Activity": "Soundproof Windows Sales",
                "Category": "2G2",
                "Units": "volume",
                "Notes": "Sales volume of soundproof windows using SF6"
            })
    elif subcategory_code == "2G3":
        if "mass_n2o_supplied_kg" in subcat_df.columns:
            activity_data.append({
                "Activity": "Mass N₂O Supplied",
                "Category": "2G3",
                "Units": "kg",
                "Notes": "N₂O supplied for product uses (IPCC 2006, Tier 1, Volume 3, Chapter 7.4)"
            })
    elif subcategory_code == "2H1":
        if "dry_pulp_produced_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Dry Pulp Produced",
                "Category": "2H1",
                "Units": "tonnes",
                "Notes": "Dry pulp produced in pulp and paper industry (IPCC 2006, Tier 1, Volume 3, Chapter 7.5)"
            })
    elif subcategory_code == "2H2":
        if "food_beverage_produced_tonnes" in subcat_df.columns:
            activity_data.append({
                "Activity": "Food/Beverage Produced",
                "Category": "2H2",
                "Units": "tonnes",
                "Notes": "Food and beverage production (IPCC 2006, Tier 1, Volume 3, Chapter 7.5)"
            })
    if not activity_data:
        logger.warning(f"No activity data mapped for subcategory: {subcategory}")
    return pd.DataFrame(activity_data)

def transfer_to_validated_table(supabase, record, validation_table, validated_table, subcategory):
    """
    Transfer a record from a validation table to its corresponding validated table,
    excluding id, status, and submission_date fields after validating key fields.
    """
    # Fields to exclude when transferring to validated table
    exclude_fields = ["id", "status", "submission_date"]
    
    # Validate key fields for the subcategory
    key_fields = KEY_FIELDS.get(subcategory, [])
    for field in key_fields:
        if field not in record:
            logger.error(f"Missing required field {field} in record ID {record['id']} for {subcategory}")
            return False, f"Missing required field: {field}"
        if record[field] is None or (isinstance(record[field], (int, float)) and record[field] <= 0):
            logger.error(f"Invalid value for {field} in record ID {record['id']} for {subcategory}: {record[field]}")
            return False, f"Invalid value for {field}: must be positive and non-null"

    # Create a new record with only the fields needed for the validated table
    validated_record = {key: value for key, value in record.items() if key not in exclude_fields}
    
    try:
        # Insert into validated table
        supabase.table(validated_table).insert(validated_record).execute()
        logger.info(f"Successfully transferred record ID {record['id']} to {validated_table}")
        
        # Delete from validation table
        supabase.table(validation_table).delete().eq("id", record["id"]).execute()
        logger.info(f"Deleted record ID {record['id']} from {validation_table}")
        return True, None
    except APIError as e:
        logger.error(f"Error transferring record ID {record['id']} from {validation_table} to {validated_table}: {e.message}")
        return False, f"Database error: {e.message}"

def ippu_view_page():
    st.markdown(
        """
        <style>
        .sector-header {font-size: 28px; font-weight: 700; margin-bottom: 20px; color: #2c3e50;}
        .nav-buttons {margin-bottom: 20px;}
        .dashboard-container {border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background: #ffffff; margin-bottom: 15px;}
        .kpi-row {display: flex; justify-content: center; gap: 20px; margin-bottom: 20px;}
        .kpi-card {flex: 0 1 200px; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; background: #f9f9f9; text-align: center;}
        .chart-layout {display: flex; gap: 20px; margin-bottom: 20px;}
        .chart-card {flex: 1; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; background: #ffffff;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sector-header">IPPU Dashboard</div>', unsafe_allow_html=True)

    supabase = get_supabase_client()
    if not supabase:
        return

    validated_tables = [
        "2A3 - Glass Production",
        "2D - Non-Energy Products from Fuels and Solvent Use",
        "2F – Product Uses as Substitutes for Ozone-Depleting Substances",
        "2G1 – Electrical Equipment",
        "2G2 – SF₆ and PFCs from Other Product Uses",
        "2G3 – N₂O from Product Uses",
        "2H1 - Pulp and Paper Industry",
        "2H2 - Food and Beverages Industry"
    ]
    validated_df_list = []
    for table in validated_tables:
        try:
            response = supabase.table(table).select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                df["Subcategory"] = table
                validated_df_list.append(df)
                logger.info(f"Successfully fetched data from table: {table}, {len(df)} rows")
            else:
                logger.warning(f"No data found in table: {table}")
                st.warning(f"No data found in table: {table}")
        except APIError as e:
            logger.error(f"Error fetching table {table}: {e.message}")
            st.error(f"Error fetching table {table}: {e.message}")
    validated_df = pd.concat(validated_df_list, ignore_index=True) if validated_df_list else pd.DataFrame()

    if validated_df.empty:
        st.error("No data fetched from any validated tables. Please check table names and data availability.")
        return

    tabs = st.tabs(["📊 Overview", "📂 Subcategory View", "⏳ Pending Reviews"])

    with tabs[0]:
        col_top = st.columns([3, 1])
        with col_top[0]:
            st.subheader("📊 Sector Overview Dashboard")

        if "data_year" in validated_df.columns:
            validated_df["data_year"] = pd.to_numeric(validated_df["data_year"], errors="coerce")
            min_year = int(validated_df["data_year"].min()) if not validated_df["data_year"].isna().all() else datetime.now().year - 10
            max_year = int(validated_df["data_year"].max()) if not validated_df["data_year"].isna().all() else datetime.now().year
            year_range = st.slider(
                "Select Year Range",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year)
            )
            validated_df = validated_df[
                (validated_df["data_year"] >= year_range[0]) &
                (validated_df["data_year"] <= year_range[1])
            ]
        else:
            min_year, max_year = datetime.now().year - 10, datetime.now().year
            year_range = (min_year, max_year)
            st.warning("No 'data_year' column found. Using default range.")

        sectors = ["IPPU", "Energy", "Waste", "AFOLU"]
        current_sector_idx = sectors.index("IPPU")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Previous Sector"):
                current_sector_idx = (current_sector_idx - 1) % len(sectors)
                st.session_state.selected_sector = sectors[current_sector_idx]
                st.session_state.page = f"{sectors[current_sector_idx].lower()}_view"
                st.rerun()
        with col2:
            st.write(f"Current Sector: {sectors[current_sector_idx]}")
        with col3:
            if st.button("Next Sector →"):
                current_sector_idx = (current_sector_idx + 1) % len(sectors)
                st.session_state.selected_sector = sectors[current_sector_idx]
                st.session_state.page = f"{sectors[current_sector_idx].lower()}_view"
                st.rerun()

        if st.button("← Back to Landing"):
            st.session_state.page = "landing"
            st.session_state.selected_sector = None
            st.rerun()

        c1, c2 = st.columns(2)
        c1.metric("Total Records", len(validated_df))

        g1, g2 = st.columns(2)
        with g1:
            chart_subcat = (
                alt.Chart(validated_df)
                .mark_bar()
                .encode(
                    x=alt.X("Subcategory", sort="-y"),
                    y="count()",
                    color="Subcategory"
                )
                .properties(title="Records by Subcategory", height=350, width=400)
            )
            st.altair_chart(chart_subcat, use_container_width=True)

        with g2:
            chart_year = (
                alt.Chart(validated_df)
                .mark_bar()
                .encode(
                    x=alt.X("data_year:O", sort=None, title="Year"),
                    y="count()",
                    color="data_year"
                )
                .properties(title="Records by Year", height=350, width=400)
            )
            st.altair_chart(chart_year, use_container_width=True)

        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        st.subheader("📋 IPPU Data Collation View")
        collated_df = data_collation_view(supabase, year_range)
        if not collated_df.empty:
            st.dataframe(collated_df, use_container_width=True)
        else:
            st.warning("No data available for Data Collation View. Check Supabase data or year range.")
            logger.warning("Data Collation View dataframe is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("📂 Subcategory Data View")
        subcategories = validated_df["Subcategory"].unique().tolist()
        if not subcategories:
            st.info("No subcategories available.")
        else:
            selected_subcat = st.selectbox("Select Subcategory", subcategories)
            try:
                response = supabase.table(selected_subcat).select("*").execute()
                if response.data:
                    subcat_df = pd.DataFrame(response.data)
                    logger.info(f"Successfully fetched raw data for {selected_subcat}, {len(subcat_df)} rows")
                else:
                    logger.warning(f"No data found in table: {selected_subcat}")
                    st.warning(f"No data found in table: {selected_subcat}")
                    subcat_df = pd.DataFrame()
            except APIError as e:
                logger.error(f"Error fetching table {selected_subcat}: {e.message}")
                st.error(f"Error fetching table {selected_subcat}: {e.message}")
                subcat_df = pd.DataFrame()

            if not subcat_df.empty and "data_year" in subcat_df.columns:
                subcat_df["data_year"] = pd.to_numeric(subcat_df["data_year"], errors="coerce")
                min_year = int(subcat_df["data_year"].min()) if not subcat_df["data_year"].isna().all() else datetime.now().year - 10
                max_year = int(subcat_df["data_year"].max()) if not subcat_df["data_year"].isna().all() else datetime.now().year
                year_range = st.slider(
                    "Select Year Range for Insights",
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year)
                )
                subcat_df = subcat_df[
                    (subcat_df["data_year"] >= year_range[0]) &
                    (subcat_df["data_year"] <= year_range[1])
                ]
            else:
                min_year, max_year = datetime.now().year - 10, datetime.now().year
                year_range = (min_year, max_year)
                if not subcat_df.empty:
                    st.warning(f"No 'data_year' column found for {selected_subcat}. Using default range.")

            numeric_fields = {
                "2A3 - Glass Production": [
                    "mass_glass_produced_tonnes", "recycled_glass_fraction", "virgin_material_mass_tonnes",
                    "carbonates_consumed_mass_tonnes", "co2_capture_volume_tonnes", "emissions_factor_tco2"
                ],
                "2D - Non-Energy Products from Fuels and Solvent Use": [
                    "total_mass_motor_oils_tonnes", "total_mass_industrial_oils_tonnes",
                    "total_mass_greases_tonnes", "mass_paraffin_wax_tonnes"
                ],
                "2F – Product Uses as Substitutes for Ozone-Depleting Substances": [
                    "mass_hfcs_supplied_tonnes", "mass_gas_fire_protection_tonnes",
                    "mass_hfcs_aerosols_tonnes", "mass_solvents_hfcs_pfcs_tonnes"
                ],
                "2G1 – Electrical Equipment": [
                    "fluorinated_gases_manufacturing_kg", "fluorinated_gases_installation_kg",
                    "fluorinated_gases_nameplate_capacity_kg"
                ],
                "2G2 – SF₆ and PFCs from Other Product Uses": [
                    "awacs_aircraft_count", "research_particle_accelerators_count",
                    "industrial_particle_accelerators_high_voltage_count", "industrial_particle_accelerators_low_voltage_count",
                    "medical_radiotherapy_units_count", "soundproof_windows_sales_volume", "sf6_pfc_sales_other_uses"
                ],
                "2G3 – N₂O from Product Uses": ["mass_n2o_supplied_kg"],
                "2H1 - Pulp and Paper Industry": ["dry_pulp_produced_tonnes"],
                "2H2 - Food and Beverages Industry": ["food_beverage_produced_tonnes"]
            }
            for field in numeric_fields.get(selected_subcat, []):
                if field in subcat_df.columns:
                    subcat_df[field] = pd.to_numeric(subcat_df[field], errors="coerce")
                else:
                    logger.warning(f"Expected column {field} not found in {selected_subcat} data")

            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            st.markdown(f"### {selected_subcat} Dashboard ({year_range[0]}–{year_range[1]})")

            if selected_subcat == "2A3 - Glass Production":
                if not all(col in subcat_df.columns for col in ["mass_glass_produced_tonnes", "recycled_glass_fraction", "co2_capture_volume_tonnes", "virgin_material_mass_tonnes"]):
                    st.warning("Required columns for 2A3 dashboard are missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    total_production = subcat_df["mass_glass_produced_tonnes"].sum()
                    recycled_fraction = subcat_df["recycled_glass_fraction"].mean() * 100
                    co2_captured = subcat_df["co2_capture_volume_tonnes"].sum()
                    virgin_mass = subcat_df["virgin_material_mass_tonnes"].sum()
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Total Glass Produced", f"{total_production:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Recycled Glass Fraction", f"{recycled_fraction:.2f}%")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("CO₂ Captured", f"{co2_captured:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col4:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Virgin Material Mass", f"{virgin_mass:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)

                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["mass_glass_produced_tonnes", "co2_capture_volume_tonnes"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["mass_glass_produced_tonnes", "co2_capture_volume_tonnes"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Tonnes"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#6a0dad", "#800080"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Production vs CO₂ Captured", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with right_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["recycled_glass_fraction"].mean().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("recycled_glass_fraction:Q", title="Fraction"),
                                tooltip=["data_year:O", "recycled_glass_fraction:Q"]
                            )
                            .properties(title="Recycled Glass Fraction Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["virgin_material_mass_tonnes", "carbonates_consumed_mass_tonnes"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["virgin_material_mass_tonnes", "carbonates_consumed_mass_tonnes"],
                                as_=["key", "value"]
                            )
                            .mark_bar()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Tonnes"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#1f77b4", "#ff7f0e"]), legend=alt.Legend(title="Metric")),
                                xOffset="key:N",
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Virgin vs Carbonates Mass", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with right_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        subcat_df["estimated_emissions"] = subcat_df["mass_glass_produced_tonnes"] * subcat_df["emissions_factor_tco2"]
                        trend_df = subcat_df.groupby("data_year")["estimated_emissions"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#d62728")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("estimated_emissions:Q", title="tCO₂"),
                                tooltip=["data_year:O", "estimated_emissions:Q"]
                            )
                            .properties(title="Estimated Emissions Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, _ = st.columns([1, 1])
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        subcat_df["estimated_emissions"] = subcat_df["mass_glass_produced_tonnes"] * subcat_df["emissions_factor_tco2"]
                        trend_df = subcat_df.groupby("data_year")[["estimated_emissions", "co2_capture_volume_tonnes"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["estimated_emissions", "co2_capture_volume_tonnes"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Tonnes"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#d62728", "#800080"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Estimated Emissions vs CO₂ Captured", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2D - Non-Energy Products from Fuels and Solvent Use":
                if not all(col in subcat_df.columns for col in ["total_mass_motor_oils_tonnes", "total_mass_industrial_oils_tonnes", "total_mass_greases_tonnes", "mass_paraffin_wax_tonnes"]):
                    st.warning("Required columns for 2D dashboard are missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    motor_oils = subcat_df["total_mass_motor_oils_tonnes"].sum()
                    industrial_oils = subcat_df["total_mass_industrial_oils_tonnes"].sum()
                    greases = subcat_df["total_mass_greases_tonnes"].sum()
                    paraffin_wax = subcat_df["mass_paraffin_wax_tonnes"].sum()
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Motor Oils", f"{motor_oils:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Industrial Oils", f"{industrial_oils:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Greases", f"{greases:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col4:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Paraffin Wax", f"{paraffin_wax:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["total_mass_motor_oils_tonnes", "total_mass_industrial_oils_tonnes", "total_mass_greases_tonnes"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["total_mass_motor_oils_tonnes", "total_mass_industrial_oils_tonnes", "total_mass_greases_tonnes"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Tonnes"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#1f77b4", "#ff7f0e", "#2ca02c"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Motor, Industrial, and Grease Mass Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with right_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["mass_paraffin_wax_tonnes"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("mass_paraffin_wax_tonnes:Q", title="Tonnes"),
                                tooltip=["data_year:O", "mass_paraffin_wax_tonnes:Q"]
                            )
                            .properties(title="Paraffin Wax Supply Trend", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2F – Product Uses as Substitutes for Ozone-Depleting Substances":
                if not all(col in subcat_df.columns for col in ["mass_hfcs_supplied_tonnes", "mass_gas_fire_protection_tonnes", "mass_hfcs_aerosols_tonnes", "mass_solvents_hfcs_pfcs_tonnes"]):
                    st.warning("Required columns for 2F dashboard are missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    hfcs_supplied = subcat_df["mass_hfcs_supplied_tonnes"].sum()
                    fire_protection = subcat_df["mass_gas_fire_protection_tonnes"].sum()
                    aerosols = subcat_df["mass_hfcs_aerosols_tonnes"].sum()
                    solvents = subcat_df["mass_solvents_hfcs_pfcs_tonnes"].sum()
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("HFCs Supplied", f"{hfcs_supplied:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Fire Protection", f"{fire_protection:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("HFCs Aerosols", f"{aerosols:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col4:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Solvents HFCs/PFCs", f"{solvents:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["mass_hfcs_supplied_tonnes", "mass_gas_fire_protection_tonnes", "mass_hfcs_aerosols_tonnes", "mass_solvents_hfcs_pfcs_tonnes"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["mass_hfcs_supplied_tonnes", "mass_gas_fire_protection_tonnes", "mass_hfcs_aerosols_tonnes", "mass_solvents_hfcs_pfcs_tonnes"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Tonnes"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="HFCs by Use Category", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with right_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        subcat_df["total_ods_mass"] = (
                            subcat_df["mass_hfcs_supplied_tonnes"] +
                            subcat_df["mass_gas_fire_protection_tonnes"] +
                            subcat_df["mass_hfcs_aerosols_tonnes"] +
                            subcat_df["mass_solvents_hfcs_pfcs_tonnes"]
                        )
                        trend_df = subcat_df.groupby("data_year")["total_ods_mass"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("total_ods_mass:Q", title="Tonnes"),
                                tooltip=["data_year:O", "total_ods_mass:Q"]
                            )
                            .properties(title="Total ODS Substitute Mass", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2G1 – Electrical Equipment":
                if not all(col in subcat_df.columns for col in ["fluorinated_gases_manufacturing_kg", "fluorinated_gases_installation_kg", "fluorinated_gases_nameplate_capacity_kg"]):
                    st.warning("Required columns for 2G1 dashboard are missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    manufacturing = subcat_df["fluorinated_gases_manufacturing_kg"].sum()
                    installation = subcat_df["fluorinated_gases_installation_kg"].sum()
                    nameplate = subcat_df["fluorinated_gases_nameplate_capacity_kg"].sum()
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Manufacturing", f"{manufacturing:.2f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Installation", f"{installation:.2f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Nameplate Capacity", f"{nameplate:.2f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["fluorinated_gases_manufacturing_kg", "fluorinated_gases_installation_kg", "fluorinated_gases_nameplate_capacity_kg"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["fluorinated_gases_manufacturing_kg", "fluorinated_gases_installation_kg", "fluorinated_gases_nameplate_capacity_kg"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="kg"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#1f77b4", "#ff7f0e", "#2ca02c"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Manufacturing vs Installation vs Nameplate Capacity", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2G2 – SF₆ and PFCs from Other Product Uses":
                if not all(col in subcat_df.columns for col in ["sf6_pfc_sales_other_uses", "awacs_aircraft_count", "research_particle_accelerators_count", "industrial_particle_accelerators_high_voltage_count", "industrial_particle_accelerators_low_voltage_count", "medical_radiotherapy_units_count", "soundproof_windows_sales_volume"]):
                    st.warning("Required columns for 2G2 dashboard are missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns(4)
                    sf6_pfc_sales = subcat_df["sf6_pfc_sales_other_uses"].sum()
                    awacs_count = subcat_df["awacs_aircraft_count"].sum()
                    accelerators_count = subcat_df["research_particle_accelerators_count"].sum()
                    windows_volume = subcat_df["soundproof_windows_sales_volume"].sum()
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("SF6/PFC Sales", f"{sf6_pfc_sales:.2f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("AWACS Aircraft", f"{int(awacs_count)} units")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Research Accelerators", f"{int(accelerators_count)} units")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col4:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        st.metric("Soundproof Windows", f"{windows_volume:.2f} volume")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, right_col = st.columns(2)
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["sf6_pfc_sales_other_uses"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("sf6_pfc_sales_other_uses:Q", title="kg"),
                                tooltip=["data_year:O", "sf6_pfc_sales_other_uses:Q"]
                            )
                            .properties(title="SF6/PFC Sales Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with right_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")[["awacs_aircraft_count", "research_particle_accelerators_count", "industrial_particle_accelerators_high_voltage_count"]].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .transform_fold(
                                ["awacs_aircraft_count", "research_particle_accelerators_count", "industrial_particle_accelerators_high_voltage_count"],
                                as_=["key", "value"]
                            )
                            .mark_line()
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("value:Q", title="Count"),
                                color=alt.Color("key:N", scale=alt.Scale(range=["#1f77b4", "#ff7f0e", "#2ca02c"]), legend=alt.Legend(title="Metric")),
                                tooltip=["data_year:O", "key:N", "value:Q"]
                            )
                            .properties(title="Equipment Counts Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2G3 – N₂O from Product Uses":
                if "mass_n2o_supplied_kg" not in subcat_df.columns:
                    st.warning("Required column 'mass_n2o_supplied_kg' for 2G3 dashboard is missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, _, _, _ = st.columns(4)
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        n2o_supplied = subcat_df["mass_n2o_supplied_kg"].sum()
                        st.metric("N₂O Supplied", f"{n2o_supplied:.2f} kg")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, _ = st.columns([1, 1])
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["mass_n2o_supplied_kg"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("mass_n2o_supplied_kg:Q", title="kg"),
                                tooltip=["data_year:O", "mass_n2o_supplied_kg:Q"]
                            )
                            .properties(title="N₂O Supplied Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2H1 - Pulp and Paper Industry":
                if "dry_pulp_produced_tonnes" not in subcat_df.columns:
                    st.warning("Required column 'dry_pulp_produced_tonnes' for 2H1 dashboard is missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, _, _, _ = st.columns(4)
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        pulp_produced = subcat_df["dry_pulp_produced_tonnes"].sum()
                        st.metric("Dry Pulp Produced", f"{pulp_produced:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, _ = st.columns([1, 1])
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["dry_pulp_produced_tonnes"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("dry_pulp_produced_tonnes:Q", title="Tonnes"),
                                tooltip=["data_year:O", "dry_pulp_produced_tonnes:Q"]
                            )
                            .properties(title="Dry Pulp Production Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            elif selected_subcat == "2H2 - Food and Beverages Industry":
                if "food_beverage_produced_tonnes" not in subcat_df.columns:
                    st.warning("Required column 'food_beverage_produced_tonnes' for 2H2 dashboard is missing. Please check the database.")
                else:
                    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
                    col1, _, _, _ = st.columns(4)
                    with col1:
                        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
                        food_produced = subcat_df["food_beverage_produced_tonnes"].sum()
                        st.metric("Food/Beverage Produced", f"{food_produced:.2f} tonnes")
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="chart-layout">', unsafe_allow_html=True)
                    left_col, _ = st.columns([1, 1])
                    with left_col:
                        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                        trend_df = subcat_df.groupby("data_year")["food_beverage_produced_tonnes"].sum().reset_index()
                        trend_chart = (
                            alt.Chart(trend_df)
                            .mark_line(color="#2c3e50")
                            .encode(
                                x=alt.X("data_year:O", title="Year"),
                                y=alt.Y("food_beverage_produced_tonnes:Q", title="Tonnes"),
                                tooltip=["data_year:O", "food_beverage_produced_tonnes:Q"]
                            )
                            .properties(title="Food/Beverage Production Over Time", height=350, width=400)
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("### Raw Data")
            if subcat_df.empty:
                st.warning(f"No raw data available for {selected_subcat}. Please check the Supabase table.")
            else:
                st.dataframe(subcat_df, use_container_width=True)

    with tabs[2]:
        st.subheader("⏳ Pending Reviews")
        
        supabase = get_supabase_client()
        if not supabase:
            st.error("Cannot fetch pending reviews due to invalid Supabase credentials.")
            return

        # Fetch pending data from all validation tables
        pending_df_list = []
        for subcategory, tables in TABLE_MAPPING.items():
            try:
                response = supabase.table(tables["validation"]).select("*").eq("status", "Pending").execute()
                if response.data:
                    df = pd.DataFrame(response.data)
                    df["Subcategory"] = subcategory
                    pending_df_list.append(df)
                    logger.info(f"Fetched {len(df)} pending records from {tables['validation']}")
                else:
                    logger.info(f"No pending records found in {tables['validation']}")
            except APIError as e:
                logger.error(f"Error fetching pending records from {tables['validation']}: {e.message}")
                st.warning(f"Error fetching pending records from {subcategory}: {e.message}")

        pending_df = pd.concat(pending_df_list, ignore_index=True) if pending_df_list else pd.DataFrame()

        if pending_df.empty:
            st.info("No pending reviews found across all subcategories.")
            return

        # Sort by subcategory and submission_date
        pending_df = pending_df.sort_values(by=["Subcategory", "submission_date"])

        # Display pending data grouped by subcategory
        for subcategory in pending_df["Subcategory"].unique():
            st.markdown(f"### {subcategory}")
            subcat_pending_df = pending_df[pending_df["Subcategory"] == subcategory]
            
            # Display the data
            st.dataframe(subcat_pending_df, use_container_width=True)

            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Review Incorrect Data")
                with st.form(f"incorrect_form_{subcategory.replace(' ', '_')}"):
                    record_id = st.text_input("Enter Record ID")
                    submit_incorrect = st.form_submit_button("Show Contact Details")
                    
                    if submit_incorrect:
                        if not record_id:
                            st.error("Please enter a valid Record ID.")
                        else:
                            try:
                                record_id = int(record_id)
                                # Fetch the record to ensure it still exists
                                response = supabase.table(TABLE_MAPPING[subcategory]["validation"]).select("*").eq("id", record_id).execute()
                                if not response.data:
                                    st.error(f"No record found with ID {record_id} in {subcategory}.")
                                else:
                                    record = response.data[0]
                                    if record["status"] != "Pending":
                                        st.warning(f"Record ID {record_id} is no longer pending (status: {record['status']}).")
                                    else:
                                        st.success("Contact details for follow-up:")
                                        st.write(f"**Provider Contact Person**: {record['provider_contact_person']}")
                                        st.write(f"**Contact Email**: {record['contact_email']}")
                                        st.write(f"**Contact Phone**: {record['contact_phone']}")
                                        logger.info(f"Displayed contact details for record ID {record_id} in {subcategory}")
                            except ValueError:
                                st.error("Invalid Record ID. Please enter a numeric ID.")
                            except APIError as e:
                                st.error(f"Error retrieving contact details: {e.message}")
                                logger.error(f"Error retrieving contact details for ID {record_id}: {e.message}")

            with col2:
                st.markdown("#### Validate Data")
                with st.form(f"validate_form_{subcategory.replace(' ', '_')}"):
                    record_id = st.text_input("Enter Record ID to Validate")
                    confirm_validation = st.checkbox(f"Confirm validation of record ID {record_id if record_id else 'N/A'}")
                    submit_validate = st.form_submit_button("Validate Data")
                    
                    if submit_validate:
                        if not record_id:
                            st.error("Please enter a valid Record ID.")
                        elif not confirm_validation:
                            st.error("Please check the confirmation box to validate the record.")
                        else:
                            try:
                                record_id = int(record_id)
                                with st.spinner("Validating record..."):
                                    # Fetch the record to ensure it still exists and is pending
                                    response = supabase.table(TABLE_MAPPING[subcategory]["validation"]).select("*").eq("id", record_id).execute()
                                    if not response.data:
                                        st.error(f"No record found with ID {record_id} in {subcategory}. It may have been processed by another user.")
                                        logger.warning(f"Record ID {record_id} not found in {TABLE_MAPPING[subcategory]['validation']}")
                                    else:
                                        record = response.data[0]
                                        if record["status"] != "Pending":
                                            st.warning(f"Record ID {record_id} is no longer pending (status: {record['status']}).")
                                            logger.warning(f"Record ID {record_id} has status {record['status']} in {TABLE_MAPPING[subcategory]['validation']}")
                                        else:
                                            # Validate and transfer to validated table
                                            success, error_message = transfer_to_validated_table(
                                                supabase,
                                                record,
                                                TABLE_MAPPING[subcategory]["validation"],
                                                TABLE_MAPPING[subcategory]["validated"],
                                                subcategory
                                            )
                                            if success:
                                                # Update status to Validated
                                                supabase.table(TABLE_MAPPING[subcategory]["validation"]).update({"status": "Validated"}).eq("id", record_id).execute()
                                                logger.info(f"Updated status to Validated for record ID {record_id} in {TABLE_MAPPING[subcategory]['validation']}")
                                                st.success(f"Record ID {record_id} validated and transferred to {subcategory}.")
                                                logger.info(f"Successfully validated and transferred record ID {record_id} for {subcategory}")
                                                st.rerun()  # Refresh to update the displayed data
                                            else:
                                                st.error(f"Failed to validate record ID {record_id}: {error_message}")
                            except ValueError:
                                st.error("Invalid Record ID. Please enter a numeric ID.")
                            except APIError as e:
                                st.error(f"Error validating record ID {record_id}: {e.message}")
                                logger.error(f"Error validating record ID {record_id}: {e.message}")