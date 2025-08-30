import pandas as pd
import json
import os

# Load your cleaned election data
with open("data/processed/presidential_county_results.json", "r") as file:
    election_data = pd.read_json(file)

# Optionally append 2024 results if present and not already included in base
path_2024 = "data/processed/presidential_county_results_2024.json"
base_has_2024 = (election_data.get("year").astype(str) == "2024").any() if "year" in election_data.columns else False
if os.path.exists(path_2024) and not base_has_2024:
    election_data_2024 = pd.read_json(path_2024)
    election_data = pd.concat([election_data, election_data_2024], ignore_index=True)

# Ensure 'year' and 'fips' are strings
election_data['year'] = election_data['year'].astype(str)
election_data['fips'] = election_data['fips'].astype(str)

# De-duplicate by (year, fips) to prevent double counting
before_dedup_count = len(election_data)
election_data = election_data.sort_values(["year", "fips"]).drop_duplicates(subset=["year", "fips"], keep="last").reset_index(drop=True)
after_dedup_count = len(election_data)
if after_dedup_count != before_dedup_count:
    print(f"Dropped {before_dedup_count - after_dedup_count} duplicate election rows (by year+fips)")

# Load the population data you previously fetched and saved
population_data_2000 = pd.read_json("data/processed/county_population_census_2000.json")
population_data_2010 = pd.read_json("data/processed/county_population_census_2010.json")
population_data_2020 = pd.read_json("data/processed/county_population_census_2020.json")

# Convert 'fips' and 'year' to strings and 'population' to numeric in population data
for pop_data in [population_data_2000, population_data_2010, population_data_2020]:
    pop_data['fips'] = pop_data['fips'].astype(str)
    pop_data['year'] = pop_data['year'].astype(str)
    pop_data['population'] = pd.to_numeric(pop_data['population'])
    pop_data['white_alone'] = pd.to_numeric(pop_data['white_alone'])
    pop_data['white_alone_pct'] = pd.to_numeric(pop_data['white_alone_pct'])

# Print to verify population data was loaded and types are correct
print(f"Population data 2000: {len(population_data_2000)} records, types:\n{population_data_2000.dtypes}")
print(f"Population data 2010: {len(population_data_2010)} records, types:\n{population_data_2010.dtypes}")
print(f"Population data 2020: {len(population_data_2020)} records, types:\n{population_data_2020.dtypes}")

# Create a mapping of presidential years to corresponding census data
population_map = {
    "2000": population_data_2000,
    "2004": population_data_2000,
    "2008": population_data_2010,
    "2012": population_data_2010,
    "2016": population_data_2010,
    "2020": population_data_2020,
    "2024": population_data_2020
}

# Function to merge population data with election data based on the year
def merge_population(election_data, population_map):
    election_data_with_population = pd.DataFrame()

    for year, pop_data in population_map.items():
        # Filter election data for the current year
        election_year_data = election_data[election_data["year"] == year]
        print(f"Processing year {year}: {len(election_year_data)} election records")

        # Merge with population data on 'fips'
        merged_data = election_year_data.merge(
            pop_data[["fips", "population", "white_alone", "white_alone_pct"]], on="fips", how="left"
        )

        merged_data['fips'] = merged_data['fips'].str.zfill(5)
        print(f"Merged data for year {year}: {len(merged_data)} records")

        # Append to the final DataFrame
        election_data_with_population = pd.concat([election_data_with_population, merged_data], ignore_index=True)

    return election_data_with_population

# Merge population data with election data
election_data_with_population = merge_population(election_data, population_map)

# Print the final result count to verify
print(f"Final merged data count: {len(election_data_with_population)} records")

# Save the final dataset
election_data_with_population.round(2).to_json(
    "data/processed/presidential_county_results_with_population.json", indent=4, orient="records"
)