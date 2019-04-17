""" Base module to handle remote tasks """

import os
import base64

class Task():
    """ Classe to handle task execution """
    def __init__(self, name, description):
        self.id = base64.b64encode(os.urandom(8).decode('ascii'))
        self.remote_id = ''
        self.name = name
        self.description = description
        self.ssh_data = sshCredentials()
        self.script=''
        
    def launch(self, credentials_path)
        self.ssh_data.load_from_file(credentials_path)
        
    
