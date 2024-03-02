"""
tools.py: A collection of helper functions for 
- Collect plant observations from the inaturalist API to be loaded into the database.py 
- Creating a leaflet map to visualize all Chicago Parkland 

Here is some information on the inaturalist API: 
"""

__author__ = "Kira Fujibayashi"
__email__ = "kirafujibayashi@gmail.com"

#import modules 
import requests
import json
import pandas as pd 
import numpy as np 
import geopandas as gpd 
from plants import *

from shapely.geometry import shape, point, Polygon, MultiPolygon
from shapely.wkt import loads
from pyinaturalist import *

def allowed_file(filename):
    ''' 
    Define a function to validate the file type of user input images 
    when saving their own observations 
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def create_map_geojson():
    '''
    Given the Chicago Park District Shape File and our observation data, 
    create GeoJSON record for the park. 

    '''
    # Load Chicago Park District Shapefile
    gdf = load_shapefile()

    # Load Plant Observation File 
    df_observations = load_obs()

    # Create Observations per Chicago Park
    park_observations = clean_plant_data(df_observations, gdf) 

    # Create aggregate observations per Chicago Park
    agg_park_observations = aggregate_plants(park_observations)

    # Sort the GeoDataFrame by park name column = "label"
    gdf = gdf.sort_values(by="label") 

    # Create a list to hold GeoJSON features
    features = []

    # Iterate over the rows in your GeoDataFrame and add polygons for each park
    for index, row in gdf.iterrows():
        # Convert the geometry to GeoJSON format
        geometry_geojson = row["geometry"].__geo_interface__

        # Create a properties dictionary for the park
        properties = {
            "label": row["label"],
            "park_class": row["park_class"],
            "park_no": row["park_no"],
            "nature_bird": row["nature_bir"],
            "nature_center": row["nature_cen"],
            "conservatory": row["conservato"],
            "wetland_ar": row["wetland_ar"],
            "lagoon": row["lagoon"], 
            "wheelchr_a": row["wheelchr_a"]
        }

        # Filter the observations for the current park
        park_obs = agg_park_observations[agg_park_observations['park_no'] == row['park_no']]\
                    .sort_values(by="observation_count", ascending=False) 
        
        park_name = row["label"]

        # Create a list of observation properties
        observation_record = []
        for _, obs_row in park_obs.iterrows():
            name = obs_row['scientific_name']# Construct the histogram file path
            histogram_file_name = f'histogram_{name.replace(" ", "_")}.png'
            histogram_file_path = os.path.join('static', 'images', park_name.replace(" ", "_"), histogram_file_name)

            if obs_row['observation_count'] >= 30 and os.path.exists(histogram_file_path):
                histogram_url = f'/static/images/{park_name.replace(" ", "_")}/{histogram_file_name}'
            else:
                histogram_url = None

            obs_properties = {
                'taxon_id': obs_row['taxon_id'],
                'iconic_taxon_name': obs_row['iconic_taxon_name'],
                'scientific_name': obs_row['scientific_name'],
                'common_name': obs_row['common_name'],
                'observation_count': obs_row['observation_count'],
                'observed_dates': obs_row['observed_dates'],
                'image_url': obs_row['most_image_url'],
                'histogram_url': histogram_url
            }
            observation_record.append(obs_properties)

        # Create a GeoJSON feature for the park
        feature = {
            "type": "Feature",
            "geometry": geometry_geojson, # geometry for mapping 
            "properties": properties, # Add park wildlife and natural features 
            "id": index,  # Add a unique identifier for the park
            "observations": observation_record  # Add the observations for the park
        }

        # Add the feature to the list
        features.append(feature)

    # Create a GeoJSON FeatureCollection from the features list
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    # Return the GeoJSON FeatureCollection
    return json.dumps(feature_collection)
