import us
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from cartopy import crs as ccrs
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.font_manager as fm

# Set Roboto as the default font
plt.rcParams["font.family"] = "Roboto"

# Read counties and party change dataframe
county_results_src = pd.read_json('data/processed/presidential_county_results_with_population.json', dtype={'fips': str})

# Filter for CONUS
county_results_df = county_results_src.query('~state_po.isin(["HI","AK"])').copy()

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
counties_gdf = counties_gdf.to_crs(albo.proj4_init)
states = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").query(
    '~STATE_NAME.isin(["Hawaii", "Alaska"])').to_crs(albo.proj4_init)

# Define the desired breaks and corresponding colors for both parties
common_breaks = [0.50, 0.55, 0.60, 0.65, 0.70, 1.0]  # Adjusted to align labels correctly
rep_ramp = ["#ffd3c3", "#f89a8b", "#E6655A", "#c52622", "#9a040b", "#670000"]
dem_ramp = ["#BBE6F8", "#8CC8F6", "#5194C3", "#166296", "#01446D", "#042853"]

# Create custom colormaps
blues_cmap = ListedColormap(dem_ramp)
reds_cmap = ListedColormap(rep_ramp)

years = sorted(county_results_df.year.unique())

# Loop through each year to generate and save maps
for year in years:
    df = county_results_df.query(f'year == {year}')

    # Merge with geography
    gdf = counties_gdf.merge(df, on='fips')

    # Initialize plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Plot Democratic wins
    gdf_dem = gdf.query('winner == "dem"')
    gdf_dem.plot(
        ax=ax,
        column="dem_pct",
        cmap=blues_cmap,
        linewidth=0.1,
        edgecolor='white',
        scheme="User_Defined",
        classification_kwds=dict(bins=common_breaks),
        legend=False
    )

    # Plot Republican wins
    gdf_rep = gdf.query('winner == "rep"')
    gdf_rep.plot(
        ax=ax,
        column="rep_pct",
        cmap=reds_cmap,
        linewidth=0.1,
        edgecolor='white',
        scheme="User_Defined",
        classification_kwds=dict(bins=common_breaks),
        legend=False
    )

    # Plot state boundaries
    states.boundary.plot(ax=ax, linewidth=0.5, color="black")

    # Customize axes
    ax.set_title(f'Presidential Election Results by County - {year}', fontsize=15)
    ax.axis("off")

    # Adjust colorbars to be narrower, centered relative to the map, and reduce space
    cbar_width = 0.25  # Narrower width to avoid bumping
    cbar_spacing = 0.05  # Spacing between the colorbars
    cbar_bottom = -0.05  # Move the colorbars closer to the map

    # Center positions with spacing
    cbar_ax = fig.add_axes([0.25, cbar_bottom, cbar_width, 0.02])  # Republican colorbar position
    cbar_ax2 = fig.add_axes([0.55, cbar_bottom, cbar_width, 0.02])  # Democratic colorbar position

    tickBreaks=[0.50, 0.55, 0.60, 0.65, 0.70]
    tickLabels=['50%', '55%', '60%', '65%', '70%+']

    # Republican colorbar
    cbar = fig.colorbar(
        plt.cm.ScalarMappable(cmap=reds_cmap, norm=BoundaryNorm(common_breaks, reds_cmap.N)),
        cax=cbar_ax, orientation='horizontal', ticks=tickBreaks
    )
    cbar.set_label('Republican %', fontsize=10)
    cbar.ax.set_xticklabels(tickLabels, fontsize=8)

    # Democratic colorbar
    cbar2 = fig.colorbar(
        plt.cm.ScalarMappable(cmap=blues_cmap, norm=BoundaryNorm(common_breaks, blues_cmap.N)),
        cax=cbar_ax2, orientation='horizontal', ticks=tickBreaks
    )
    cbar2.set_label('Democratic %', fontsize=10)
    cbar2.ax.set_xticklabels(tickLabels, fontsize=8)

    # Save the plot
    plt.savefig(f'visuals/presidential_results_{year}.png', bbox_inches='tight')
    plt.close()

    gdf.to_file(f'data/geo/presidential_election_{year}.geojson', driver="GeoJSON")
    states.to_file(f'data/geo/states.geojson', driver="GeoJSON")

print("Maps generated successfully.")
