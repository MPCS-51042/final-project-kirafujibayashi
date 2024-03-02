class DataBase:

    def __init__(self):
        self._data = {}
        self.observations = []

    def add_observation(self, observation):
        self.observations.append(observation)

    def get_observations(self):
        return self.observations

    def delete_observation(self, key):
        if key in self._data:
            delete_val = self._data[key]
            del self._data[key]
            return delete_val
        return False
