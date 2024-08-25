import pandas as pd

# Load the merged election data with population
election_data = pd.read_json("data/processed/presidential_county_results_with_population.json")

# Function to calculate metrics for each election year
def calculate_election_metrics(election_data):
    results = []

    for year in election_data['year'].unique():
        # Filter data for the year
        year_data = election_data[election_data['year'] == year].copy()
        
        # Determine the winning party for each row based on the vote counts
        year_data['winning_party'] = year_data.apply(lambda row: 'R' if row['votes_rep'] > row['votes_dem'] else 'D', axis=1)
        
        # Calculate number of counties by party
        num_r_counties = year_data[year_data['winning_party'] == 'R'].shape[0]
        num_d_counties = year_data[year_data['winning_party'] == 'D'].shape[0]
        total_counties = num_r_counties + num_d_counties
        
        # Share of counties by party
        share_r_counties = num_r_counties / total_counties
        share_d_counties = num_d_counties / total_counties
        
        # Population by party
        pop_r_counties = year_data[year_data['winning_party'] == 'R']['population'].sum()
        pop_d_counties = year_data[year_data['winning_party'] == 'D']['population'].sum()
        total_population = year_data['population'].sum()
        
        # Share of population by party
        share_r_population = pop_r_counties / total_population
        share_d_population = pop_d_counties / total_population
        
        # Percent of population that's white alone in R/D counties
        pct_white_r_counties = (
            year_data[year_data['winning_party'] == 'R']
            .apply(lambda row: row['white_alone_pct'] * row['population'], axis=1)
            .sum() / pop_r_counties
        )
        pct_white_d_counties = (
            year_data[year_data['winning_party'] == 'D']
            .apply(lambda row: row['white_alone_pct'] * row['population'], axis=1)
            .sum() / pop_d_counties
        )

        # Store the results for the year
        results.append({
            "year": year,
            "num_r_counties": num_r_counties,
            "num_d_counties": num_d_counties,
            "share_r_counties": share_r_counties,
            "share_d_counties": share_d_counties,
            "pop_r_counties": pop_r_counties,
            "pop_d_counties": pop_d_counties,
            "share_r_population": share_r_population,
            "share_d_population": share_d_population,
            "pct_white_r_counties": pct_white_r_counties,
            "pct_white_d_counties": pct_white_d_counties,
        })

    return pd.DataFrame(results)

# Calculate the metrics
election_metrics = calculate_election_metrics(election_data)

# Save the results
election_metrics.to_json("data/processed/election_metrics_by_year.json", orient="records", indent=4)

print("Election metrics calculated and saved successfully.")
