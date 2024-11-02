#!/usr/bin/env python
# coding: utf-8

# Presidential results by state, 1972-2020
# Source: Dave Leip's US Election Atlas
# https://uselectionatlas.org/RESULTS/data.php?year={INSERTYEAR}&datatype=national&def=1&f=1&off=0&elect=0

import us
import requests
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup

# Configuration
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
}
presidential_years = list(range(1972, 2020 + 1, 4))

# Column mappings for each election
column_mappings = {
    1972: ['state', 'r_ev', 'd_ev', 'o_ev', 'total vote', 'r', 'd', 'r_pct', 'd_pct', 'other_pct', 'r_votes', 'd_votes', 'o_votes'],
    1976: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'd_pct', 'r_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes'],
    1980: ['state', 'r_ev', 'd_ev', 'total vote', 'r', 'd', 'o', 'r_pct', 'd_pct', 'other_pct', 'other2_pct', 'd_votes', 'r_votes', 'o_votes', 'other2_votes'],
    1984: ['state', 'r_ev', 'd_ev', 'total vote', 'r', 'd', 'r_pct', 'd_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes'],
    1988: ['state', 'r_ev', 'd_ev', 'total vote', 'r', 'd', 'r_pct', 'd_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes'],
    1992: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'o', 'd_pct', 'r_pct', 'other_pct', 'other2_pct', 'd_votes', 'r_votes', 'o_votes', 'other2_votes'],
    1996: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'o', 'd_pct', 'r_pct', 'other_pct', 'other2_pct', 'd_votes', 'r_votes', 'o_votes', 'other2_votes'],
    2000: ['state', 'r_ev', 'd_ev', 'total vote', 'd', 'r', 'o', 'd_pct', 'r_pct', 'other_pct', 'other2_pct', 'd_votes', 'r_votes', 'o_votes', 'other2_votes'],
    2004: ['state', 'r_ev', 'd_ev', 'total vote', 'r', 'd', 'r_pct', 'd_pct', 'other_pct', 'r_votes', 'd_votes', 'o_votes'],
    2008: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'd_pct', 'r_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes'],
    2012: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'd_pct', 'r_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes'],
    2016: ['state', 'r_ev', 'd_ev', 'o_ev', 'total vote', 'd', 'r', 'o', 'd_pct', 'r_pct', 'other_pct', 'other2_pct', 'd_votes', 'r_votes', 'o_votes', 'other2_votes'],
    2020: ['state', 'd_ev', 'r_ev', 'total vote', 'd', 'r', 'd_pct', 'r_pct', 'other_pct', 'd_votes', 'r_votes', 'o_votes']
}


# Function to get the data from each year's page
def fetch_and_parse_election_data(year, headers):
    params = {
        'elect': '0', 'def': '1', 'datatype': 'national', 'f': '1', 'off': '0', 'year': year,
    }
    response = requests.get('https://uselectionatlas.org/RESULTS/data.php', params=params, headers=headers)
    html_content = BeautifulSoup(response.text, 'html.parser')
    df = pd.read_html(StringIO(str(html_content)))[1]
    return df.query('~State.isnull() and ~Margin.isnull() and State != "Total"').drop(['Map', 'Pie', 'Margin', '%Margin'], axis=1, errors='ignore')

# Fetch, process, and standardize data
dfs = []
for year in presidential_years:
    df = fetch_and_parse_election_data(year, headers)
    if year in column_mappings:
        df.columns = column_mappings[year]
    else:
        continue
    df['year'] = year
    dfs.append(df)

all_pres_years_src = pd.concat(dfs).reset_index(drop=True)
all_pres_years_src['other_votes'] = all_pres_years_src[['other2_votes', 'o_votes']].fillna(0).sum(axis=1)

# Final cleanup and calculations
def calculate_percentages(df):
    df['r_pct'] = round((df['r_votes'] / df['total vote']) * 100, 2)
    df['d_pct'] = round((df['d_votes'] / df['total vote']) * 100, 2)
    df['o_pct'] = round((df['other_votes'] / df['total vote']) * 100, 2)
    return df

all_pres_years_slim = calculate_percentages(all_pres_years_src.drop(['r', 'd', 'o', 'o_ev', 'other_pct', 'other2_pct'], axis=1, errors='ignore'))
all_pres_years_slim['winner'] = all_pres_years_slim[['r_ev', 'd_ev']].idxmax(axis=1).str.replace('r_ev', 'REP').str.replace('d_ev', 'DEM')

# Output files
output_base_path = "data/processed/presidential_results_states"
for fmt in ["csv", "json"]:
    all_pres_years_slim.to_csv(f"{output_base_path}_all.csv", index=False) if fmt == "csv" else \
    all_pres_years_slim.to_json(f"{output_base_path}_all.json", indent=4, orient='records')