""" Simple class to pack a files manifest"""

import os

class DataBundle():
    def __init__(self, bundle_id):
        self.id = bundle_id
        self.files = []
    
    def add_file(self, file_path):
        self.files.append(file_path)
        
    def add_dir(self, dir_path):
        try:
            self.files = list(map(lambda x: dir_path+'/'+x, os.listdir(dir_path)))
        except IOError as err:
            sys.exit(err)
