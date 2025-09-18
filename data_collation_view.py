import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def data_collation_view(supabase, year_range):
    activity_mappings = {
        "2A3 - Glass Production": [
            {"Activity": "Glass Production", "Column": "mass_glass_produced_tonnes", "Units": "tonnes", "Notes": "Total mass of glass produced (IPCC 2006, Tier 1, Volume 3, Chapter 2.3)", "Aggregation": "sum"},
            {"Activity": "Recycled Glass Fraction", "Column": "recycled_glass_fraction", "Units": "fraction", "Notes": "Fraction of recycled glass used in production", "Aggregation": "mean"},
            {"Activity": "CO₂ Capture Volume", "Column": "co2_capture_volume_tonnes", "Units": "tonnes", "Notes": "CO₂ captured from glass production processes", "Aggregation": "sum"},
            {"Activity": "Virgin Material Mass", "Column": "virgin_material_mass_tonnes", "Units": "tonnes", "Notes": "Mass of virgin material used in glass production", "Aggregation": "sum"},
            {"Activity": "Carbonates Consumed", "Column": "carbonates_consumed_mass_tonnes", "Units": "tonnes", "Notes": "Mass of carbonates consumed, key for CO₂ emissions (IPCC 2006)", "Aggregation": "sum"},
            {"Activity": "Emissions Factor", "Column": "emissions_factor_tco2", "Units": "tCO₂/tonne", "Notes": "Emissions factor for glass production", "Aggregation": "mean"}
        ],
        "2D - Non-Energy Products from Fuels and Solvent Use": [
            {"Activity": "Motor Oils", "Column": "total_mass_motor_oils_tonnes", "Units": "tonnes", "Notes": "Mass of motor oils used (IPCC 2006, Tier 1, Volume 3, Chapter 5.4)", "Aggregation": "sum"},
            {"Activity": "Industrial Oils", "Column": "total_mass_industrial_oils_tonnes", "Units": "tonnes", "Notes": "Mass of industrial oils used", "Aggregation": "sum"},
            {"Activity": "Greases", "Column": "total_mass_greases_tonnes", "Units": "tonnes", "Notes": "Mass of greases used", "Aggregation": "sum"},
            {"Activity": "Paraffin Wax", "Column": "mass_paraffin_wax_tonnes", "Units": "tonnes", "Notes": "Mass of paraffin wax used (IPCC 2006, Tier 1)", "Aggregation": "sum"}
        ],
        "2F – Product Uses as Substitutes for Ozone-Depleting Substances": [
            {"Activity": "HFCs Supplied (Foam Blowing)", "Column": "mass_hfcs_supplied_tonnes", "Units": "tonnes", "Notes": "HFCs supplied for foam blowing agents (IPCC 2006, Tier 1, Volume 3, Chapter 7.2)", "Aggregation": "sum"},
            {"Activity": "Gas Fire Protection", "Column": "mass_gas_fire_protection_tonnes", "Units": "tonnes", "Notes": "HFCs/PFCs used in fire protection equipment", "Aggregation": "sum"},
            {"Activity": "HFCs Aerosols", "Column": "mass_hfcs_aerosols_tonnes", "Units": "tonnes", "Notes": "HFCs used in aerosols", "Aggregation": "sum"},
            {"Activity": "Solvents HFCs/PFCs", "Column": "mass_solvents_hfcs_pfcs_tonnes", "Units": "tonnes", "Notes": "HFCs/PFCs used in solvents (IPCC 2006, Tier 1)", "Aggregation": "sum"}
        ],
        "2G1 – Electrical Equipment": [
            {"Activity": "Fluorinated Gases Manufacturing", "Column": "fluorinated_gases_manufacturing_kg", "Units": "kg", "Notes": "SF6/PFC used in manufacturing electrical equipment (IPCC 2006, Tier 1, Volume 3, Chapter 7.3)", "Aggregation": "sum"},
            {"Activity": "Fluorinated Gases Installation", "Column": "fluorinated_gases_installation_kg", "Units": "kg", "Notes": "SF6/PFC used during equipment installation", "Aggregation": "sum"},
            {"Activity": "Fluorinated Gases Nameplate Capacity", "Column": "fluorinated_gases_nameplate_capacity_kg", "Units": "kg", "Notes": "Nameplate capacity of SF6/PFC in equipment", "Aggregation": "sum"}
        ],
        "2G2 – SF₆ and PFCs from Other Product Uses": [
            {"Activity": "SF6/PFC Sales Other Uses", "Column": "sf6_pfc_sales_other_uses", "Units": "kg", "Notes": "SF6/PFC sales for non-electrical uses (IPCC 2006, Tier 1, Volume 3, Chapter 7.3)", "Aggregation": "sum"},
            {"Activity": "AWACS Aircraft Count", "Column": "awacs_aircraft_count", "Units": "count", "Notes": "Number of AWACS aircraft using SF6/PFC", "Aggregation": "sum"},
            {"Activity": "Research Particle Accelerators", "Column": "research_particle_accelerators_count", "Units": "count", "Notes": "Number of research particle accelerators using SF6/PFC", "Aggregation": "sum"},
            {"Activity": "Industrial Particle Accelerators (High Voltage)", "Column": "industrial_particle_accelerators_high_voltage_count", "Units": "count", "Notes": "Number of high-voltage industrial accelerators", "Aggregation": "sum"},
            {"Activity": "Industrial Particle Accelerators (Low Voltage)", "Column": "industrial_particle_accelerators_low_voltage_count", "Units": "count", "Notes": "Number of low-voltage industrial accelerators", "Aggregation": "sum"},
            {"Activity": "Medical Radiotherapy Units", "Column": "medical_radiotherapy_units_count", "Units": "count", "Notes": "Number of radiotherapy units using SF6/PFC", "Aggregation": "sum"},
            {"Activity": "Soundproof Windows Sales", "Column": "soundproof_windows_sales_volume", "Units": "volume", "Notes": "Sales volume of soundproof windows using SF6", "Aggregation": "sum"}
        ],
        "2G3 – N₂O from Product Uses": [
            {"Activity": "N₂O Supplied", "Column": "mass_n2o_supplied_kg", "Units": "kg", "Notes": "N₂O supplied for product uses (IPCC 2006, Tier 1, Volume 3, Chapter 7.4)", "Aggregation": "sum"}
        ],
        "2H1 - Pulp and Paper Industry": [
            {"Activity": "Dry Pulp Produced", "Column": "dry_pulp_produced_tonnes", "Units": "tonnes", "Notes": "Dry pulp produced in pulp and paper industry (IPCC 2006, Tier 1, Volume 3, Chapter 7.5)", "Aggregation": "sum"}
        ],
        "2H2 - Food and Beverages Industry": [
            {"Activity": "Food/Beverage Produced", "Column": "food_beverage_produced_tonnes", "Units": "tonnes", "Notes": "Food and beverage production (IPCC 2006, Tier 1, Volume 3, Chapter 7.5)", "Aggregation": "sum"}
        ]
    }

    collated_data = []
    for subcategory, activities in activity_mappings.items():
        try:
            response = supabase.table(subcategory).select("*").execute()
            if not response.data:
                st.warning(f"No data found in table: {subcategory}")
                continue
            df = pd.DataFrame(response.data)

            if "data_year" in df.columns:
                df["data_year"] = pd.to_numeric(df["data_year"], errors="coerce")
                df = df[(df["data_year"] >= year_range[0]) & (df["data_year"] <= year_range[1])]
            else:
                st.warning(f"No 'data_year' column found in table: {subcategory}")
                continue

            for activity in activities:
                column = activity["Column"]
                if column not in df.columns:
                    st.warning(f"Column {column} not found in table: {subcategory}")
                    continue

                df[column] = pd.to_numeric(df[column], errors="coerce")

                if activity["Aggregation"] == "sum":
                    agg_df = df.groupby("data_year")[column].sum().reset_index()
                else:
                    agg_df = df.groupby("data_year")[column].mean().reset_index()

                row = {
                    "Activity": activity["Activity"],
                    "Category": subcategory.split(" - ")[0],
                    "Units": activity["Units"],
                    "Notes": activity["Notes"]
                }
                for year in range(year_range[0], year_range[1] + 1):
                    year_data = agg_df[agg_df["data_year"] == year][column]
                    row[str(year)] = year_data.iloc[0] if not year_data.empty else (0 if activity["Aggregation"] == "sum" else None)
                collated_data.append(row)

        except APIError as e:
            st.error(f"Error fetching table {subcategory}: {e.message}")
            continue

    if not collated_data:
        st.error("No data available for collation across any subcategories.")
        return pd.DataFrame()

    collated_df = pd.DataFrame(collated_data)
    year_columns = [str(year) for year in range(year_range[0], year_range[1] + 1)]
    collated_df = collated_df[["Activity", "Category", "Units", "Notes"] + year_columns]
    for col in year_columns:
        collated_df[col] = collated_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else x)
    return collated_df