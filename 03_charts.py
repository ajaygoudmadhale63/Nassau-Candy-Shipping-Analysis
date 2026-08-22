"""
Step 7: Report Charts
Factory-to-Customer Shipping Route Efficiency Analysis - Nassau Candy Distributor

Regenerates the 3 static figures embedded in the research paper
(Nassau_Candy_Shipping_Efficiency_Report.docx), reading from the summary
CSVs produced by 02_route_analysis.py. Run 01 and 02 before this script.

Output: PNG files saved to charts/
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------
# Figure 1: Top 10 most efficient vs bottom 10 least efficient routes
# ---------------------------------------------------------------
reliable_routes = pd.read_csv(DATA_DIR / "route_benchmark.csv").sort_values("Avg_Lead_Time")
top10 = reliable_routes.head(10)
bottom10 = reliable_routes.tail(10)
combined = pd.concat([top10, bottom10])
colors = ["#2E7D32"] * len(top10) + ["#C62828"] * len(bottom10)

fig, ax = plt.subplots(figsize=(11, 7))
ax.barh(combined["Route (State)"], combined["Avg_Lead_Time"], color=colors)
ax.invert_yaxis()
ax.set_xlabel("Average Shipping Lead Time (Days)")
ax.set_title("Top 10 Most Efficient vs Bottom 10 Least Efficient Routes")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "fig1_route_efficiency.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# Figure 2: 15 states with the highest average lead time
# ---------------------------------------------------------------
state_summary = pd.read_csv(DATA_DIR / "state_summary.csv")
top15_slow = state_summary.sort_values("Avg_Lead_Time", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(11, 7))
ax.barh(top15_slow["State/Province"], top15_slow["Avg_Lead_Time"], color="#AD1457")
ax.invert_yaxis()
ax.set_xlabel("Average Shipping Lead Time (Days)")
ax.set_title("15 States With the Highest Average Lead Time")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "fig2_state_lead_time.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# Figure 3: Avg lead time and delay rate by ship mode
# ---------------------------------------------------------------
ship_mode_summary = pd.read_csv(DATA_DIR / "ship_mode_summary.csv").sort_values("Avg_Lead_Time")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].bar(ship_mode_summary["Ship Mode"], ship_mode_summary["Avg_Lead_Time"], color="#1565C0")
axes[0].set_ylabel("Days")
axes[0].set_title("Avg Lead Time by Ship Mode")
axes[0].tick_params(axis="x", rotation=20)

axes[1].bar(ship_mode_summary["Ship Mode"], ship_mode_summary["Delay_Rate_Pct"], color="#EF6C00")
axes[1].set_ylabel("% of shipments delayed")
axes[1].set_title("Delay Rate by Ship Mode")
axes[1].tick_params(axis="x", rotation=20)

plt.tight_layout()
plt.savefig(CHARTS_DIR / "fig3_ship_mode.png", dpi=150)
plt.close()

print(f"Saved 3 charts to {CHARTS_DIR}/")
