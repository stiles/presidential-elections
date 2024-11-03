import us
import math
import requests
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
from matplotlib.lines import Line2D

plt.rc('font', family='Roboto')

# Define Albers Equal Area projection
albo = ccrs.AlbersEqualArea(
    central_longitude=-96,
    central_latitude=37.5,
    false_easting=0.0,
    false_northing=0.0,
    standard_parallels=(29.5, 45.5),
)

# Load state geometries and filter out Hawaii and Alaska
states_gdf = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").rename(columns={'STATE_FIPS': 'fips'})
states_gdf = states_gdf[~states_gdf['STATE_NAME'].isin(["Hawaii", "Alaska"])].copy()
states_gdf['STATE_NAME'] = states_gdf['STATE_NAME'].str.lower()  # Ensure lowercase for merge consistency

# Reproject to Albers Equal Area
states_gdf = states_gdf.to_crs(albo.proj4_init)

election_src = pd.read_json('data/processed/presidential_election_results_by_state.json', dtype={'fips': str, 'year': str})
election_df = election_src.query('year >= "1924" and year != "1970"').copy()

# Prepare election data and ensure lowercase state names
election_df['state_name'] = election_df['state_name'].str.lower()

# Merge election data with state geometries
election_geo = states_gdf.merge(election_df, left_on='fips', right_on='fips', how='inner')

# Set min and max radius for symbols
min_radius = 50
max_radius = 2000

# Loop through each year
years = sorted(election_geo['year'].unique())
for year in years:
    try:
        # Filter data for the current year
        election_year_data = election_geo[election_geo['year'] == f'{year}'].copy()

        # Check if data exists for the year
        if election_year_data.empty:
            print(f"No data available for year {year}, skipping...")
            continue

        # Calculate winner_votes and winner
        election_year_data['winner_votes'] = election_year_data.apply(
            lambda x: x['dem_votes'] if x['dem_pct'] > x['rep_pct'] else x['rep_votes'], axis=1
        )
        election_year_data['winner'] = election_year_data.apply(
            lambda x: 'dem' if x['dem_pct'] > x['rep_pct'] else 'rep', axis=1
        )

        # Normalize the radius
        min_votes = election_year_data['winner_votes'].min()
        max_votes = election_year_data['winner_votes'].max()
        if min_votes != max_votes:
            election_year_data['radius'] = election_year_data['winner_votes'].apply(
                lambda x: min_radius + (max_radius - min_radius) * ((x - min_votes) / (max_votes - min_votes))
            )
        else:
            election_year_data['radius'] = (min_radius + max_radius) / 2

        # Filter out invalid geometries
        election_year_data = election_year_data[election_year_data.geometry.notnull()]

        # Calculate centroids after projection
        centroids = election_year_data.geometry.centroid.to_crs(albo.proj4_init)

        # Dynamically define thresholds for the legend based on vote range
        vote_range = max_votes - min_votes
        legend_thresholds = [min_votes + vote_range * 0.1, min_votes + vote_range * 0.5, max_votes]
        legend_sizes = [
            min_radius + (max_radius - min_radius) * ((votes - min_votes) / (max_votes - min_votes))
            for votes in legend_thresholds
        ]

        # Plotting
        fig, ax = plt.subplots(1, 1, figsize=(15, 10), subplot_kw={'projection': albo})

        # Fill the states with a light color and outline each state
        states_gdf.plot(ax=ax, linewidth=0.5, edgecolor='white', color='#e9e9e9')

        # Plot proportional symbols at centroids
        ax.scatter(
            centroids.x,
            centroids.y,
            s=election_year_data['radius'],
            color=election_year_data.apply(lambda x: '#5194c3' if x['winner'] == 'dem' else '#c52622', axis=1),
            alpha=.7,
            transform=albo,
        )

        # Add title
        plt.title(f"Presidential election results by state: {year}\nLarger circles represent more votes received by the winner",
                  fontsize=14, fontweight='bold', fontname='Roboto')
        plt.axis('off')

        # Helper function to format numbers
        def format_votes(votes):
            if votes >= 1_000_000:
                return f'{votes / 1_000_000:.0f}M'  # Format as "5M"
            elif votes >= 1_000:
                return f'{votes / 1_000:.0f}k'       # Format as "500k"
            else:
                return str(votes)
            
        
        # Helper function to round values to nice intervals (like 100k, 1M)
        def nice_round(value):
            if value >= 1_000_000:
                return round(value / 1_000_000) * 1_000_000
            elif value >= 100_000:
                return round(value / 100_000) * 100_000
            elif value >= 10_000:
                return round(value / 10_000) * 10_000
            else:
                return round(value, -3)

        # Dynamically define rounded thresholds for the legend based on vote range
        vote_range = max_votes - min_votes
        legend_thresholds = [nice_round(min_votes + vote_range * 0.25),
                            nice_round(min_votes + vote_range * 0.5),
                            nice_round(max_votes)]
        legend_sizes = [
            min_radius + (max_radius - min_radius) * ((votes - min_votes) / (max_votes - min_votes))
            for votes in legend_thresholds
        ]

        # Add proportional symbols legend using Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='none', label=f'{format_votes(votes)}', 
                   markerfacecolor='none', markeredgecolor='#e6e6e6', markersize=np.sqrt(size))
            for size, votes in zip(legend_sizes, legend_thresholds)
        ]

        # Plot legend with custom sizes and formatted labels
        legend = ax.legend(
            handles=legend_elements,
            frameon=False, labelspacing=1, title="Winner votes",
            loc="lower left", bbox_to_anchor=(0.05, 0.05)  # Adjust padding with `bbox_to_anchor`
        )
        legend.set_title("Winner votes", prop={'size': 12, 'weight': 'bold'})

        # Save the figure
        plt.savefig(f"visuals/pres_state_symbols_{year}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    except Exception as e:
        print(f"Error processing year {year}: {e}")