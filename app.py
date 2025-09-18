import streamlit as st
import os
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime
from ippu_form import ippu_data_form
from waste_form import waste_data_form
import ghg_inventory
import knowledge_library
import btr_section

# Try to import supabase client; handle gracefully if missing
SUPABASE_AVAILABLE = True
try:
    from supabase import create_client
except Exception:
    SUPABASE_AVAILABLE = False

# --- Helpers ---
def get_supabase_client():
    """Return a Supabase client with hardcoded credentials for development."""
    if not SUPABASE_AVAILABLE:
        return None
    url = "https://ahrtfdgutdoghoydyluo.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFocnRmZGd1dGRvZ2hveWR5bHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzNzM4NTQsImV4cCI6MjA2OTk0OTg1NH0.He6WmGiMaP4HJsJr1eMZ5y4of_P_IZq-AtKU1L6B4g4"
    if not url or not key:
        st.error("Supabase credentials are invalid.")
        return None
    return create_client(url, key)

def init_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "drafts" not in st.session_state:
        st.session_state.drafts = []
    if "last_fetch" not in st.session_state:
        st.session_state.last_fetch = None
    if "selected_sector" not in st.session_state:
        st.session_state.selected_sector = None

# --- Page components ---

def landing_page():
    st.markdown(
        """
        <style>
        .hero-title{font-size:48px; font-weight:800; margin-bottom:6px; line-height:1}
        .hero-sub{color: #6b7280; margin-top:6px; margin-bottom:6px}
        .hero-meta{color:#9ca3af; margin-top:8px}
        .role-card{border:1px solid #e6e9ee; padding:18px; border-radius:10px; box-shadow:0 1px 3px rgba(16,24,40,0.03); background:#fff}
        .card-logo-wrap{display:flex; justify-content:center; margin-bottom:12px}
        .card-logo{border-radius:12px; border:1px solid #e6e9ee; padding:8px; background:#fff}
        .placeholder{border:2px dashed #d1d5db; padding:12px; text-align:center; color:#6b7280; border-radius:8px}
        .small-placeholder{border:1px dashed #e5e7eb; padding:8px; text-align:center; color:#6b7280; border-radius:6px; width:96px}
        .hero-row{display:flex; align-items:center; gap:18px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_col, title_col = st.columns([1, 5])
    with logo_col:
        local_logo_path = "met logo.jpg"
        if os.path.exists(local_logo_path):
            try:
                st.image(local_logo_path, use_container_width=True)
            except Exception:
                st.markdown("<div class='placeholder'>Logo placeholder</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='placeholder'>Logo placeholder<br/>(met logo.jpg not found in project folder)</div>", unsafe_allow_html=True)

    with title_col:
        st.markdown("<div class='hero-row'>", unsafe_allow_html=True)
        st.markdown("<div style='flex:1'>", unsafe_allow_html=True)
        st.markdown("<div class='hero-title'>GHG Inventory Data Hub</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='hero-sub'>Collect — Validate — Visualize.</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hero-meta'>A lightweight platform to collect greenhouse gas (GHG) inventory data, manage knowledge, and generate Biennial Transparency Reports (BTR).</div>",
            unsafe_allow_html=True,
        )

        st.write("")
        st.write("Use the buttons below to continue as a Data Provider, GHG Compiler, access the Stakeholder Database, or explore new sections for GHG Inventory, Knowledge Library, and BTR reporting.")

    st.write("")

    # Create a 3x2 grid for buttons
    row1 = st.columns(3)
    row2 = st.columns(3)

    def render_role_card(title, description, button_key, image_filename=None, container=None):
        with container:
            if image_filename and os.path.exists(image_filename):
                try:
                    st.image(image_filename, width=220)
                except Exception as e:
                    st.write(f"Debug: Failed to load {image_filename} - {str(e)}")
                    img_html = f"<div class='card-logo-wrap'><div class='card-logo'><img src='{image_filename}' style='display:block; width:220px; height:150px; object-fit:cover; border-radius:10px;'></div></div>"
                    st.markdown(img_html, unsafe_allow_html=True)
            else:
                st.write(f"Debug: Image file {image_filename} not found or not provided.")
                pass

            st.markdown("<div class='role-card'>", unsafe_allow_html=True)
            st.subheader(title)
            st.write(description)
            if st.button(f"Proceed — {title}", key=button_key):
                if title == "Data Provider":
                    st.session_state.page = "provider"
                elif title == "GHG Compiler":
                    st.session_state.page = "compiler"
                elif title == "Stakeholder Database":
                    st.session_state.page = "stakeholder"
                elif title == "GHG Inventory":
                    st.session_state.page = "ghg_inventory"
                elif title == "Knowledge Library":
                    st.session_state.page = "knowledge_library"
                elif title == "BTR Section":
                    st.session_state.page = "btr_section"
            st.markdown("</div>", unsafe_allow_html=True)

    # Assign buttons to 3x2 grid
    with row1[0]:
        render_role_card(
            "Data Provider",
            "Submit sector-specific GHG data (IPPU, Waste, Energy, AFOLU). Simple forms and file uploads for evidence.",
            button_key="btn_provider_hero",
            image_filename="data.png",
            container=row1[0],
        )

    with row1[1]:
        render_role_card(
            "GHG Compiler",
            "Review, validate and visualise submitted data. Dashboard tools to generate insights and identify gaps.",
            button_key="btn_compiler_hero",
            image_filename="ghg.png",
            container=row1[1],
        )

    with row1[2]:
        render_role_card(
            "Stakeholder Database",
            "Access the stakeholder directory — organisations, contacts and roles used to invite data providers and assign compilers.",
            button_key="btn_stake_db",
            image_filename="stakeholder.png",
            container=row1[2],
        )

    with row2[0]:
        render_role_card(
            "GHG Inventory",
            "Build and manage GHG inventories, track mitigation actions, and monitor NDC progress.",
            button_key="btn_ghg_inventory",
            image_filename="inventory.png",
            container=row2[0],
        )

    with row2[1]:
        render_role_card(
            "Knowledge Library",
            "Repository for official documents with search, extraction, and validation features.",
            button_key="btn_knowledge_library",
            image_filename="library.png",
            container=row2[1],
        )

    with row2[2]:
        render_role_card(
            "BTR Section",
            "Generate and preview Biennial Transparency Report (BTR) outputs with CTF tables.",
            button_key="btn_btr_section",
            image_filename="btr.png",
            container=row2[2],
        )

    st.divider()
    st.info("This is a starter app. Forms and validation workflows are placeholders for now.")
    st.write("Supabase status:", "available" if get_supabase_client() else "not configured or supabase package missing")
    st.write("")
    st.caption("App version 0.2 — Built for GHG inventory workflows and BTR reporting")

def data_provider_page():
    st.header("Data Provider — Select Sector")
    st.write("Choose the sector you want to submit data for.")

    sectors = [
        ("IPPU", "IPPU.png"),
        ("Energy", "Energy.png"),
        ("Waste", "Waste.png"),
        ("AFOLU", "AFOLU.png"),
    ]

    cols = st.columns(4)
    for i, (sector_name, image_file) in enumerate(sectors):
        with cols[i]:
            if os.path.exists(image_file):
                try:
                    st.image(image_file, width=200)
                except Exception as e:
                    st.write(f"Debug: Failed to load {image_file} - {str(e)}")
                    st.markdown(
                        "<div style='height:150px;border-radius:10px;border:1px solid #e6e9ee; display:flex;align-items:center;justify-content:center;'>"
                        f"{sector_name} logo</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='height:150px;border:2px dashed #d1d5db;border-radius:10px; display:flex;align-items:center;justify-content:center;color:#6b7280;'>"
                    f"Image {image_file} not found</div>",
                    unsafe_allow_html=True,
                )

            st.subheader(sector_name)
            key_name = f"provider_btn_{sector_name.lower()}"
            if st.button(f"Proceed — {sector_name}", key=key_name):
                st.session_state.selected_sector = sector_name
                if sector_name == "IPPU":
                    st.session_state.page = "ippu_form"
                elif sector_name == "Waste":
                    st.session_state.page = "waste_form"
                st.rerun()

    st.write("")
    if st.button("← Back to Landing"):
        st.session_state.page = "landing"
        st.session_state.selected_sector = None
        st.rerun()

def ghg_compiler_page():
    st.header("GHG Compiler — Select Sector")
    st.write("Choose the sector you want to review and validate submissions for.")

    sectors = [
        ("IPPU", "IPPU.png"),
        ("Energy", "Energy.png"),
        ("Waste", "Waste.png"),
        ("AFOLU", "AFOLU.png"),
    ]

    cols = st.columns(4)
    for i, (sector_name, image_file) in enumerate(sectors):
        with cols[i]:
            if os.path.exists(image_file):
                try:
                    st.image(image_file, width=200)
                except Exception as e:
                    st.write(f"Debug: Failed to load {image_file} - {str(e)}")
                    st.markdown(
                        "<div style='height:150px;border-radius:10px;border:1px solid #e6e9ee; display:flex;align-items:center;justify-content:center;'>"
                        f"{sector_name} logo</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='height:150px;border:2px dashed #d1d5db;border-radius:10px; display:flex;align-items:center;justify-content:center;color:#6b7280;'>"
                    f"Image {image_file} not found</div>",
                    unsafe_allow_html=True,
                )

            st.subheader(sector_name)
            key_name = f"compiler_btn_{sector_name.lower()}"
            if st.button(f"Review — {sector_name}", key=key_name):
                st.session_state.selected_sector = sector_name
                if sector_name == "IPPU":
                    try:
                        from ippu_view import ippu_view_page
                        st.session_state.page = "ippu_view"
                    except ImportError as e:
                        st.error(f"Failed to load ippu_view.py: {e}")
                        st.write("Please ensure ippu_view.py is in the same directory and contains the ippu_view_page function.")
                elif sector_name == "Energy":
                    try:
                        from energy_view import energy_view_page
                        st.session_state.page = "energy_view"
                    except ImportError as e:
                        st.error(f"Failed to load energy_view.py: {e}")
                        st.write("Please ensure energy_view.py is in the same directory and contains the energy_view_page function.")
                elif sector_name == "Waste":
                    try:
                        from waste_view import waste_view_page
                        st.session_state.page = "waste_view"
                    except ImportError as e:
                        st.error(f"Failed to load waste_view.py: {e}")
                        st.write("Please ensure waste_view.py is in the same directory and contains the waste_view_page function.")
                elif sector_name == "AFOLU":
                    try:
                        from afolu_view import afolu_view_page
                        st.session_state.page = "afolu_view"
                    except ImportError as e:
                        st.error(f"Failed to load afolu_view.py: {e}")
                        st.write("Please ensure afolu_view.py is in the same directory and contains the afolu_view_page function.")
                st.rerun()

    st.write("")
    if st.button("← Back to Landing", key="back_from_compiler"):
        st.session_state.page = "landing"
        st.session_state.selected_sector = None
        st.rerun()

def stakeholder_page():
    st.header("Stakeholder Database")
    st.write("Stakeholder directory UI will be implemented here.")
    if st.button("← Back to Landing"):
        st.session_state.page = "landing"
        st.session_state.selected_sector = None
        st.rerun()

# --- App entrypoint ---
def main():
    st.set_page_config(page_title="GHG Inventory Hub", layout="wide")
    init_session_state()

    if st.session_state.page == "landing":
        landing_page()
    elif st.session_state.page == "provider":
        data_provider_page()
    elif st.session_state.page == "compiler":
        ghg_compiler_page()
    elif st.session_state.page == "stakeholder":
        stakeholder_page()
    elif st.session_state.page == "ghg_inventory":
        ghg_inventory.main()
    elif st.session_state.page == "knowledge_library":
        knowledge_library.main()
    elif st.session_state.page == "btr_section":
        btr_section.main()
    elif st.session_state.page == "ippu_form":
        try:
            from ippu_form import ippu_data_form
            ippu_data_form()
        except ImportError as e:
            st.error(f"Failed to load ippu_form.py: {e}")
            st.write("Please ensure ippu_form.py is in the same directory and contains the ippu_data_form function.")
    elif st.session_state.page == "waste_form":
        try:
            from waste_form import waste_data_form
            waste_data_form()
        except ImportError as e:
            st.error(f"Failed to load waste_form.py: {e}")
            st.write("Please ensure waste_form.py is in the same directory and contains the waste_data_form function.")
    elif st.session_state.page == "ippu_view":
        try:
            from ippu_view import ippu_view_page
            ippu_view_page()
        except ImportError as e:
            st.error(f"Failed to load ippu_view.py: {e}")
            st.write("Please ensure ippu_view.py is in the same directory and contains the ippu_view_page function.")
    elif st.session_state.page == "energy_view":
        try:
            from energy_view import energy_view_page
            energy_view_page()
        except ImportError as e:
            st.error(f"Failed to load energy_view.py: {e}")
            st.write("Please ensure energy_view.py is in the same directory and contains the energy_view_page function.")
    elif st.session_state.page == "waste_view":
        try:
            from waste_view import waste_view_page
            waste_view_page()
        except ImportError as e:
            st.error(f"Failed to load waste_view.py: {e}")
            st.write("Please ensure waste_view.py is in the same directory and contains the waste_view_page function.")
    elif st.session_state.page == "afolu_view":
        try:
            from afolu_view import afolu_view_page
            afolu_view_page()
        except ImportError as e:
            st.error(f"Failed to load afolu_view.py: {e}")
            st.write("Please ensure afolu_view.py is in the same directory and contains the afolu_view_page function.")
    else:
        st.session_state.page = "landing"
        st.rerun()

if __name__ == "__main__":
    main()