
# Presidential election results

## Overview

This project collects, analyzes and visualizes U.S. presidential election results by county and state from a variety of sources, including [MIT's election lab](https://electionlab.mit.edu/data) and Dave Leip's [Atlas of US Presidential Elections](https://uselectionatlas.org/RESULTS/).

The project includes scripts to process raw election data, fetch population data from the Census API, merge these datasets and generate various output files for further analysis and visualization, such as this scatter plot that shows the relationship between the political parties and the population characteristics of the places they win:

![](visuals/presidential_pop_scatter_2020.png?raw=true)

## Scripts

- `00_process_results.py`: Processes the raw election results data from MIT and saves it in a structured format.

-  `01_fetch_population.py`: Fetches county-by-county population data from the US Census Bureau's decennial counts in 2000, 2010 and 2020. It uses the bureau's API and requires a key stored in your local environment. 

- `02_apply_population_results.py`: Merges the population data with the election results data.

- `03_output_geofiles_maps.py`: Merges elections results/population data with county-level geography files and outputs GeoJSON files. It also outputs choropleth maps with the results from 2000-2020. 

- `04_analyze_results.py`: Analyzes the merged election and population data, generating metrics like the number of counties won by each party.

- `05_output_county_symbol_maps.py`: Generates proportional symbol maps at the county level for each election year, saving the output as PNG files.

- `06_population_scatter_parties.py`: Generates scatter plots exploring the relationship between the population characteristics of counties won by the parties in each election cycle. This is a very early draft.

- `07_fetch_state_results.py` Collects state-level presidential votes and vote share for major parties candidates from 1924-2020. 

- `08_output_state_symbol_maps.py.py`: Generates proportional symbol maps at the state level for each election year, saving the output as PNG files. 

## Data Files

### 1. Population
County population data for the respective years fetched from the Census API.

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
        "white_alone_pct":25.6,
        "year":"2020"
    },
    {
        "fips":"06083",
        "place":"Santa Barbara County",
        "state_name":"California",
        "population":"448229",
        "white_alone":"184746",
        "white_alone_pct":41.22,
        "year":"2020"
    },
]
```


### 2. Election aggregates
Metrics such as the number of counties won by each party, the share of counties, and population-related statistics.

**Data:** `data/processed/election_metrics_by_year.json`

**Sample:**
*List of dictionaries for each election. File includes the number of counties won by each party; the percentage of all counties in the US won by each party; the population of the counties won by each party; the share of the national population -- not the votes, just the population -- represented in those counties; and the percentage of the population that is "white non-Hispanic" in the counties won by each party.*

```json
    {
        "year":2020,
        "num_r_counties":2596,
        "num_d_counties":558,
        "share_r_counties":0.82,
        "share_d_counties":0.18,
        "pop_r_counties":131721370.0,
        "pop_d_counties":199294337.0,
        "share_r_population":0.4,
        "share_d_population":0.6,
        "pct_white_r_counties":73.31,
        "pct_white_d_counties":47.61
    }
```

### 3. Raw results
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
        "dem_pct":0.71,
        "rep_pct":0.27,
        "winner":"dem"
    },
```

Election results data by state for the years 1924 to 2020.

**Data:** `data/processed/presidential_election_results_by_state.json`

**Sample:**
*List of dictionaries for each state.*

```json
        {
        "fips":"48",
        "year":"1948",
        "total_votes":1249432,
        "dem_votes":824235,
        "rep_votes":303467,
        "ind_votes":113776,
        "other_votes":7954,
        "dem_pct":65.97,
        "rep_pct":24.29,
        "ind_pct":9.11,
        "other_pct":0.64,
        "state":"48",
        "state_name":"Texas"
    },
```

### 3. County change
Shows changes in voting percentages by county between the 2016 and 2020 presidential elections.

**Data:** `data/processed/presidential_county_change_2016_2020.json`

**Sample:**

```json
    {
        "fips":"42049",
        "county_name":"ERIE",
        "state_po":"PA",
        "dem_pct_2016":46.99,
        "rep_pct_2016":48.57,
        "margin_2016":1.58,
        "winner_2016":"rep",
        "dem_pct_2020":49.81,
        "rep_pct_2020":48.78,
        "margin_2020":-1.03,
        "winner_2020":"dem",
        "dem_pct_diff":2.82,
        "rep_pct_diff":0.21,
        "margin_diff":-2.61,
        "flipped":true
    },
```

### 5. County results with population
Combined county-level election results with population data for the years 2000, 2004, 2008, 2012, 2016, 2020, 2024. Population is mapped to the closest decennial census; 2024 uses 2020.

**Data:** `data/processed/presidential_county_results_with_population.json`

```python
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
```

Note: 2024 county results are deduplicated by FIPS before merging.

**Sample:**
*List of dictionaries for each county.*

```json
    {
        "fips":"06037",
        "county_name":"LOS ANGELES",
        "state_po":"CA",
        "year":"2020",
        "votes_dem":3028885,
        "votes_rep":1145530,
        "votes_all":4264365,
        "dem_pct":0.71,
        "rep_pct":0.27,
        "winner":"dem",
        "population":10014009.0,
        "white_alone":2563609.0,
        "white_alone_pct":25.6
    }
```

## Map sketches

- `visuals/presidential_results_{YEAR}.png`: Choropleth maps for each election year (2000, 2004, 2008, 2012, 2016, 2020). Darker shades represent a greater vote share by the winning party. 

![](visuals/presidential_results_2020.png?raw=true)

- `visuals/pres_county_symbols_{YEAR}.png`: Proportional symbol maps for each election year (2000, 2004, 2008, 2012, 2016, 2020). Larger circles represent more votes, and colors indicate the winning party (red for Republicans, blue for Democrats).

![](visuals/pres_county_symbols_2020.png?raw=true)

- `visuals/pres_state_symbols_{YEAR}.png`: Proportional symbol maps for each election year (1924-2020). Larger circles represent the winning party's vote total, and the colors indicate the winning party (red for Republicans, blue for Democrats).

![](visuals/pres_state_symbols_2020.png?raw=true)

- `visuals/county_shift_2016_2020.png`: A symbol map with arrows representing a presidential vote margin shift from 2016 to 2020. Arrows moving to the right show a shift towards the Republicans and those moving to the left indicate a change towards the Democrats. The colors represent the direction of the shift, not the winner. 

![](visuals/county_shift_2016_2020.png?raw=true)