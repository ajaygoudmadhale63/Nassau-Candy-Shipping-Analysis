"""
Step 1: Data Cleaning & Validation + Step 2: Feature Engineering
Factory-to-Customer Shipping Route Efficiency Analysis - Nassau Candy Distributor

What this script does (in plain English):
1. Loads the raw order/shipment data
2. Fixes a data quality bug in the Ship Date column (explained below)
3. Builds the "Route" (Factory -> Customer State/Region) for every order
4. Calculates the KPIs we need for the rest of the analysis
5. Saves a clean file that the EDA notebook and Streamlit app will both use
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths are relative to this script's location, so this works no matter
# where the repo is cloned or which directory it's run from.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_PATH = DATA_DIR / "Nassau_Candy_Distributor.csv"
CLEAN_PATH = DATA_DIR / "cleaned_shipments.csv"

# ---------------------------------------------------------------
# Lookup tables that come from the project brief (not in the CSV)
# ---------------------------------------------------------------

# Factory location, from the "Factories Co-ordinates" table in the brief
FACTORY_COORDS = {
    "Lot's O' Nuts":     {"lat": 32.881893, "lon": -111.768036},
    "Wicked Choccy's":   {"lat": 32.076176, "lon": -81.088371},
    "Sugar Shack":       {"lat": 48.119140, "lon": -96.181150},
    "Secret Factory":    {"lat": 41.446333, "lon": -90.565487},
    "The Other Factory": {"lat": 35.117500, "lon": -89.971107},
}

# Which factory makes which product, from "Products and Factories Correlation"
PRODUCT_TO_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Kazookles": "The Other Factory",
}

df = pd.read_csv(RAW_PATH)
print(f"Loaded {len(df)} rows, {df.shape[1]} columns")

# ---------------------------------------------------------------
# STEP 1: Data Cleaning & Validation
# ---------------------------------------------------------------

# 1a. Parse dates (format in file is DD-MM-YYYY)
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
df["Ship Date_raw"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y")

# 1b. Standardize text/geographic fields (strip whitespace, consistent case)
for col in ["City", "State/Province", "Division", "Region", "Ship Mode", "Country/Region"]:
    df[col] = df[col].astype(str).str.strip()

# 1c. Duplicate & missing value check (kept here for transparency; dataset is clean)
assert df.duplicated().sum() == 0, "Unexpected duplicate rows found"
assert df.isna().sum().sum() == 0, "Unexpected missing values found"

# 1d. THE KEY DATA QUALITY FIX
# ---------------------------------------------------------------
# Problem found during EDA: Ship Date's YEAR is corrupted.
#   - Order Date only ever falls in 2024-2025 (2 realistic years)
#   - Ship Date falls in 2026-2030 (5 years), and the spread of years is
#     RANDOM with respect to Ship Mode (Same Day isn't the fastest, which
#     makes no business sense -> the year field is noise, not signal).
#   - Raw (Ship Date - Order Date) averages ~1,300 days, which is obviously
#     not a real shipping lead time for candy.
#
# Fix: keep the Ship Date's month & day (that part is trustworthy) but
# replace its year with the Order Date's year. If that lands the ship
# date BEFORE the order date, roll it forward by one year (an order can't
# ship before it was placed).
#
# After this fix, Ship Mode ranks in the exact order you'd expect
# (Same Day fastest -> Standard Class slowest), which is strong evidence
# this is the correct reconstruction.

def fix_ship_date(row):
    try:
        d = row["Ship Date_raw"].replace(year=row["Order Date"].year)
    except ValueError:  # Feb 29 edge case
        d = row["Ship Date_raw"].replace(year=row["Order Date"].year, day=28)
    if d < row["Order Date"]:
        try:
            d = d.replace(year=d.year + 1)
        except ValueError:
            d = d.replace(year=d.year + 1, day=28)
    return d

df["Ship Date"] = df.apply(fix_ship_date, axis=1)
df["Shipping Lead Time (Days)"] = (df["Ship Date"] - df["Order Date"]).dt.days

# 1e. Remove any invalid / negative lead times (safety net, should be none after fix)
before = len(df)
df = df[df["Shipping Lead Time (Days)"] >= 0].copy()
print(f"Removed {before - len(df)} rows with invalid lead time")

df.drop(columns=["Ship Date_raw"], inplace=True)

# ---------------------------------------------------------------
# STEP 2: Feature Engineering
# ---------------------------------------------------------------

# 2a. Map every order to its factory using the product it contains
df["Factory"] = df["Product Name"].map(PRODUCT_TO_FACTORY)
assert df["Factory"].isna().sum() == 0, "Some products didn't map to a factory - check spelling"

# 2b. Attach factory coordinates
df["Factory_Lat"] = df["Factory"].map(lambda f: FACTORY_COORDS[f]["lat"])
df["Factory_Lon"] = df["Factory"].map(lambda f: FACTORY_COORDS[f]["lon"])

# 2c. Define the Route: Factory -> Customer State  (also keep a coarser Region-level route)
df["Route (State)"] = df["Factory"] + " -> " + df["State/Province"]
df["Route (Region)"] = df["Factory"] + " -> " + df["Region"]

# Save
df.to_csv(CLEAN_PATH, index=False)
print(f"Saved cleaned data -> {CLEAN_PATH}")
print(df[["Order Date", "Ship Date", "Ship Mode", "Shipping Lead Time (Days)", "Factory", "Route (State)"]].head())
print()
print("Lead time by Ship Mode (sanity check - should rank Same Day < First < Second < Standard):")
print(df.groupby("Ship Mode")["Shipping Lead Time (Days)"].mean().sort_values())
