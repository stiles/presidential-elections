import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import radians, cos, sin
from matplotlib.patches import FancyArrowPatch

plt.rc('font', family='Roboto')

albers_epsg = "EPSG:5070"  # CONUS Albers Equal Area

# Load county-level results and compute 2020→2024 change
results = pd.read_json("data/processed/presidential_county_results_with_population.json", dtype={'fips': str})
results['year'] = results['year'].astype(str)

cols = ['fips', 'dem_pct', 'rep_pct']
df20 = results.query('year == "2020"')[cols].rename(columns={
    'dem_pct': 'dem_pct_2020',
    'rep_pct': 'rep_pct_2020'
})
df24 = results.query('year == "2024"')[cols].rename(columns={
    'dem_pct': 'dem_pct_2024',
    'rep_pct': 'rep_pct_2024'
})

change_data = df20.merge(df24, on='fips', how='inner')
change_data['margin_2020'] = change_data['rep_pct_2020'] - change_data['dem_pct_2020']
change_data['margin_2024'] = change_data['rep_pct_2024'] - change_data['dem_pct_2024']
change_data['margin_diff'] = change_data['margin_2024'] - change_data['margin_2020']

# Load county geojson with limited columns and reproject to Albers
counties_src = gpd.read_file("https://stilesdata.com/gis/usa_counties_demos_generations.geojson")
counties_src = counties_src.rename(columns={'ID': 'fips', 'ST_ABBREV': 'st_abbrev', 'NAME': 'name'})
counties_src = counties_src[['fips', 'name', 'st_abbrev', 'geometry']]
counties_gdf = counties_src.to_crs(albers_epsg).query('~st_abbrev.isin(["AK", "HI"])').copy()

states_gdf = gpd.read_file("https://stilesdata.com/gis/usa_states_esri_simple.json").query('~STATE_NAME.isin(["Hawaii", "Alaska"])').to_crs(albers_epsg)

# Merge change data with county geometries
change_geo = counties_gdf.merge(change_data, on='fips')

# Define the symbol size parameters
min_symbol_size = 1
max_symbol_size = 30
scaling_factor = 500

# Calculate symbol sizes based on `dem_pct_diff`
min_diff = change_geo['margin_diff'].abs().min()
max_diff = change_geo['margin_diff'].abs().max()

if min_diff != max_diff:
    change_geo['symbol_size'] = change_geo['margin_diff'].abs().apply(
        lambda x: min_symbol_size + (max_symbol_size - min_symbol_size) * (x - min_diff) / (max_diff - min_diff)
    )
else:
    change_geo['symbol_size'] = (min_symbol_size + max_symbol_size) / 2

# Determine color and angle for party shifts
change_geo['color'] = change_geo['margin_diff'].apply(lambda x: '#5194c3' if x < 0 else '#c52622')
change_geo['angle'] = change_geo['margin_diff'].apply(lambda x: radians(135) if x < 0 else radians(45))

# Plotting
fig, ax = plt.subplots(1, 1, figsize=(15, 10))

# Fill counties with a light color and add state boundaries
counties_gdf.plot(ax=ax, linewidth=0.2, edgecolor='#d1f1d1', color='#e9e9e9')
states_gdf.plot(ax=ax, linewidth=1, edgecolor='white', facecolor='none')

# Calculate centroids for symbol plotting
centroids = change_geo.geometry.centroid
x = centroids.x.values
y = centroids.y.values
dx = change_geo['symbol_size'] * np.cos(change_geo['angle'])
dy = change_geo['symbol_size'] * np.sin(change_geo['angle'])
colors = change_geo['color'].values

# Plot arrows using quiver
quiver = ax.quiver(x, y, dx, dy, color=colors, scale=scaling_factor, headwidth=3, headlength=4, headaxislength=3, minlength=0.1)

# Add title
plt.title("County-level shift in presidential vote share, 2020 to 2024\nArrows indicate shift direction; larger symbols represent greater shifts",
          fontsize=14, fontweight='bold')
plt.axis('off')

# Custom legend positioned on the map
legend_ax = fig.add_axes([0.25, 0.05, 0.1, 0.1])
legend_ax.set_xlim(0, 2)
legend_ax.set_ylim(0, 2)
legend_ax.axis('off')

# Define custom arrow properties with equal lengths and adjusted thickness
arrow_props_republican = dict(arrowstyle="-|>", color="#c52622", linewidth=2, mutation_scale=15)
arrow_props_democrat = dict(arrowstyle="-|>", color="#5194c3", linewidth=2, mutation_scale=15)

# Add arrows and labels in the legend axes
legend_ax.add_patch(FancyArrowPatch((0.3, 0.5), (0.1, 1), **arrow_props_democrat))  # Democratic arrow at 10:30
legend_ax.add_patch(FancyArrowPatch((1.7, 0.5), (1.9, 1), **arrow_props_republican))  # Republican arrow at 1:30

# Adjust text placement for separation and alignment
legend_ax.text(0.3, 0.3, "More Democratic", color="#666666", fontsize=10, ha="center")
legend_ax.text(1.7, 0.3, "More Republican", color="#666666", fontsize=10, ha="center")

# Save the figure with the integrated legend
plt.savefig("visuals/county_shift_2020_2024.png", dpi=300, bbox_inches='tight')
plt.close(fig)