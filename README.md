
# Presidential election results

## Overview

This project analyzes and visualizes U.S. presidential election results by county, focusing on the years 2000, 2004, 2008, 2012, 2016, and 2020. 

The project includes scripts to process raw election data, fetch population data from the Census API, merge these datasets and generate various output files for further analysis and visualization.

## Data Files

### Population
Population data for the respective years fetched from the Census API.

**Data:**
- `data/processed/county_population_census_2000.json`
- `data/processed/county_population_census_2010.json`
- `data/processed/county_population_census_2020.json`

**Sample:** 
*List of dictionaries for each county:*

```json
[
    {
        "fips":"06037",
        "place":"Los Angeles County",
        "state_name":"California",
        "population":"10014009",
        "white_alone":"2563609",
        "white_alone_pct":25.6002266425,
        "year":"2020"
    },
    {
        "fips":"06083",
        "place":"Santa Barbara County",
        "state_name":"California",
        "population":"448229",
        "white_alone":"184746",
        "white_alone_pct":41.2168779798,
        "year":"2020"
    },
]
```


### Election aggregates
Metrics such as the number of counties won by each party, the share of counties, and population-related statistics.

**Data:** `data/processed/election_metrics_by_year.json`

**Sample:**
*List of dictionaries for each election. File includes the number of counties won by each party; the percentage of all counties in the US won by each party; the population of the counties won by each party; the share of the national population -- not the votes, just the population -- represented in those counties; and the percentage of the population that is "white non-Hispanic" in the counties won by each party.*

```json
    {
        "year":2020,
        "num_r_counties":2596,
        "num_d_counties":558,
        "share_r_counties":0.8230818009,
        "share_d_counties":0.1769181991,
        "pop_r_counties":131721370.0,
        "pop_d_counties":199294337.0,
        "share_r_population":0.3979308752,
        "share_d_population":0.6020691248,
        "pct_white_r_counties":73.3057756687,
        "pct_white_d_counties":47.6064530624
    }
```

#### County change
Shows changes in voting percentages by county between the 2000 and 2020 presidential elections.

**Data:** `data/processed/presidential_county_change_2000_2020.json`

**Sample:**

```json
    {
        "fips":"48113",
        "county_name":"DALLAS",
        "state_po":"TX",
        "dem_pct_2000":0.4490872522,
        "rep_pct_2000":0.525814834,
        "dem_pct_2020":0.6509770485,
        "rep_pct_2020":0.333958308,
        "dem_pct_diff":0.2018897963,
        "rep_pct_diff":-0.191856526
    },
```

#### Raw results
Election results data by county for the years 2000, 2004, 2008, 2012, 2016, 2020.

**Data:** `data/processed/presidential_county_results.json`

**Sample:**
*List of dictionaries for each county.*

```json
    {
        "fips":"06037",
        "county_name":"LOS ANGELES",
        "state_po":"CA",
        "year":"2020",
        "votes_dem":3028885.0,
        "votes_rep":1145530.0,
        "votes_all":4264365.0,
        "dem_pct":0.7102780836,
        "rep_pct":0.2686285062,
        "winner":"dem"
    }
```

#### Results with population
Combined election results with population data for the years 2000, 2004, 2008, 2012, 2016, 2020. Data are mapped to the closest Census decade: 

**Data:** `data/processed/presidential_county_results_with_population.json`

```python
# Create a mapping of presidential years to corresponding census data
population_map = {
    "2000": population_data_2000,
    "2004": population_data_2000,
    "2008": population_data_2010,
    "2012": population_data_2010,
    "2016": population_data_2010,
    "2020": population_data_2020
}
```

**Sample:**
*List of dictionaries for each county.*

```json
    {
        "fips":"06037",
        "county_name":"LOS ANGELES",
        "state_po":"CA",
        "year":"2020",
        "votes_dem":3028885.0,
        "votes_rep":1145530.0,
        "votes_all":4264365.0,
        "dem_pct":0.7102780836,
        "rep_pct":0.2686285062,
        "winner":"dem"
    }
```

## Scripts

- `00_process_results.py`: Processes the raw election results data from [MIT's election lab](https://electionlab.mit.edu/data) and saves it in a structured format.

-  `01_fetch_population.py`: Fetches county-by-county population data from the US Census Bureau's decennial counts in 2000, 2010 and 2020. It uses the bureau's API.

- `02_apply_population_results.py`: Merges the population data with the election results data.

- `03_output_geofiles_maps.py`: Merges elections results/population data with county-level geography files and outputs GeoJSON files. It also outputs choropleth maps with the results from 2000-2020. 

- `04_analyze_results.py`: Analyzes the merged election and population data, generating metrics like the number of counties won by each party.

- `05_output_symbol_maps.py`: Generates proportional symbol maps for each election year, saving the output as PNG files.

## Map sketches

- `visuals/pres_county_symbols_{YEAR}.png`: Proportional symbol maps for each election year (2000, 2004, 2008, 2012, 2016, 2020). Larger circles represent more votes, and colors indicate the winning party (red for Republican, blue for Democrat).

![](visuals/pres_county_symbols_2000.png?raw=true)

- `visuals/presidential_results_{YEAR}.png`: Choropleth maps for each election year (2000, 2004, 2008, 2012, 2016, 2020). Darker shades represent a greater vote share by the winning party. 

![](visuals/presidential_results_2000.png?raw=true)