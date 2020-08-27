""" Simple class to pack a files manifest"""

import os
import sys
import json

class DataBundle():
    def __init__(self, bundle_id):
        self.id = bundle_id
        self.files = []

    def add_file(self, file_path):
        if file_path not in self.files:
            self.files.append(file_path)

    def add_dir(self, dir_path):
        try:
            self.files = list(map(lambda x: dir_path+'/'+x, os.listdir(dir_path)))
        except IOError as err:
            sys.exit(err)
    
    def get_file_names(self):
        return [os.path.basename(x) for x in self.files]
    
    def to_json(self):
        return json.dumps(self)