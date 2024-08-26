import pandas as pd
import altair as alt
import plotly.express as px
import altair_stiles as altstiles

alt.themes.register("stiles", altstiles.theme)
alt.themes.enable("stiles")
alt.data_transformers.disable_max_rows()

# Load the dataset
with open("data/processed/presidential_county_results_with_population.json", "r") as file:
    election_data = pd.read_json(file)

# Convert necessary columns to appropriate data types
election_data['year'] = election_data['year'].astype(str)
election_data['white_alone_pct'] = pd.to_numeric(election_data['white_alone_pct'])

# Loop through each year and save the scatter plot as a PNG
years = sorted(election_data['year'].unique())

for year in years:
    # Filter data for the current year
    year_data = election_data[election_data['year'] == year]

    # Create the scatter plot
    scatter_plot = alt.Chart(year_data).mark_circle().encode(
        x=alt.X('white_alone_pct', title='% White alone population', axis=alt.Axis(tickCount=6)),
        y=alt.Y('population', title='Total population', axis=alt.Axis(format='1s', tickCount=5)),
        color=alt.Color('winner:N', title='Winning party', scale=alt.Scale(domain=['rep', 'dem'], range=['#c52622', '#5194c3'])),
        size=alt.Size('population', title='Population size', scale=alt.Scale(range=[10, 200])),
        tooltip=['county_name', 'state_po', 'year', 'winner', 'population', 'white_alone_pct']
    ).properties(
        width=800,
        height=500,
        title=f'County population vs. % White alone, by winning party and election in {year}'
    ).configure_legend(symbolType='circle')

    # Save the plot as a PNG file
    file_path = f"visuals/presidential_pop_scatter_{year}.png"
    scatter_plot.save(file_path)

print("Scatter plots saved successfully.")
