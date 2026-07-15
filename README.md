# Presidential election results

This project collects, analyzes and visualizes U.S. presidential election results by county and state from a variety of sources, including [MIT's election lab](https://electionlab.mit.edu/data) and Dave Leip's [Atlas of US Presidential Elections](https://uselectionatlas.org/RESULTS/).

The scripts process raw election data, fetch population data from the Census API, merge the datasets and generate output files for analysis and visualization, such as this scatter plot showing the relationship between the political parties and the population characteristics of the places they win:

![](visuals/presidential_pop_scatter_2024.png?raw=true)

## Setup

The project requires Python 3.12 or later. Install dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

`01_fetch_population.py` calls the Census Bureau's API and requires a key stored in a `CENSUS_API_KEY` environment variable. You can request a key [here](https://api.census.gov/data/key_signup.html).

## Scripts

Run the scripts in numbered order. Each step reads the outputs of the previous ones.

- `00_fetch_2024.py`: Scrapes 2024 county-level results from Dave Leip's Atlas and saves them to `data/processed/presidential_county_results_2024.json`. Vote shares in this file are 0–1 proportions; the next script converts them to percentages.

- `00_process_results.py`: Processes the raw MIT election results (2000–2020), appends the 2024 scrape and calculates vote shares, margins and winners. Also computes county-level change between 2016 and 2020.

- `01_fetch_population.py`: Fetches county-by-county population data from the Census Bureau's decennial counts in 2000, 2010 and 2020.

- `02_apply_population_results.py`: Merges the population data with the election results, mapping each election year to the closest decennial census.

- `03_output_geofiles_maps.py`: Merges results and population data with county-level geography, outputs GeoJSON files to `data/geo/` and draws choropleth maps for each election from 2000 to 2024.

- `04_analyze_results.py`: Generates yearly metrics such as the number of counties won by each party and the population living in them.

- `05_output_county_symbol_maps.py`: Draws proportional symbol maps at the county level for each election year.

- `06_population_scatter_parties.py`: Draws scatter plots comparing the population characteristics of counties won by each party. This is an early draft.

- `07_fetch_state_results.py`: Scrapes state-level presidential votes and vote share for major party candidates from 1924 to 2020.

- `08_output_state_symbol_maps.py`: Draws proportional symbol maps at the state level for each election year.

- `09_map_county_shift.py`: Draws an arrow map showing the county-level shift in vote margin from 2020 to 2024.

## Data files

Percent fields (`dem_pct`, `rep_pct`) in the processed county and state files use 0–100 percentage points unless noted otherwise. FIPS codes are zero-padded strings.

### County population

County population data fetched from the Census API for each decennial year.

**Data:**
- `data/processed/county_population_census_2000.json`
- `data/processed/county_population_census_2010.json`
- `data/processed/county_population_census_2020.json`

**Sample:**

```json
[
    {
        "fips": "06037",
        "place": "Los Angeles County",
        "state_name": "California",
        "population": "10014009",
        "white_alone": "2563609",
        "white_alone_pct": 25.6,
        "year": "2020"
    }
]
```

### County results

Election results by county for 2000, 2004, 2008, 2012, 2016, 2020 and 2024.

**Data:** `data/processed/presidential_county_results.json`

**Sample:**

```json
[
    {
        "fips": "06037",
        "county_name": "LOS ANGELES",
        "state_po": "CA",
        "year": "2024",
        "votes_dem": 2416879.0,
        "votes_rep": 1191577.0,
        "votes_all": 3747099.0,
        "dem_pct": 64.5,
        "rep_pct": 31.8,
        "margin": -32.7,
        "winner": "dem"
    }
]
```

### County results with population

County results merged with population data. Population is mapped to the closest decennial census: 2000 and 2004 use the 2000 census, 2008 through 2016 use 2010 and 2020 and 2024 use 2020. Results are deduplicated by year and FIPS before merging.

**Data:** `data/processed/presidential_county_results_with_population.json`

**Sample:**

```json
[
    {
        "fips": "06037",
        "county_name": "LOS ANGELES",
        "state_po": "CA",
        "year": "2020",
        "votes_dem": 3028885,
        "votes_rep": 1145530,
        "votes_all": 4264365,
        "dem_pct": 71.0,
        "rep_pct": 27.0,
        "winner": "dem",
        "population": 10014009.0,
        "white_alone": 2563609.0,
        "white_alone_pct": 25.6
    }
]
```

### County change

Changes in voting percentages by county between the 2016 and 2020 elections.

**Data:** `data/processed/presidential_county_change_2016_2020.json`

**Sample:**

```json
[
    {
        "fips": "42049",
        "county_name": "ERIE",
        "state_po": "PA",
        "dem_pct_2016": 46.99,
        "rep_pct_2016": 48.57,
        "margin_2016": 1.58,
        "winner_2016": "rep",
        "dem_pct_2020": 49.81,
        "rep_pct_2020": 48.78,
        "margin_2020": -1.03,
        "winner_2020": "dem",
        "dem_pct_diff": 2.82,
        "rep_pct_diff": 0.21,
        "margin_diff": -2.61,
        "flipped": true
    }
]
```

### Election metrics

Yearly aggregates: the number and share of counties won by each party, the population of those counties, the share of the national population they represent and the percentage of that population that is white non-Hispanic.

**Data:** `data/processed/election_metrics_by_year.json`

**Sample:**

```json
[
    {
        "year": 2024,
        "num_r_counties": 2651,
        "num_d_counties": 436,
        "share_r_counties": 0.86,
        "share_d_counties": 0.14,
        "pop_r_counties": 162294706.0,
        "pop_d_counties": 167763659.0,
        "share_r_population": 0.49,
        "share_d_population": 0.51,
        "pct_white_r_counties": 67.64,
        "pct_white_d_counties": 48.37
    }
]
```

### State results

Election results by state from 1924 to 2020, plus a 2024 file aggregated from the county results.

**Data:**
- `data/processed/presidential_election_results_by_state.json` (also as CSV)
- `data/processed/presidential_election_results_by_state_2024.json`

**Sample:**

```json
[
    {
        "fips": "48",
        "year": "1948",
        "total_votes": 1249432,
        "dem_votes": 824235,
        "rep_votes": 303467,
        "ind_votes": 113776,
        "other_votes": 7954,
        "dem_pct": 65.97,
        "rep_pct": 24.29,
        "ind_pct": 9.11,
        "other_pct": 0.64,
        "state": "48",
        "state_name": "Texas"
    }
]
```

### Geography

`03_output_geofiles_maps.py` writes county results merged with geography to `data/geo/presidential_election_{YEAR}.geojson`, plus a `states.geojson` boundary file. Maps use the CONUS Albers Equal Area projection (EPSG:5070) and exclude Alaska and Hawaii.

## Map sketches

- `visuals/presidential_results_{YEAR}.png`: Choropleth maps for each election year from 2000 to 2024. Darker shades represent a greater vote share by the winning party.

![](visuals/presidential_results_2024.png?raw=true)

- `visuals/pres_county_symbols_{YEAR}.png`: Proportional symbol maps by county for each election year from 2000 to 2024. Larger circles represent more votes, and colors indicate the winning party (red for Republicans, blue for Democrats).

![](visuals/pres_county_symbols_2024.png?raw=true)

- `visuals/pres_state_symbols_{YEAR}.png`: Proportional symbol maps by state for each election year from 1924 to 2024. Larger circles represent the winning party's vote total.

![](visuals/pres_state_symbols_2024.png?raw=true)

- `visuals/county_shift_2020_2024.png`: A symbol map with arrows representing the shift in presidential vote margin from 2020 to 2024. Arrows pointing right show a shift toward the Republicans and arrows pointing left show a shift toward the Democrats. The colors represent the direction of the shift, not the winner.

![](visuals/county_shift_2020_2024.png?raw=true)

## Sources

- County results, 2000–2020: [MIT Election Data and Science Lab](https://electionlab.mit.edu/data) via the [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ)
- County results, 2024, and state results, 1924–2020: Dave Leip's [Atlas of US Presidential Elections](https://uselectionatlas.org/RESULTS/)
- Population: US Census Bureau decennial counts, 2000, 2010 and 2020
