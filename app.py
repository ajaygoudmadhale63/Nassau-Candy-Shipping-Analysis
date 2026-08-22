"""
Factory-to-Customer Shipping Route Efficiency Dashboard
Nassau Candy Distributor | Unified Mentor Internship Project 2

Run locally with:  streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy | Shipping Route Efficiency",
    page_icon="🚚",
    layout="wide",
)

# Data path is relative to this script's location, so `streamlit run app.py`
# works no matter which directory it's launched from.
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned_shipments.csv"

US_STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# Factory locations, taken from the "Factories Co-ordinates" reference table
# in the official project brief (not present in the raw CSV).
FACTORY_COORDS = {
    "Lot's O' Nuts":     {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's":   {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack":       {"lat": 48.119140, "lon": -96.181150},
    "Secret Factory":    {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory": {"lat": 35.117500, "lon": -89.971107},
}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["Order Date", "Ship Date"])
    return df


df = load_data()

# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.title("🍬 Nassau Candy")
st.sidebar.caption("Factory-to-Customer Shipping Route Efficiency")

min_date, max_date = df["Order Date"].min(), df["Order Date"].max()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

regions = st.sidebar.multiselect("Region", sorted(df["Region"].unique()), default=list(df["Region"].unique()))
states = st.sidebar.multiselect("State / Province", sorted(df["State/Province"].unique()))
ship_modes = st.sidebar.multiselect(
    "Ship Mode", sorted(df["Ship Mode"].unique()), default=list(df["Ship Mode"].unique())
)
lead_threshold = st.sidebar.slider(
    "Lead-time threshold (days) — flags shipments slower than this",
    int(df["Shipping Lead Time (Days)"].min()),
    int(df["Shipping Lead Time (Days)"].max()),
    int(df["Shipping Lead Time (Days)"].mean() + df["Shipping Lead Time (Days)"].std()),
)
st.sidebar.caption(
    "Default = network mean + 1 std dev (the same delay definition used in the research paper). "
    "Drag to explore other cutoffs."
)

# Apply filters
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["Order Date"] >= pd.Timestamp(date_range[0])) & (fdf["Order Date"] <= pd.Timestamp(date_range[1]))]
if regions:
    fdf = fdf[fdf["Region"].isin(regions)]
if states:
    fdf = fdf[fdf["State/Province"].isin(states)]
if ship_modes:
    fdf = fdf[fdf["Ship Mode"].isin(ship_modes)]
fdf["Above_Threshold"] = fdf["Shipping Lead Time (Days)"] > lead_threshold

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(fdf):,}** of {len(df):,} shipments")

# ---------------------------------------------------------------
# Header + KPI row
# ---------------------------------------------------------------
st.title("🚚 Factory-to-Customer Shipping Route Efficiency")
st.caption("Nassau Candy Distributor — Data-driven visibility into route performance, bottlenecks, and ship mode trade-offs")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Shipments", f"{len(fdf):,}")
k2.metric("Avg Lead Time", f"{fdf['Shipping Lead Time (Days)'].mean():.1f} days" if len(fdf) else "—")
k3.metric("Delay Rate", f"{fdf['Above_Threshold'].mean()*100:.1f}%" if len(fdf) else "—")
k4.metric("Active Routes", f"{fdf['Route (State)'].nunique():,}")
k5.metric("Total Sales", f"${fdf['Sales'].sum():,.0f}")

st.caption(
    "⚠️ **Data quality note:** the source Ship Date field had a corrupted year, which was reconstructed "
    "from Order Date (see Report §4 for the full method). Lead-time values above are a corrected, "
    "**relative/comparable index** — useful for ranking routes and ship modes against each other — "
    "not a literal count of real-world shipping days."
)
st.caption(
    f"**Delay Rate** = % of shipments above the lead-time threshold set in the sidebar "
    f"(default = network mean + 1 standard deviation ≈ **{df['Shipping Lead Time (Days)'].mean() + df['Shipping Lead Time (Days)'].std():.1f} days**, "
    f"matching the methodology used in the research paper). Move the **Lead-time threshold** slider "
    f"in the sidebar to test other cutoffs."
)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Route Efficiency Overview", "🗺️ Geographic Shipping Map", "📦 Ship Mode Comparison", "🔎 Route Drill-Down"]
)

# ---------------------------------------------------------------
# TAB 1: Route Efficiency Overview
# ---------------------------------------------------------------
with tab1:
    st.subheader("Route Performance Leaderboard")
    st.caption("Routes with fewer than 5 shipments are excluded to keep the ranking statistically reliable.")

    route_perf = (
        fdf.groupby("Route (State)")
        .agg(
            Factory=("Factory", "first"),
            State=("State/Province", "first"),
            Total_Shipments=("Shipping Lead Time (Days)", "count"),
            Avg_Lead_Time=("Shipping Lead Time (Days)", "mean"),
        )
        .reset_index()
    )
    route_perf = route_perf[route_perf["Total_Shipments"] >= 5]

    if len(route_perf) > 0:
        rmin, rmax = route_perf["Avg_Lead_Time"].min(), route_perf["Avg_Lead_Time"].max()
        denom = (rmax - rmin) if rmax != rmin else 1
        route_perf["Efficiency_Score"] = (100 * (rmax - route_perf["Avg_Lead_Time"]) / denom).round(1)
        route_perf = route_perf.sort_values("Avg_Lead_Time")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🟢 Top 10 Most Efficient Routes**")
            fig = px.bar(
                route_perf.head(10), x="Avg_Lead_Time", y="Route (State)", orientation="h",
                color_discrete_sequence=["#2E7D32"], labels={"Avg_Lead_Time": "Avg Lead Time (days)"},
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**🔴 Bottom 10 Least Efficient Routes**")
            fig = px.bar(
                route_perf.tail(10), x="Avg_Lead_Time", y="Route (State)", orientation="h",
                color_discrete_sequence=["#C62828"], labels={"Avg_Lead_Time": "Avg Lead Time (days)"},
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Full Route Leaderboard**")
        st.dataframe(
            route_perf[["Route (State)", "Factory", "State", "Total_Shipments", "Avg_Lead_Time", "Efficiency_Score"]]
            .rename(columns={"Avg_Lead_Time": "Avg Lead Time (days)"})
            .style.format({"Avg Lead Time (days)": "{:.1f}"}),
            use_container_width=True, height=350,
        )
    else:
        st.info("No routes meet the minimum shipment count under current filters.")

# ---------------------------------------------------------------
# TAB 2: Geographic Shipping Map
# ---------------------------------------------------------------
with tab2:
    st.subheader("US Heatmap of Shipping Efficiency")

    us_states = fdf[fdf["Country/Region"] == "United States"]
    state_geo = (
        us_states.groupby("State/Province")
        .agg(Avg_Lead_Time=("Shipping Lead Time (Days)", "mean"), Shipments=("Shipping Lead Time (Days)", "count"))
        .reset_index()
    )
    state_geo["Code"] = state_geo["State/Province"].map(US_STATE_ABBR)
    state_geo = state_geo.dropna(subset=["Code"])

    fig = px.choropleth(
        state_geo, locations="Code", locationmode="USA-states", color="Avg_Lead_Time",
        scope="usa", color_continuous_scale="RdYlGn_r",
        hover_name="State/Province", hover_data={"Shipments": True, "Code": False},
        labels={"Avg_Lead_Time": "Avg Lead Time (days)"},
    )
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Regional Bottleneck View** — states with high volume *and* high average lead time")
    vol_thr = state_geo["Shipments"].quantile(0.75) if len(state_geo) else 0
    lead_thr = state_geo["Avg_Lead_Time"].quantile(0.75) if len(state_geo) else 0
    bottlenecks = state_geo[(state_geo["Shipments"] >= vol_thr) & (state_geo["Avg_Lead_Time"] >= lead_thr)]
    bottlenecks = bottlenecks.sort_values("Avg_Lead_Time", ascending=False)
    if len(bottlenecks):
        st.dataframe(bottlenecks[["State/Province", "Shipments", "Avg_Lead_Time"]], use_container_width=True)
    else:
        st.info("No bottleneck states under current filters.")

    st.markdown("**Factory Locations**")
    fac_df = pd.DataFrame(
        [{"Factory": f, "lat": c["lat"], "lon": c["lon"]} for f, c in FACTORY_COORDS.items()]
    )
    fig2 = px.scatter_geo(
        fac_df, lat="lat", lon="lon", text="Factory", scope="usa", color_discrete_sequence=["#5E35B1"],
    )
    fig2.update_traces(marker=dict(size=14))
    fig2.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------
# TAB 3: Ship Mode Comparison
# ---------------------------------------------------------------
with tab3:
    st.subheader("Lead Time & Delay Comparison by Ship Mode")

    sm = (
        fdf.groupby("Ship Mode")
        .agg(
            Total_Shipments=("Shipping Lead Time (Days)", "count"),
            Avg_Lead_Time=("Shipping Lead Time (Days)", "mean"),
            Delay_Rate=("Above_Threshold", lambda x: x.mean() * 100),
            Avg_Sales=("Sales", "mean"),
        )
        .reset_index()
        .sort_values("Avg_Lead_Time")
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(sm, x="Ship Mode", y="Avg_Lead_Time", color="Ship Mode",
                     labels={"Avg_Lead_Time": "Avg Lead Time (days)"}, title="Average Lead Time")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(sm, x="Ship Mode", y="Delay_Rate", color="Ship Mode",
                     labels={"Delay_Rate": "% Delayed"}, title="Delay Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Cost–Time Trade-off (descriptive)**")
    fig = px.scatter(
        sm, x="Avg_Lead_Time", y="Avg_Sales", size="Total_Shipments", color="Ship Mode",
        labels={"Avg_Lead_Time": "Avg Lead Time (days)", "Avg_Sales": "Avg Sales Value ($)"},
        title="Faster ship modes vs. average order value",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(sm.style.format({"Avg_Lead_Time": "{:.1f}", "Delay_Rate": "{:.1f}%", "Avg_Sales": "${:.2f}"}),
                 use_container_width=True)

# ---------------------------------------------------------------
# TAB 4: Route Drill-Down
# ---------------------------------------------------------------
with tab4:
    st.subheader("Drill Into a Specific Route")

    route_options = sorted(fdf["Route (State)"].unique())
    if route_options:
        selected_route = st.selectbox("Select a route (Factory → State)", route_options)
        rdf = fdf[fdf["Route (State)"] == selected_route]

        c1, c2, c3 = st.columns(3)
        c1.metric("Shipments on this route", f"{len(rdf):,}")
        c2.metric("Avg Lead Time", f"{rdf['Shipping Lead Time (Days)'].mean():.1f} days")
        c3.metric("Delay Rate", f"{rdf['Above_Threshold'].mean()*100:.1f}%")

        st.markdown("**State-level performance insight**")
        fig = px.histogram(rdf, x="Shipping Lead Time (Days)", nbins=15, color_discrete_sequence=["#1565C0"])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Order-level shipment timeline**")
        st.dataframe(
            rdf[["Order ID", "Order Date", "Ship Date", "Ship Mode", "City", "Product Name",
                 "Sales", "Shipping Lead Time (Days)"]]
            .sort_values("Order Date")
            .head(200),
            use_container_width=True, height=400,
        )
    else:
        st.info("No routes available under current filters.")

st.markdown("---")
st.caption("Built by Ajay | Unified Mentor Data Analytics Internship — Project 2: E-commerce/Logistics Analytics")
