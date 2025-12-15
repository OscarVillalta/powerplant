import sys, os
import io
from activity import display_sales_activity
from all_plants import display_all_plant
from calldir import call_directory
from login import logout_user, show_login
from outtage import display_outtages
import psycopg2
import streamlit as st
import pandas as pd
import warnings
from PIL import Image
from pandas import ExcelWriter
import xlsxwriter
from st_aggrid import AgGrid, GridOptionsBuilder

# ------------------------------------------------------
# Streamlit config (should be one of the first calls)
# ------------------------------------------------------
st.set_page_config(
    page_title="PowerPlant Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

warnings.filterwarnings("ignore", category=UserWarning, module="psycopg2")

# ------------------------------------------------------
# DB connection
# ------------------------------------------------------
conn = psycopg2.connect(os.environ["DATABASE_URL"])

# ------------------------------------------------------
# CACHED LOADERS for Plant Search tab
# ------------------------------------------------------
@st.cache_data(ttl=900)
def load_filter_data():
    plant_names = pd.read_sql(
        "SELECT DISTINCT plantname FROM general_plant_info "
        "WHERE plantname IS NOT NULL ORDER BY plantname;",
        conn
    )
    fuel_types = pd.read_sql(
        "SELECT DISTINCT fuel_type_1 FROM general_plant_info "
        "WHERE fuel_type_1 IS NOT NULL ORDER BY fuel_type_1;",
        conn
    )
    manufacturers = pd.read_sql(
        "SELECT DISTINCT drive_manufacturer FROM plant_drive_info "
        "WHERE drive_manufacturer IS NOT NULL ORDER BY drive_manufacturer;",
        conn
    )
    drive_types = pd.read_sql(
        "SELECT DISTINCT drive_info FROM plant_drive_info "
        "WHERE drive_info IS NOT NULL ORDER BY drive_info;",
        conn
    )

    plant_option = ["All"] + plant_names["plantname"].dropna().tolist()
    fuel_options = ["All"] + fuel_types["fuel_type_1"].dropna().tolist()
    manufacturer_options = ["All"] + manufacturers["drive_manufacturer"].dropna().tolist()
    drive_info_options = ["All"] + drive_types["drive_info"].dropna().tolist()

    return plant_option, fuel_options, manufacturer_options, drive_info_options


@st.cache_data(ttl=120)
def load_main_plant_summary():
    query = """
        SELECT DISTINCT 
            g.plant_id, 
            g.plantname, 
            g.ownername, 
            g.company_city, 
            g.company_state, 
            g.fuel_type_1,
            COUNT(DISTINCT c.cont_id) AS contact_count,
            COUNT(DISTINCT d.drive_id) AS drive_count
        FROM general_plant_info g
        INNER JOIN contact_plant_info c ON g.plant_id = c.plant_id
        INNER JOIN plant_drive_info d ON g.plant_id = d.plant_id
        GROUP BY g.plant_id, g.plantname, g.ownername, g.company_address,
                 g.company_city, g.company_state, g.fuel_type_1
        ORDER BY g.plantname ASC;
    """

    df = pd.read_sql_query(query, conn)

    df = df.rename(columns={
        "plantname": "Plant Name",
        "ownername": "Owner Name",
        "company_city": "City",
        "company_state": "State",
        "fuel_type_1": "Primary Fuel",
        "contact_count": "Contacts",
        "drive_count": "Drives"
    })

    return df


# ------------------------------------------------------
# LOGIN
# ------------------------------------------------------
if st.session_state.get("logged_out"):
    st.session_state.clear()

user = show_login(conn)

st.sidebar.markdown(f"👋 Logged in as **{user['full_name'] or user['username']}** ({user['role']})")
if st.sidebar.button("🚪 Logout"):
    logout_user()

# ------------------------------------------------------
# HEADER
# ------------------------------------------------------
col1, col2 = st.columns([1, 1.5])
with col1:
    st.markdown("# AFC Power Plant Portal")
with col2:
    st.image("powerplant1.svg", width=80)

st.write("Welcome to the internal plant intelligence and contact system.")

# ------------------------------------------------------
# FAKE TABS
# ------------------------------------------------------
st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] > div[role="radiogroup"] {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    div[role="radiogroup"] > label {
        border-radius: 999px;
        padding: 0.4rem 0.9rem;
        border: 1px solid #444;
        background: #1b1e27;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
        color: #e0e0e0;
    }
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    div[role="radiogroup"] > label[data-selected="true"] {
        background: linear-gradient(135deg, #6A5ACD, #4A90E2);
        border-color: #6A5ACD;
        color: #ffffff;
        box-shadow: 0 0 8px rgba(106, 90, 205, 0.6);
    }
    div[role="radiogroup"] > label:hover {
        border-color: #4A90E2;
        box-shadow: 0 0 6px rgba(74, 144, 226, 0.4);
    }
    </style>
    """,
    unsafe_allow_html=True
)

tab = st.radio(
    "Navigation",
    [
        "Search Plants By Name",
        "Call Directory Overview",
        "All Plants",
        "Sales Activity",
        "Outtages",
    ],
    horizontal=True,
    key="main_nav",
)

st.markdown(
    """
    <style>
    label[for="main_nav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------
# TAB FUNCTION
# ------------------------------------------------------
def tab_search_plants():
    st.header("🏭 Powerplants with Contacts & Drives")

    try:
        plant_option, fuel_options, manufacturer_options, drive_info_options = load_filter_data()
    except Exception as e:
        st.error(f"Error loading dropdown data: {e}")
        plant_option, fuel_options, manufacturer_options, drive_info_options = ["All"], ["All"], ["All"], ["All"]

    df = load_main_plant_summary()

    st.dataframe(df, use_container_width=True, hide_index=True)


# ------------------------------------------------------
# ROUTING
# ------------------------------------------------------
if tab == "Search Plants By Name":
    tab_search_plants()

elif tab == "Call Directory Overview":
    call_directory(conn)

elif tab == "All Plants":
    display_all_plant(conn)

elif tab == "Sales Activity":
    display_sales_activity(conn)

elif tab == "Outtages":
    display_outtages(conn)

# ------------------------------------------------------
# FOOTER
# ------------------------------------------------------
st.sidebar.caption("To reset search refresh the page! 🔄")
st.sidebar.caption("Made by: Raul Ostorga & Oscar Ostorga")


#
#⠀⠀⠀⠀⠀⠀⠀⠀⣠⡤⠒⠛⣋⣉⡛⠲⢿⣄⣀⣠⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⣠⠞⠁⠀⣴⣿⣿⣿⣿⣧⣀⣿⣿⣿⣿⣿⣷⠦⢤⣀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⡼⠁⠀⠀⢠⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⠀⠀⠈⠻⣦⠀⠀
#⠀⠀⠀⠀⡼⢁⠀⣤⣶⠟⠻⢿⣿⣿⡿⠟⠀⠘⠻⠿⠿⠟⠁⠀⠀⠀⠀⠈⢷⠀
#⠀⠀⠀⣼⢳⣿⣦⡹⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣶⣶⣦⠀⠀⠀⠀⢸⡇
#⠀⢀⣼⡇⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠁⠀⠀⠀⠀⣸⠇
#⢠⣿⢿⡇⣿⣿⣿⣿⣿⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠏⠀
#⠀⠉⠈⣷⣿⣿⣿⣿⣿⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⠴⠞⠛⠁⠀⠀
#⠀⠀⠀⠈⠿⣿⣿⡿⢟⣼⠗⠲⠦⢤⣀⠀⠀⠀⢀⡴⠚⠉⠁⠀⠀⠀⠀⠀⠀⠀
#⢀⣤⣶⡛⢳⡮⢉⣛⣋⣁⣀⣀⣀⣀⡾⠓⠤⠤⠞⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠸⣄⠈⠉⢸⡟⠉⠀⠀⠀⠀⠀⠀⠉⠙⠂⠤⠤⠤⠾⣟⣧⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⢸⡇⠀⣸⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⡄⠀⠀⠀⠀⠀⠀⠀
#⠀⠈⠓⠲⠋⠀⠉⠉⠉⠉⠉⠉⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⣄⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣏⠀⠀⠀⠀⠀⠀⠀⠀⢀⣧⣽⡄⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠤⠤⣿⣦⠤⠤⠤⠤⠄⠐⠒⠛⠋⠀⢹⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠛⠉⠉⠉⢷⣄⠀⠀⠀⠀⢀⣄⠀⠀⣼⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣛⣶⡶⠚⠛⠓⠒⠒⠛⠲⣄⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠼⣯⣅⣖⣀⣒⣘⣙⣦⣈⣷⣀⣸⠇⠀⠀
#
# Need something?