#!/usr/bin/env python
# coding: utf-8

import pandas as pd

"""
US presidential election results by county: 2016-2020
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
counties_df["dem_pct"] = round((counties_df["votes_dem"] / counties_df["votes_all"])*100,2)
counties_df["rep_pct"] = round((counties_df["votes_rep"] / counties_df["votes_all"])*100,2)

# Margin
counties_df["margin"] = counties_df["rep_pct"] - counties_df["dem_pct"]

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


# Separate the data for 2016 and 2020
df_2016 = counties_df[counties_df["year"] == "2016"].set_index(
    ["fips", "county_name", "state_po"]
)
df_2020 = counties_df[counties_df["year"] == "2020"].set_index(
    ["fips", "county_name", "state_po"]
)

# Merge the two years on fips
change_df = df_2016[["dem_pct", "rep_pct", 'margin', 'winner']].merge(
    df_2020[["dem_pct", "rep_pct", 'margin', 'winner']],
    left_index=True,
    right_index=True,
    suffixes=("_2016", "_2020"),
)


# Calculate the percentage point differences
change_df["dem_pct_diff"] = change_df["dem_pct_2020"] - change_df["dem_pct_2016"]
change_df["rep_pct_diff"] = change_df["rep_pct_2020"] - change_df["rep_pct_2016"]
change_df["margin_diff"] = change_df["margin_2020"] - change_df["margin_2016"]

# Function to name winner
def determine_flip(row):
    if row["winner_2016"] == row["winner_2020"]:
        return False
    else:
        return True

# Apply 'winner' function
change_df["flipped"] = change_df.apply(determine_flip, axis=1)

# Reset index to have fips as a column again
change_df = change_df.reset_index()

# Exports
# Change from 2016 to 2020
change_df.round(2).to_json(
    "data/processed/presidential_county_change_2016_2020.json", indent=4, orient="records"
)
# Results and share by county and candidate - all elections
counties_df.round(2).to_json(
    "data/processed/presidential_county_results.json", indent=4, orient="records"
)