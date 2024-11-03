import us
import requests
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

state_postal = us.states.mapping('name', 'abbr')
fips_name = us.states.mapping('fips', 'name')
fips_name['11'] = "District of Columbia"

# Define a function to parse the election data for a specific state FIPS code
def fetch_state_data(fips_code):
    url = f'https://uselectionatlas.org/RESULTS/compare.php?fips={fips_code}&f=1&off=0&elect=0&type=state'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='datatable')
    
    # Initialize an empty list to hold row data
    rows = []
    
    # Check if table exists
    if table:
        for row in table.find_all('tr')[2:]:  # Skipping header rows
            cells = row.find_all('td')
            if len(cells) < 16:
                continue  # Skip incomplete rows
            
            # Extract the relevant fields, reversing colors for D/R columns
            year = cells[2].text.strip()
            total_votes = cells[3].text.strip().replace(',', '')
            dem_votes = cells[13].text.strip().replace(',', '')
            rep_votes = cells[14].text.strip().replace(',', '')
            ind_votes = cells[15].text.strip().replace(',', '')
            other_votes = cells[16].text.strip().replace(',', '')
            dem_pct = cells[9].text.strip().replace('%', '')
            rep_pct = cells[10].text.strip().replace('%', '')
            ind_pct = cells[11].text.strip().replace('%', '')
            other_pct = cells[12].text.strip().replace('%', '')
            
            # Append to rows list as a dictionary
            rows.append({
                'fips': fips_code,
                'year': year,
                'total_votes': int(total_votes) if total_votes.isdigit() else 0,
                'dem_votes': int(dem_votes) if dem_votes.isdigit() else 0,
                'rep_votes': int(rep_votes) if rep_votes.isdigit() else 0,
                'ind_votes': int(ind_votes) if ind_votes.isdigit() else 0,
                'other_votes': int(other_votes) if other_votes.isdigit() else 0,
                'dem_pct': float(dem_pct) if dem_pct else 0,
                'rep_pct': float(rep_pct) if rep_pct else 0,
                'ind_pct': float(ind_pct) if ind_pct else 0,
                'other_pct': float(other_pct) if other_pct else 0,
                'state': state_fips
            })
    return rows

# Initialize an empty list to collect data for each state
all_data = []

# Define the list of FIPS codes including DC (FIPS 11)
fips_to_name = us.states.mapping('fips', 'name')
states = [fips for fips in fips_to_name.keys() if int(fips) <= 56] + ['11']

# Fetch data for each state
for state_fips in states:
    print(f"Fetching data for FIPS {state_fips}")
    state_data = fetch_state_data(state_fips)
    all_data.extend(state_data)


# Convert the list of dictionaries to a DataFrame
election_df = pd.DataFrame(all_data).query('year != "2024"')

election_df['state_name'] = election_df['state'].map(fips_name)

# Optionally, save to a CSV file
election_df.to_csv('data/processed/presidential_election_results_by_state.csv', index=False)
election_df.to_json('data/processed/presidential_election_results_by_state.json', indent=4, orient='records')