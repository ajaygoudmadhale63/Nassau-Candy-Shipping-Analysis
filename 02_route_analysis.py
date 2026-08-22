"""
Step 3: Route Definition & Aggregation
Step 4: Efficiency Benchmarking
Step 5: Geographic Bottleneck Analysis
Step 6: Ship Mode Performance Analysis

Reads the cleaned data and produces route-level, state-level, and
ship-mode-level summary tables that both the report and the Streamlit
dashboard will use.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths are relative to this script's location, so this works no matter
# where the repo is cloned or which directory it's run from.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

df = pd.read_csv(DATA_DIR / "cleaned_shipments.csv", parse_dates=["Order Date", "Ship Date"])

LEAD = "Shipping Lead Time (Days)"

# ---------------------------------------------------------------
# STEP 3: Route Definition & Aggregation (Factory -> State)
# ---------------------------------------------------------------
route_summary = (
    df.groupby("Route (State)")
    .agg(
        Factory=("Factory", "first"),
        State=("State/Province", "first"),
        Region=("Region", "first"),
        Total_Shipments=(LEAD, "count"),
        Avg_Lead_Time=(LEAD, "mean"),
        Lead_Time_StdDev=(LEAD, "std"),
        Total_Sales=("Sales", "sum"),
    )
    .reset_index()
)
route_summary["Lead_Time_StdDev"] = route_summary["Lead_Time_StdDev"].fillna(0)

# Only benchmark routes with a meaningful sample size (avoid ranking a route
# that had just 1 order - not statistically reliable)
MIN_SHIPMENTS = 5
reliable_routes = route_summary[route_summary["Total_Shipments"] >= MIN_SHIPMENTS].copy()

# ---------------------------------------------------------------
# STEP 4: Efficiency Benchmarking
# ---------------------------------------------------------------
reliable_routes = reliable_routes.sort_values("Avg_Lead_Time")

# Route Efficiency Score: normalize lead time to a 0-100 scale where
# 100 = fastest route, 0 = slowest route (min-max normalization, inverted)
min_lead, max_lead = reliable_routes["Avg_Lead_Time"].min(), reliable_routes["Avg_Lead_Time"].max()
reliable_routes["Route_Efficiency_Score"] = (
    100 * (max_lead - reliable_routes["Avg_Lead_Time"]) / (max_lead - min_lead)
).round(1)

top10 = reliable_routes.head(10)
bottom10 = reliable_routes.tail(10)

print("=== TOP 10 MOST EFFICIENT ROUTES ===")
print(top10[["Route (State)", "Total_Shipments", "Avg_Lead_Time", "Route_Efficiency_Score"]].to_string(index=False))
print()
print("=== BOTTOM 10 LEAST EFFICIENT ROUTES ===")
print(bottom10[["Route (State)", "Total_Shipments", "Avg_Lead_Time", "Route_Efficiency_Score"]].to_string(index=False))

# ---------------------------------------------------------------
# Delay Frequency KPI: % of shipments exceeding a threshold
# Threshold = overall mean + 1 standard deviation (statistically "unusually slow")
# ---------------------------------------------------------------
overall_mean = df[LEAD].mean()
overall_std = df[LEAD].std()
DELAY_THRESHOLD = round(overall_mean + overall_std, 1)
df["Is_Delayed"] = df[LEAD] > DELAY_THRESHOLD

print(f"\nDelay threshold (mean + 1 std): {DELAY_THRESHOLD} days")
print(f"Overall delay frequency: {df['Is_Delayed'].mean()*100:.1f}%")

# ---------------------------------------------------------------
# STEP 5: Geographic Bottleneck Analysis (state level)
# ---------------------------------------------------------------
state_summary = (
    df.groupby(["State/Province", "Region", "Country/Region"])
    .agg(
        Total_Shipments=(LEAD, "count"),
        Avg_Lead_Time=(LEAD, "mean"),
        Delay_Rate_Pct=("Is_Delayed", lambda x: round(x.mean() * 100, 1)),
    )
    .reset_index()
    .sort_values("Avg_Lead_Time", ascending=False)
)

# Bottleneck = high volume AND high average lead time (top 25% on both)
vol_threshold = state_summary["Total_Shipments"].quantile(0.75)
lead_threshold = state_summary["Avg_Lead_Time"].quantile(0.75)
bottlenecks = state_summary[
    (state_summary["Total_Shipments"] >= vol_threshold) & (state_summary["Avg_Lead_Time"] >= lead_threshold)
].sort_values("Avg_Lead_Time", ascending=False)

print(f"\n=== GEOGRAPHIC BOTTLENECKS (high volume + high lead time) ===")
print(bottlenecks[["State/Province", "Region", "Total_Shipments", "Avg_Lead_Time", "Delay_Rate_Pct"]].to_string(index=False))

# ---------------------------------------------------------------
# STEP 6: Ship Mode Performance Analysis
# ---------------------------------------------------------------
ship_mode_summary = (
    df.groupby("Ship Mode")
    .agg(
        Total_Shipments=(LEAD, "count"),
        Avg_Lead_Time=(LEAD, "mean"),
        Median_Lead_Time=(LEAD, "median"),
        Delay_Rate_Pct=("Is_Delayed", lambda x: round(x.mean() * 100, 1)),
        Avg_Sales=("Sales", "mean"),
    )
    .reset_index()
    .sort_values("Avg_Lead_Time")
)
print("\n=== SHIP MODE PERFORMANCE ===")
print(ship_mode_summary.to_string(index=False))

# ---------------------------------------------------------------
# Save all summary tables for the report + dashboard
# ---------------------------------------------------------------
df.to_csv(DATA_DIR / "cleaned_shipments.csv", index=False)  # re-save with Is_Delayed flag
route_summary.to_csv(DATA_DIR / "route_summary.csv", index=False)
reliable_routes.to_csv(DATA_DIR / "route_benchmark.csv", index=False)
state_summary.to_csv(DATA_DIR / "state_summary.csv", index=False)
bottlenecks.to_csv(DATA_DIR / "bottlenecks.csv", index=False)
ship_mode_summary.to_csv(DATA_DIR / "ship_mode_summary.csv", index=False)

print(f"\nAll summary tables saved to {DATA_DIR}/")
