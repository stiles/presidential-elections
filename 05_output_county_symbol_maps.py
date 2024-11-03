import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np
from matplotlib.lines import Line2D

plt.rcParams["font.family"] = "Roboto"

# Define Albers Equal Area projection
albo = ccrs.AlbersEqualArea(
    central_longitude=-96,
    central_latitude=37.5,
    false_easting=0.0,
    false_northing=0.0,
    standard_parallels=(29.5, 45.5),
)

# Load the election data
election_data = pd.read_json("data/processed/presidential_county_results_with_population.json", dtype={'fips': str}).query('~state_po.isin(["HI","AK"])')

# Load county and state geojson files with only necessary columns
counties_src = gpd.read_file("https://stilesdata.com/gis/usa_counties_demos_generations.geojson").rename(columns={'ID': 'fips'})
counties_src.columns = counties_src.columns.str.lower()
counties_gdf = counties_src[['fips', 'name', 'st_abbrev', 'geometry']].copy()

# Reproject counties and filter out Alaska and Hawaii
counties_gdf = counties_gdf.to_crs(albo.proj4_init).query('~st_abbrev.isin(["AK", "HI"])').copy()
states = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").query('~STATE_NAME.isin(["Hawaii", "Alaska"])').to_crs(albo.proj4_init)

# Merge election data with counties
election_geo = counties_gdf.merge(election_data, left_on='fips', right_on='fips')

# Set min and max radius for symbols
min_radius = 1
max_radius = 500

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

# Loop through election years
years = sorted(election_geo.year.unique())
for year in years:
    election_year_data = election_geo[election_geo['year'] == year].copy()

    # Calculate winner_votes based on party
    election_year_data['winner_votes'] = election_year_data.apply(
        lambda x: x['votes_dem'] if x['winner'] == 'dem' else x['votes_rep'], axis=1
    )

    # Normalize radius based on vote counts
    min_votes = election_year_data['winner_votes'].min()
    max_votes = election_year_data['winner_votes'].max()
    if min_votes != max_votes:
        election_year_data['radius'] = election_year_data['winner_votes'].apply(
            lambda x: min_radius + (max_radius - min_radius) * ((x - min_votes) / (max_votes - min_votes))
        )
    else:
        election_year_data['radius'] = (min_radius + max_radius) / 2

    # Calculate centroids
    centroids = election_year_data.geometry.centroid

    # Define rounded legend thresholds based on the vote range
    vote_range = max_votes - min_votes
    legend_thresholds = [nice_round(min_votes + vote_range * 0.25),
                         nice_round(min_votes + vote_range * 0.5),
                         nice_round(max_votes)]
    legend_sizes = [
        min_radius + (max_radius - min_radius) * ((votes - min_votes) / (max_votes - min_votes))
        for votes in legend_thresholds
    ]

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(15, 10), subplot_kw={'projection': albo})

    # Fill the states with light gray and add boundaries
    counties_gdf.boundary.plot(ax=ax, linewidth=0.05, color='grey')
    states.plot(ax=ax, linewidth=2, edgecolor='white', color='#e9e9e9')

    # Plot proportional symbols at centroids
    ax.scatter(
        centroids.x,
        centroids.y,
        s=election_year_data['radius'],
        color=election_year_data.apply(lambda x: '#c52622' if x['winner'] == 'rep' else '#5194c3', axis=1),
        alpha=0.7,
        transform=albo,
    )

    # Add title
    plt.title(f"Presidential election results in {year}, by county\nLarger circles represent more votes received by the winner",
              fontsize=14, fontweight='bold')

    # Add proportional symbols legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='none', label=f'{format_votes(votes)}', 
               markerfacecolor='none', markeredgecolor='#e6e6e6', markersize=np.sqrt(size))
        for size, votes in zip(legend_sizes, legend_thresholds)
    ]

    # Plot legend with custom sizes and formatted labels
    legend = ax.legend(
        handles=legend_elements,
        frameon=False, labelspacing=1, title="Winner votes",
        loc="lower left", bbox_to_anchor=(0.05, 0.05)
    )
    legend.set_title("Winner votes", prop={'size': 12, 'weight': 'bold'})

    # Remove axes
    plt.axis('off')

    # Save the figure
    plt.savefig(f"visuals/pres_county_symbols_{year}.png", dpi=300, bbox_inches='tight')
    plt.close()