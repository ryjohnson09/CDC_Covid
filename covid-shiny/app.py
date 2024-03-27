from shiny import App, render, ui
import numpy as np
import matplotlib.pyplot as plt
import duckdb
import pandas as pd
import json
import geopandas as gpd
import matplotlib
from datetime import date

app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_slider("date", "Date", date(2020, 1, 23), 
                date(2023, 3, 10), date(2020, 3, 2)),
        ),
        ui.panel_main(
            ui.output_plot("map"),
        ),
    ),
)


def server(input, output, session):

    # Connect to the DuckDB database
    conn = duckdb.connect(database="/data/duckdb/database/demo-datasets.db", read_only=False)

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Execute a query to select data from the table
    cursor.execute("SELECT * FROM covid")

    # Fetch the results into a pandas DataFrame
    df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    # Convert to date
    df['date'] = pd.to_datetime(df['date'])

    @render.plot
    def map():
        # Specify the specific date to filter for
        specific_date = input.date()

        # Filter the DataFrame for the specific date
        filtered_df = df[df['date'] == format(input.date(), "%Y-%m-%d")]

        # Add 1 to all values (for log transforming)
        filtered_df['new_cases1'] = filtered_df.new_cases + 1

        # Transform to json
        data_dict = filtered_df.set_index('province_state')['new_cases1'].to_dict()

        # Convert the dictionary to JSON format
        state_values = {province_state: new_cases1 for province_state, new_cases1 in data_dict.items()}
        
        # Load the US States shapefile
        map_df = gpd.read_file("cb_2018_us_state_20m.shp")

        # Filter out OCONUS state/povinces
        map_df = map_df[~map_df['STUSPS'].isin(['AK', 'HI'])]

        # Merge the numerical values with the shapefile
        map_df['value'] = map_df['NAME'].map(state_values)


        # Plotting
        fig, ax = plt.subplots(1, 1, figsize=(15, 10))
        map_df.plot(column='value', 
                    cmap='OrRd', 
                    linewidth=0.8, 
                    ax=ax, edgecolor='0.8', 
                    legend=True, 
                    norm=matplotlib.colors.LogNorm(vmin=1, 
                                                   vmax=df.new_cases.max()))


        # Remove the box around the plot
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.axis('off')

        plt.title('New Covid Cases')

        # Set the size of the current figure
        plt.gcf().set_size_inches(7, 5)


app = App(app_ui, server)
