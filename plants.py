"""
plants.py: Cleaning observation plant file and 
joining it to Chicago Park District shapefile 
records to match observations to a park

Here is the link to the data saved the Google drive: 
https://drive.google.com/drive/folders/1wXRpBrXa_bwbDfVvb9VoPr39w32aRdzT?usp=sharing

"""

__author__ = "Kira Fujibayashi"
__email__ = "kirafujibayashi@gmail.com"

#import modules 
import pandas as pd 
import numpy as np 
import geopandas as gpd 

from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.wkt import loads
from pyinaturalist import *

from pydantic import BaseModel

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

class plant_observation(): 
    '''
        taxon_id: str 
        common_name: str
        scientific_name: str
        iconic_taxon_name: str
        park_name: str
        park_no: str
        observed_date: date
    '''

    def __init__(self, taxon_id, common_name, scientific_name, iconic_tax_name, park_name, park_no, observed_date): 
        pass 

# declare global variable for file path 
file_path = '/Users/kirafujibayashi/final-project-kirafujibayashi/data/plant_observations/Chicago_Plant_Observations.csv'
file_path_shapefile = '/Users/kirafujibayashi/final-project-kirafujibayashi/data/chicago_parks_meta_data/'

# Load Observation Records 
def load_obs(file=file_path): 
    '''
    Read in CSV file and return DataFrame

    Input: csv file of observations 

    Output: DataFrame
    '''
    df_observations = pd.read_csv(file, low_memory=False)
    return df_observations

# Load Chicago Park shapefile
def load_shapefile(file=file_path_shapefile): 
    '''
    Read in shapefile and return geoDataFrame

    Input: Chicago Open Data Portal Parks Shapefile

    Output: Geo DataFrame 
    '''
    gdf = gpd.read_file(file)\
            .sort_values(by="label") 
    return gdf

def clean_plant_data(df_observations, gdf): 
    '''
    Give the file path to the plant data, 
    load the observation records and match them to parks 
    within the City of Chicago Data Open Data Park shapefile. 

    Input: 
    - Plant Observation Data for Chicago from iNaturalist
    - Chicago Open Data Portal Parks Shapefile

    Output: 
    - DataFrame of plants observed in Chicagoland parks 
    
    '''

    # Filter for plants && clean the data to remove irregular place_guess entries (i.e., non-english records)
    plants_df = df_observations[(df_observations['iconic_taxon_name'] == 'Plantae') &
                                (df_observations['place_guess'].str.contains('^[A-Za-z0-9, .-]*$', na=False)) &
                                (df_observations['observed_on'].notnull())]
    
    def match_plants_to_parks(plants_df, gdf):
        # Convert plant_counts DataFrame to a GeoDataFrame
        gdf_plants = gpd.GeoDataFrame(plants_df, geometry=gpd.points_from_xy(plants_df.longitude, plants_df.latitude))

        # Set the coordinate reference system (CRS) to match the parks GeoDataFrame
        gdf_plants.set_crs(gdf.crs, inplace=True)

        # Perform a spatial join to match plant observations to parks
        joined = gpd.sjoin(gdf_plants, gdf, how='left', predicate='intersects')

        # Rename the 'label' column to 'park_name' for clarity
        joined.rename(columns={'label': 'park_name'}, inplace=True)

        # Filter the joined DataFrame to include only observations within parks
        plants_in_parks = joined[joined['park_name'].notnull()][['place_guess', 'latitude', 'longitude', 'scientific_name', 
                                                                 'common_name', 'iconic_taxon_name', 'taxon_id',
                                                                 'observed_on', 'park_name', 'park', 'park_class', 'park_no', 'image_url']]

        return plants_in_parks

    # Apply the function to match plant observations to parks
    matched_plants = match_plants_to_parks(plants_df, gdf)

    # Filter the DataFrame to include only observations within parks
    plants_in_parks = matched_plants[matched_plants['park_name'].notnull()]

    # Clean the observed date -- add two columns for month/year and year
    # Convert the date column to datetime format
    plants_in_parks['observed_on'] = pd.to_datetime(plants_in_parks['observed_on'])

    # Create a new column for month-year
    plants_in_parks['month_year'] = plants_in_parks['observed_on'].dt.to_period('M')

    # Create a new column for year
    plants_in_parks['year'] = plants_in_parks['observed_on'].dt.year

    return plants_in_parks 

def aggregate_plants(df):
    '''
    Aggregate the plant observations to concenate the observation dates 
    and identify the most recently submitted images 
    '''
    # Sort the results by observation date in descending order
    df_sorted = df.sort_values(['observed_on'], ascending=[False])

    # Group by the specified columns and aggregate
    plant_counts = df_sorted.groupby(['park_name', 'park_no', 'scientific_name', 'common_name', 'iconic_taxon_name', 'taxon_id']) \
                    .agg(observation_count=('observed_on', 'size'), 
                         observed_dates=('month_year', lambda x: ', '.join(sorted(x.astype(str)))), 
                         observed_dates_distinct=('month_year', lambda x: ', '.join(sorted(x.unique().astype(str)))),
                         most_image_url=('image_url', 'first')) \
                    .reset_index()

    # Display the first few rows of the DataFrame
    return plant_counts

def plot_observations(df, park_name): 
    '''
    Given the list of plants observed at the selected park, 
    create a histogram of observation dates (month-year) 

    Input: Park observation records and a specific park name

    Output: Histogram paths
    '''
    histograms= []

    filtered_df = df[df['park_name'] == park_name]

    # Iterate through each distinct plant
    for name, group in filtered_df.groupby('scientific_name'):
        # Convert observed dates into a list and then into a pandas Series
        observed_dates_series = pd.Series(','.join(group['observed_dates']).split(', '))

        # Count the number of observations per month-year
        obs_counts = observed_dates_series.value_counts().sort_index()

        # Only plot the histogram if the observation count is greater than or equal to 30
        if group['observation_count'].sum() >= 100:

            # Plot the histogram
            plt.figure()
            plt.bar(obs_counts.index, obs_counts.values)
            plt.xlabel('Month-Year')
            plt.ylabel('Observation Count')
            plt.title(f'Histogram of {name} Observations by Month')
            
            # plot every fourth month-year record for ease of reading
            xticks = obs_counts.index[::4]
            plt.xticks(ticks=xticks, labels=xticks, rotation=45)

            # Create the folder if it doesn't exist
            folder_path = os.path.join('static', 'images', park_name.replace(" ", "_"))
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Save the histogram as an image file
            file_name = f'histogram_{name.replace(" ", "_")}.png'
            file_path = os.path.join(folder_path, file_name)
            plt.savefig(file_path, bbox_inches='tight')

            # Add the histogram URL to the data structure
            histograms.append({
                'scientific_name': name,
                'histogram_url': f'/static/images/{park_name.replace(" ", "_")}/{file_name}'
            })

            # Clear the current figure
            plt.clf()

        else: 
            continue

    return histograms

if __name__ == "__main__": 
    gdf = load_shapefile() 
    df_observations = load_obs()
    plants_data = clean_plant_data(df_observations=df_observations, gdf=gdf)
    print(plants_data[['observed_on']])
    plant_aggregate = aggregate_plants(plants_data)

    # Get unique values from the 'park_name' column to loop through and create histograms 
    park_list = plants_data['park_name'].unique()
    for name in park_list: 
        plot_observations(plant_aggregate, name)

