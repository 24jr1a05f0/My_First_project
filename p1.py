import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Dict, Any, Tuple

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------
API_URL = "https://open.er-api.com/v6/latest/USD"
FALLBACK_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.25,
    "JPY": 155.0,
    "CAD": 1.36,
    "AUD": 1.51,
    "CHF": 0.90,
    "CNY": 7.23,
    "SGD": 1.35,
}

POPULAR_CURRENCIES = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD"]

# Page Setup
st.set_page_config(
    page_title="Pranasya Currency Converter",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #6B7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: bold;
        color: #1D4ED8;
    }
    </style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Helper Functions & API Integration
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # Cache rates for 1 hour
def fetch_exchange_rates() -> Tuple[Dict[str, float], str, bool]:
    """
    Fetches real-time exchange rates relative to USD from Open Exchange Rates API.
    
    Returns:
        rates (dict): Currency codes mapped to rate values against USD.
        last_updated (str): Formatted string of last update time.
        is_live (bool): True if fetched live, False if fallback data used.
    """
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("result") == "success":
            rates = data.get("rates", {})
            last_updated_ts = data.get("time_last_update_unix")
            last_updated = datetime.fromtimestamp(last_updated_ts).strftime('%Y-%m-%d %H:%M:%S UTC') if last_updated_ts else "Just now"
            return rates, last_updated, True
    except (requests.RequestException, ValueError, KeyError):
        pass  # Graceful degradation on network error or bad JSON
    
    # Fallback if API fails
    return FALLBACK_RATES, "Offline / Fallback Data", False


def convert_currency(amount: float, from_curr: str, to_curr: str, rates: Dict[str, float]) -> Tuple[float, float]:
    """
    Converts amount from source currency to target currency using USD relative rates.
    """
    usd_amount = amount / rates[from_curr]
    converted_amount = usd_amount * rates[to_curr]
    rate_ratio = rates[to_curr] / rates[from_curr]
    return converted_amount, rate_ratio


# -----------------------------------------------------------------------------
# Sidebar Navigation & Instructions
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1086/1086741.png", width=80)
    st.title("Pranasya Converter")
    st.caption("Version 1.0.0")
    
    st.markdown("---")
    st.subheader("💡 How to use")
    st.markdown("""
    1. Enter the **Amount** you wish to convert.
    2. Choose source (**From**) and target (**To**) currencies.
    3. Click **↔️ Swap** to swap currencies quickly.
    4. View real-time output and market overview chart below.
    """)
    
    st.markdown("---")
    st.info("📊 **Note:** Rates update automatically every hour from reliable public API endpoints.")
    st.markdown("Developed with ❤️ by **Pranasya Team**")


# -----------------------------------------------------------------------------
# Main Application Content
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">💱 Pranasya Currency Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-time Global Foreign Exchange Rates & Analytics</div>', unsafe_allow_html=True)

# Load data with caching
rates, last_updated, is_live = fetch_exchange_rates()

if not is_live:
    st.warning("⚠️ Could not fetch live rates. Displaying cached fallback exchange rates.")

currency_list = sorted(list(rates.keys()))

# Initialize session state for currency swapping
if "from_curr" not in st.session_state:
    st.session_state["from_curr"] = "USD"
if "to_curr" not in st.session_state:
    st.session_state["to_curr"] = "INR"

def swap_currencies():
    temp = st.session_state["from_curr"]
    st.session_state["from_curr"] = st.session_state["to_curr"]
    st.session_state["to_curr"] = temp

# Input Container
with st.container():
    col_amt, col_from, col_swap, col_to = st.columns([2.5, 2.5, 1, 2.5])

    with col_amt:
        amount = st.number_input(
            "Amount to Convert",
            min_value=0.01,
            value=100.0,
            step=10.0,
            format="%.2f"
        )

    with col_from:
        from_curr = st.selectbox(
            "From Currency",
            options=currency_list,
            key="from_curr"
        )

    with col_swap:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        st.button("↔️ Swap", on_click=swap_currencies, use_container_width=True, help="Click to swap currencies")

    with col_to:
        to_curr = st.selectbox(
            "To Currency",
            options=currency_list,
            key="to_curr"
        )

# Calculation
converted_amount, rate_ratio = convert_currency(amount, from_curr, to_curr, rates)

st.markdown("---")

# Display Results
res_col1, res_col2 = st.columns([1, 1])

with res_col1:
    st.metric(
        label=f"Converted Amount ({to_curr})",
        value=f"{converted_amount:,.2f} {to_curr}",
        delta=f"1 {from_curr} = {rate_ratio:.4f} {to_curr}"
    )

with res_col2:
    st.caption("ℹ️ Exchange Rate Info")
    st.write(f"**Base Rate:** 1 {from_curr} = `{rate_ratio:.6f}` {to_curr}")
    st.write(f"**Inverse Rate:** 1 {to_curr} = `{(1/rate_ratio):.6f}` {from_curr}")
    st.write(f"**Last Updated:** `{last_updated}`")

st.markdown("---")

# -----------------------------------------------------------------------------
# Comparison Chart (Bonus Feature)
# -----------------------------------------------------------------------------
st.subheader(f"📊 Market Comparison for {amount:,.2f} {from_curr}")

# Compare against major world currencies
comparison_currencies = [c for c in POPULAR_CURRENCIES if c != from_curr]
comparison_data = []

for curr in comparison_currencies:
    comp_val, _ = convert_currency(amount, from_curr, curr, rates)
    comparison_data.append({
        "Currency": curr,
        "Converted Value": comp_val
    })

df_comp = pd.DataFrame(comparison_data)

# Create Plotly Bar Chart
fig = px.bar(
    df_comp,
    x="Currency",
    y="Converted Value",
    text_auto=".2f",
    title=f"Equivalent value of {amount:,.2f} {from_curr} in Major Currencies",
    color="Converted Value",
    color_continuous_scale="Blues"
)

fig.update_layout(
    xaxis_title="Currency Code",
    yaxis_title=f"Value in Currency",
    showlegend=False,
    height=400,
    margin=dict(l=20, r=20, t=50, b=20)
)

st.plotly_chart(fig, use_container_width=True)