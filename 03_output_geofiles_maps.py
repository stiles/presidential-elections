import us
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
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

# Reproject to Albers Equal Area for consistency (CONUS Albers: EPSG:5070)
albers_epsg = "EPSG:5070"

# Reproject to Albers
counties_gdf = counties_gdf.to_crs(albers_epsg)
states = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").query(
    '~STATE_NAME.isin(["Hawaii", "Alaska"])').to_crs(albers_epsg)

# Define the desired breaks and corresponding colors for both parties
# Add an 80% bin so the darkest shade is reserved for 80%+ counties
# Note: dem_pct/rep_pct are stored as 0–100 percentages in the data
common_breaks = [50, 55, 60, 65, 70, 80, 100]

# Slightly lighter ramps to avoid overly dark maps
rep_ramp = [
    "#ffe5de",  # <=50%
    "#f8c9bd",  # 50-55%
    "#f49e8e",  # 55-60%
    "#e97061",  # 60-65%
    "#d7493e",  # 65-70%
    "#b92b28",  # 70-80%
    "#8f0f0f"   # 80%+
]
dem_ramp = [
    "#e4f3fb",  # <=50%
    "#c7e6fb",  # 50-55%
    "#9bc8f7",  # 55-60%
    "#6da0d9",  # 60-65%
    "#427ab6",  # 65-70%
    "#215b93",  # 70-80%
    "#0a3f6d"   # 80%+
]

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
    states.boundary.plot(ax=ax, linewidth=0.5, color="white")

    # Customize axes
    ax.axis("off")
    # Figure-level title (left-aligned) and small source line bottom-left
    fig.suptitle(
        f'US presidential election results, by county, in {year}',
        x=0.01, y=0.97, ha='left', va='top', fontsize=15, fontweight='bold'
    )
    fig.text(0.01, 0.02, 'Map: Matt Stiles | Data sources: MIT Election Lab / Dave Leip',
             ha='left', va='bottom', fontsize=9, color='#666666')
    # Tighten left/right margins; add a bit more space below colorbars
    fig.subplots_adjust(top=0.88, bottom=0.08, left=0.01, right=0.99)

    # Place colorbars at the top, under the title
    cbar_width = 0.20
    cbar_y = 0.92
    cbar_ax = fig.add_axes([0.25, cbar_y, cbar_width, 0.015])  # Republican colorbar position
    cbar_ax2 = fig.add_axes([0.60, cbar_y, cbar_width, 0.015])  # Democratic colorbar position

    tickBreaks=[50, 55, 60, 65, 70, 80]
    tickLabels=['50%', '55%', '60%', '65%', '70%', '80%+']

    # Republican colorbar
    cbar = fig.colorbar(
        plt.cm.ScalarMappable(cmap=reds_cmap, norm=BoundaryNorm(common_breaks, reds_cmap.N)),
        cax=cbar_ax, orientation='horizontal', ticks=tickBreaks
    )
    cbar.set_label('Republican %', fontsize=10)
    cbar.ax.set_xticklabels(tickLabels, fontsize=8)
    # Remove colorbar outline and spines
    cbar.outline.set_visible(False)
    for spine in cbar_ax.spines.values():
        spine.set_visible(False)

    # Democratic colorbar
    cbar2 = fig.colorbar(
        plt.cm.ScalarMappable(cmap=blues_cmap, norm=BoundaryNorm(common_breaks, blues_cmap.N)),
        cax=cbar_ax2, orientation='horizontal', ticks=tickBreaks
    )
    cbar2.set_label('Democratic %', fontsize=10)
    cbar2.ax.set_xticklabels(tickLabels, fontsize=8)
    # Remove colorbar outline and spines
    cbar2.outline.set_visible(False)
    for spine in cbar_ax2.spines.values():
        spine.set_visible(False)

    # Remove any default axes margins and save with minimal padding
    ax.margins(0)
    plt.savefig(f'visuals/presidential_results_{year}.png', bbox_inches='tight', pad_inches=0.1)
    plt.close()

    gdf.to_file(f'data/geo/presidential_election_{year}.geojson', driver="GeoJSON")
    states.to_file(f'data/geo/states.geojson', driver="GeoJSON")

print("Maps generated successfully.")
