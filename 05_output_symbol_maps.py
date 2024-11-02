import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

# Load the election data
election_data = pd.read_json("data/processed/presidential_county_results_with_population.json", dtype={'fips': str}).query('~state_po.isin(["HI","AK"])')

# Load county geojson with limited columns and lower case
counties_src = gpd.read_file(
    "https://stilesdata.com/gis/usa_counties_demos_generations.geojson"
).rename(columns={'ID': 'fips'})

counties_src.columns = counties_src.columns.str.lower()

cols_keep = ['fips', 'name', 'st_abbrev', 'geometry']
counties_gdf = counties_src[cols_keep].copy()

# Reproject to Albers Equal Area for consistency
albo = ccrs.AlbersEqualArea(
    central_longitude=-96,
    central_latitude=37.5,
    false_easting=0.0,
    false_northing=0.0,
    standard_parallels=(29.5, 45.5),
    globe=None,
)

# Reproject to Albers
counties_gdf = counties_gdf.to_crs(albo.proj4_init).query('~st_abbrev.isin(["AK", "HI"])').copy()
states = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").query('~STATE_NAME.isin(["Hawaii", "Alaska"])').to_crs(albo.proj4_init)

# Merge election data with counties
election_geo = counties_gdf.merge(election_data, left_on='fips', right_on='fips')

# Loop through election years
years = sorted(election_geo.year.unique())

# Set min and max radius for the symbol sizes
min_radius = 1  # Adjust as needed for visibility
max_radius = 500  # Adjust as needed for prominent counties

for year in years: 
    election_year_data = election_geo[election_geo['year'] == year].copy()

    # Define winner's votes for scaling
    election_year_data['winner_votes'] = election_year_data.apply(
        lambda x: x['votes_dem'] if x['winner'] == 'dem' else x['votes_rep'], axis=1
    )

    # Normalize the radius within the min and max range
    min_votes = election_year_data['winner_votes'].min()
    max_votes = election_year_data['winner_votes'].max()
    
    # Apply min-max scaling for radius calculation
    election_year_data['radius'] = election_year_data['winner_votes'].apply(
        lambda x: min_radius + (max_radius - min_radius) * ((x - min_votes) / (max_votes - min_votes))
    )

    # Calculate centroids for the proportional symbols
    centroids = election_year_data.geometry.centroid

    # Plot the base map
    plt.rcParams["font.family"] = "Roboto"
    
    fig, ax = plt.subplots(1, 1, figsize=(15, 10), subplot_kw={'projection': albo})
    states.boundary.plot(ax=ax, linewidth=0.3, color='grey')
    counties_gdf.boundary.plot(ax=ax, linewidth=.05, color='grey')

    # Plot proportional symbols at centroids
    ax.scatter(
        centroids.x,
        centroids.y,
        s=election_year_data['radius'],
        color=election_year_data.apply(lambda x: '#c52622' if x['winner'] == 'rep' else '#5194c3', axis=1),
        alpha=0.7,
        transform=albo,
    )

    plt.title(f"Presidential election results in {year}, by party and county. Larger circles represent more votes received by the winner.",
          fontsize=14, fontweight='bold')
    plt.axis('off')
    
    # Save the figure
    plt.savefig(f"visuals/pres_county_symbols_{year}.png", dpi=300, bbox_inches='tight')
    plt.close()
