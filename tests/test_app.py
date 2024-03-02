from app import app

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200

def test_add_observation(client):
    response = client.get('/add_observation')
    assert response.status_code == 200

def test_plant_identification(client):
    response = client.get('/plant_identification')
    assert response.status_code == 200
