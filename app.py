from flask import Flask, render_template, Blueprint, request, redirect, url_for
import geopandas as gpd
from plants import * 
from tools import * 
from pydantic import BaseModel
from database import DataBase
from typing import Optional
from werkzeug.utils import secure_filename

import base64


app = Flask(__name__)
app.db = DataBase() 

class Observation(BaseModel):
    scientific_name: Optional[str]
    common_name: Optional[str]
    park_name: Optional[str]
    observed_on: Optional[str] 
    image_url: Optional[str]

@app.route("/")
def index():
    # Generate GeoJSON data for the map
    geojson = create_map_geojson()

    # Render the index.html template and pass the GeoJSON data
    return render_template("index.html", geojson=geojson)

@app.route('/add_observation', methods=['GET', 'POST'])
def add_observation():
    # Parse and add user input observations to the DataBase
    observations = app.db.get_observations()
    if request.method == 'POST':
        observation_data = {
            'scientific_name': request.form['scientific_name'],
            'common_name': request.form['common_name'],
            'observed_on': request.form['observed_on'],
            'park_name': request.form['park_name']
        }

        # Handle the uploaded image
        image = request.files.get('observation_image')
        image_dir = os.path.join(app.root_path, 'static/images/observations')
        
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            file_path = os.path.join(image_dir, filename)
            print(f"Saving image to: {file_path}")
            image.save(file_path)
            image_url = url_for('static', filename=f'images/observations/{filename}')
        else:
            print(f"No image uploaded: {image}")
            image_url = None

        observation_data['image_url'] = image_url

        try:
            observation = Observation(**observation_data)
            app.db.add_observation(observation.dict())
            return redirect(url_for('add_observation'))
        
        except Exception as e:
            print(f"Error creating observation: {e}")
            return "Error processing the observation", 400

    return render_template('add_observation.html', observations=observations)

@app.route('/identify_plant', methods=['GET', 'POST'])
def identify_plant():
    # User input a photo for identification
    if request.method == 'POST':
        # Get the file from the user upload form
        file = request.files['plant_photo']
        if file:
            # Prepare the image for the Plant.id API
            images = [base64.b64encode(file.read()).decode('ascii')]
            
            # Call the Plant.id API
            response = requests.post(
                        'https://api.plant.id/v3/identification',
                        params={'details': 'url,common_names,name_authority,wiki_description,taxonomy'},
                        headers={'Api-Key': 'DyW60XtfACbzl41bC5V8Pd6qzesW86ZVW79VA28z6lrK2Ah17B'},
                        json={'images': images},
                    )

            identification = response.json()

            # Process the response and render the results
            return render_template('plant_identification_results.html', plant_info=identification)

    # Render the form for GET requests
    return render_template('identify_plant.html')

@app.route('/plant_identification')
def plant_identification():
    return render_template('identify_plant.html')

if __name__ == '__main__':
    ''' 
    Run the flask app 
    '''
    app.run()


