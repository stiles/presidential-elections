#!/usr/bin/env python
# coding: utf-8

import pandas as pd

"""
US presidential election results by county: 2000-2020
# Harvard/MIT: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
This notebook reads and processes county-level results collected by [MIT's election lab](https://electionlab.mit.edu/data)
"""

# Read raw data
counties_src = (
    pd.read_csv(
        "data/raw/countypres_2000-2020.csv",
        dtype={"county_fips": str, "year": str, "version": str},
    )
    # just major parties
    .query('party.str.contains("DEMOCRAT|REPUBLICAN") and totalvotes>0')
    # only county-level geographies (not federal precincts, overseas votes, etc.)
    .dropna(subset="county_fips")
)

# Clean up candidate names
counties_src["candidate"] = (
    counties_src["candidate"]
    .str.replace("JOSEPH R BIDEN JR", "JOE BIDEN")
    .str.replace("J TRUMP", "TRUMP")
)

# Aggregate to deal with states lacking "total" category (early, provisional, election day, etc.)
counties_agg_df = (
    counties_src.groupby(
        [
            "year",
            "state",
            "state_po",
            "county_name",
            "county_fips",
            "candidate",
            "party",
        ]
    )
    .agg({"candidatevotes": "sum", "totalvotes": "mean"})
    .reset_index()
)

# Make sure the fips is a five-digit string
counties_agg_df["county_fips"] = counties_agg_df["county_fips"].str.zfill(5)


# Wide format
counties_pivot = counties_agg_df.pivot(
    columns=["party"],
    values=["candidatevotes", "totalvotes"],
    index=["county_fips", "county_name", "state_po", "year"],
).reset_index().rename(columns={'county_fips':'fips'})


# Cleaning up multi-index df
counties_pivot.columns = [
    "_".join(filter(None, col))
    .strip()
    .lower()
    .replace("candidate", "")
    .replace("totalvotes_democrat", "votes_all")
    .replace("ocrat", "")
    .replace("ublican", "")
    for col in counties_pivot.columns
]

counties_df = counties_pivot.drop(["totalvotes_rep"], axis=1).copy()

# Calculate share
counties_df["dem_pct"] = counties_df["votes_dem"] / counties_df["votes_all"]
counties_df["rep_pct"] = counties_df["votes_rep"] / counties_df["votes_all"]

# Function to name winner
def calculate_winner(row):
    if row["dem_pct"] > row["rep_pct"]:
        return "dem"
    elif row["dem_pct"] < row["rep_pct"]:
        return "rep"
    else:
        return "tie"
    
    
# Apply 'winner' function
counties_df["winner"] = counties_df.apply(calculate_winner, axis=1)


# Separate the data for 2000 and 2020
df_2000 = counties_df[counties_df["year"] == "2000"].set_index(
    ["fips", "county_name", "state_po"]
)
df_2020 = counties_df[counties_df["year"] == "2020"].set_index(
    ["fips", "county_name", "state_po"]
)

# Merge the two years on fips
change_df = df_2000[["dem_pct", "rep_pct"]].merge(
    df_2020[["dem_pct", "rep_pct"]],
    left_index=True,
    right_index=True,
    suffixes=("_2000", "_2020"),
)


# Calculate the percentage point differences
change_df["dem_pct_diff"] = change_df["dem_pct_2020"] - change_df["dem_pct_2000"]
change_df["rep_pct_diff"] = change_df["rep_pct_2020"] - change_df["rep_pct_2000"]

# Reset index to have fips as a column again
change_df = change_df.reset_index()

# Exports
# Change from 2000 to 2020
change_df.to_json(
    "data/processed/presidential_county_change_2000_2020.json", indent=4, orient="records"
)
# Results and share by county and candidate - all elections
counties_df.to_json(
    "data/processed/presidential_county_results.json", indent=4, orient="records"
)