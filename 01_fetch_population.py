import os
import requests
import pandas as pd

# Retrieve API key from environment variable
api_key = os.getenv("CENSUS_API_KEY")

# Define Census API endpoints and variables
endpoints = {
    "2000": {
        "url": "https://api.census.gov/data/2000/dec/sf1",
        "variables": "P001001,P004003",  # Total population and White alone, not Hispanic or Latino
        "geography": "county:*",
    },
    "2010": {
        "url": "https://api.census.gov/data/2010/dec/sf1",
        "variables": "P001001,P005003",  # Total population and White alone, not Hispanic or Latino
        "geography": "county:*",
    },
    "2020": {
        "url": "https://api.census.gov/data/2020/dec/pl",
        "variables": "P1_001N,P2_005N",  # Total population and White alone, not Hispanic or Latino
        "geography": "county:*",
    }
}

# Function to fetch data from the Census API
def fetch_census_data(year, endpoint, api_key):
    url = f"{endpoint['url']}?get={endpoint['variables']},NAME&for={endpoint['geography']}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    # Convert to DataFrame
    columns = data[0]
    src = pd.DataFrame(data[1:], columns=columns)
    src.columns = src.columns.str.lower()
    src["year"] = year
    src["fips"] = src["state"] + src["county"]
    src[["place", 'state_name']] = src["name"].str.split(', ', expand=True)
    
    # Rename columns for consistency
    src = src.rename(columns={
        'p1_001n': "population",
        'p001001': "population",
        'p004003': "white_alone",
        'p005003': "white_alone",
        'p2_005n': "white_alone"
    })

    # Calculate White alone percentage
    src["white_alone_pct"] = (src["white_alone"].astype(float) / src["population"].astype(float)) * 100
    
    colsOrder = ['fips', 'place', 'state_name', 'population', 'white_alone', 'white_alone_pct', 'year']
    df = src.drop(['name'], axis=1)[colsOrder].copy()
    return df

# Fetch data for each decennial census
population_data_2000 = fetch_census_data("2000", endpoints["2000"], api_key)
population_data_2010 = fetch_census_data("2010", endpoints["2010"], api_key)
population_data_2020 = fetch_census_data("2020", endpoints["2020"], api_key)

# Save the population data for each decennial year to JSON files
population_data_2000.round(2).to_json("data/processed/county_population_census_2000.json", orient="records", indent=4)
population_data_2010.round(2).to_json("data/processed/county_population_census_2010.json", orient="records", indent=4)
population_data_2020.round(2).to_json("data/processed/county_population_census_2020.json", orient="records", indent=4)

print("Population data including White alone percentage saved to JSON files.")