# Factory-to-Customer Shipping Route Efficiency Analysis
### Nassau Candy Distributor | Unified Mentor Data Analytics Internship — Project 2

## Overview
Nassau Candy Distributor ships products from 5 factories to customers across the US and Canada, but had no visibility into which factory-to-customer routes were efficient, where delays were happening, or how shipping method affected reliability. This project builds that visibility from raw order/shipment data.

## Repository structure
```
.
├── README.md
├── requirements.txt
├── 01_data_cleaning.py                          # cleans data, fixes the Ship Date bug, builds Route + KPIs
├── 02_route_analysis.py                         # route / state / ship-mode benchmarking
├── 03_charts.py                                 # regenerates the 3 charts used in the report
├── app.py                                       # Streamlit dashboard
├── Nassau_Candy_Shipping_Efficiency_Research_Paper.docx # full research paper (EDA, methodology, findings)
├── Nassau_Candy_Executive_Summary.docx          # 2-page stakeholder summary
├── data/
│   ├── Nassau_Candy_Distributor.csv             # raw input data
│   ├── cleaned_shipments.csv                    # output of 01_data_cleaning.py
│   ├── route_summary.csv                        # output of 02_route_analysis.py
│   ├── route_benchmark.csv                      # output of 02_route_analysis.py
│   ├── state_summary.csv                        # output of 02_route_analysis.py
│   ├── bottlenecks.csv                          # output of 02_route_analysis.py
│   └── ship_mode_summary.csv                    # output of 02_route_analysis.py
└── charts/
    ├── fig1_route_efficiency.png                # output of 03_charts.py
    ├── fig2_state_lead_time.png                 # output of 03_charts.py
    └── fig3_ship_mode.png                       # output of 03_charts.py
```
All CSV/PNG outputs are committed as-is so the dashboard and report can be reviewed immediately, but every one of them is fully reproducible by re-running the three numbered scripts in order (see below).

## Key finding worth reading first
While validating shipping lead time, I found the Ship Date column's **year** was corrupted — Order Dates were only ever 2024–2025, but Ship Dates were scattered across 2026–2030, and this scatter didn't correlate with shipping method (Same Day wasn't the fastest, which can't be right). I traced the issue and fixed it by reconstructing Ship Date's year from Order Date. The fix was sanity-checked (not proven) by confirming Ship Mode then ranked in the correct real-world order — full writeup, including the limitation that the resulting day-counts are a comparative index rather than literal calendar days, is in the research paper, Section 4.

## How to run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Reproduce the analysis (run in order; each script uses paths relative to
#    its own location, so this works from any directory)
python 01_data_cleaning.py     # cleans data, fixes date bug, builds Route + KPIs
python 02_route_analysis.py    # route/state/ship-mode benchmarking
python 03_charts.py            # regenerates report charts into charts/

# 3. Run the dashboard
streamlit run app.py
```

## Tech stack
Python (pandas, numpy) for cleaning & analysis · matplotlib for static report charts · Streamlit + Plotly for the interactive dashboard · python-docx for the report/summary documents.

## Deliverables (per project brief)
- [x] Research paper (EDA, insights, recommendations) — `Nassau_Candy_Shipping_Efficiency_Research_Paper.docx`
- [x] Streamlit dashboard (live analytics) — `app.py`
- [x] Executive summary — `Nassau_Candy_Executive_Summary.docx`

## Known limitations
- The corrected `Shipping Lead Time` values (~173–185 days) are a synthetic, internally-consistent index for **comparing** routes and ship modes against each other. They are not literal real-world shipping days — see Research Paper §4 for the full explanation.
- The Tennessee "bottleneck" finding is a **criterion-based** result (the one state meeting both a top-25%-volume and top-25%-lead-time threshold simultaneously), not a dramatic statistical outlier — the underlying lead-time gap versus the network average is modest (178.0 vs. 177.6 days). See Report §7.
