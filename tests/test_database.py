from database import DataBase

def test_get(): 
    db = DataBase()
    db._data = {"example_key" : "example_value"}
    assert db.get("example_key") == "example_value"


def test_put(): 
    db = DataBase()
    db.put("some_key", "some_value")
    assert db.put("some_key", "some_value") == "some_value"
    assert db._data["some_key"] == "some_value"

def test_all(): 
    db = DataBase()
    dictionary_of_data = {"example_key" : "example_value", "some_key" : "some_value"}
    db._data = dictionary_of_data

    result = db.all()

    assert result == dictionary_of_data

def test_exists(): 
    db = DataBase()
    dictionary_of_data = {"example_key" : "example_value", "some_key" : "some_value"}
    db._data = dictionary_of_data

    assert db.exists("example_key") == True 
    assert db.exists("invalid_key") == False 

def test_delete(): 
    db = DataBase()
    dictionary_of_data = {"example_key" : "example_value", "some_key" : "some_value"}
    db._data = dictionary_of_data

    assert db.delete("example_key") == "example_value"
    assert db.delete("invalid_key") == False 