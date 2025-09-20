import streamlit as st
import pandas as pd
from fredapi import Fred
import matplotlib.pyplot as plt
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="FRED Economic Dashboard",
    page_icon="📈",
    layout="wide",
)

# --- FRED API Key Configuration ---
# You can set this as a secret in Streamlit Cloud, or directly here for a simple script.
# For production, it's recommended to use st.secrets.
# Create a file called `.streamlit/secrets.toml` with the following content:
# fred_api_key = "YOUR_API_KEY_HERE"

# Try to get API key from secrets, otherwise fall back to environment variable or hardcoded value.
try:
    FRED_API_KEY = st.secrets["fred_api_key"]
except KeyError:
    FRED_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual key if not using secrets

if not FRED_API_KEY or FRED_API_KEY == "YOUR_API_KEY_HERE":
    st.error("Please provide a FRED API key. See the code for instructions.")
    st.stop()

# Initialize FRED API client
fred = Fred(api_key=FRED_API_KEY)

# --- Data Caching to Avoid Repeated API Calls ---
@st.cache_data
def get_fred_data(series_id, start_date=None, end_date=None):
    """Fetches and caches data from the FRED API."""
    try:
        data = fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
        )
        if data is None or data.empty:
            return pd.DataFrame()
        
        # Rename the series to make it more readable
        data.name = fred.get_series_info(series_id)['title']
        return data.to_frame()
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return pd.DataFrame()

# --- Dashboard Layout and Content ---
st.title("FRED Economic Intelligence Dashboard")
st.markdown("This dashboard provides a simple view of key U.S. economic indicators sourced from the Federal Reserve Economic Data (FRED).")

# --- Sidebar for User Input ---
st.sidebar.header("Dashboard Controls")
selected_series_ids = st.sidebar.multiselect(
    "Select Economic Indicators",
    [
        "GDPC1",  # Real Gross Domestic Product
        "CPIAUCSL", # Consumer Price Index
        "UNRATE",   # Unemployment Rate
        "MORTGAGE30US", # 30-Year Fixed Rate Mortgage Average
        "PPIACO",   # Producer Price Index
        "DFF",      # Federal Funds Rate
        "CSUSHPINSA", # Case-Shiller Home Price Index
    ],
    default=["UNRATE", "GDPC1"]
)

start_date = st.sidebar.date_input("Start Date", datetime(2000, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now().date())

# --- Fetch and Display Data ---
if selected_series_ids:
    st.header("Economic Indicator Trends")

    # Fetch all selected series and merge them into a single DataFrame
    df_list = []
    for series_id in selected_series_ids:
        data = get_fred_data(series_id, start_date, end_date)
        if not data.empty:
            df_list.append(data)
    
    if df_list:
        combined_df = pd.concat(df_list, axis=1)
        
        # Create a line chart for all selected series
        st.line_chart(combined_df)

        st.divider()
        st.header("Detailed Data & Insights")
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Raw Data Table")
            st.dataframe(combined_df)
        
        with col2:
            st.subheader("Key Statistics")
            
            # --- Business Intelligence Insights using pandas aggregation ---
            for series_id in selected_series_ids:
                data = combined_df[fred.get_series_info(series_id)['title']].dropna()
                
                if not data.empty:
                    st.write(f"**{data.name}**")
                    col_stats1, col_stats2 = st.columns(2)
                    with col_stats1:
                        st.metric("Latest Value", f"{data.iloc[-1]:,.2f}")
                        st.metric("Average", f"{data.mean():,.2f}")
                        st.metric("Min", f"{data.min():,.2f}")
                    with col_stats2:
                        st.metric("Change from Previous", f"{data.iloc[-1] - data.iloc[-2]:,.2f}")
                        st.metric("Max", f"{data.max():,.2f}")
                        st.metric("Std. Dev.", f"{data.std():,.2f}")
                    st.write("---")
    else:
        st.warning("No data found for the selected indicators and date range.")
else:
    st.info("Please select at least one economic indicator from the sidebar.")

st.sidebar.markdown("---")
st.sidebar.info("Data provided by the Federal Reserve Bank of St. Louis (FRED).")