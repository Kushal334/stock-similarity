import json


class StorageAPI():
    store = {}

    def __init__(self, output_file='../data/keystore.json'):
        self.output_file = output_file

    def save(self, key, payload):
        self.store[key] = payload
        with open(self.output_file, 'w') as f:
            json.dump(self.store, f)

    def get(self, key):
        with open(self.output_file, 'r') as f:
            self.store = json.load(f)
        return self.store.get(key, None)


if __name__ == '__main__':
    storage = StorageAPI()
    # storage.save('a', 1)  # test:
    # TODO: run below inside for loop
    print(storage.get('b'))
    print(storage.get('a'))
