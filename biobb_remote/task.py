""" Base module to handle remote tasks """

import os
import base64
from ssh_session import sshCredentials, SshSession

class Task():
    """ Classe to handle task execution """
    def __init__(self, name, description):
        self.id = base64.b64encode(os.urandom(8).decode('ascii'))
        self.name = name
        self.description = description
        self.data_bundle = dataBundle()
        
        self.remote_queue_settings = {
            submit_command: '',
            cancel_command: '',
            status_command: ''
        }

        self.ssh_data = sshCredentials()
        
        self.script=''
        self.remote_path = ''
        
    def set_credentials(self, credentials_path):
        self.ssh_data.load_from_file(credentials_path)
        
    def prepare_queue_script(self):
        return self.script
    
    def submit(self, send_data=False):
        if not self.ssh_data:
            print("No credentials")
            return
        ssh = SshSession(ssh_data=self.ssh_data)
        if self.remote_path and send_data and self.data_bundle:
            self.send_input_data()
        if self.script:
            self.remote_script = self.remote_path + "/task_" + self.id + ".sh" 
            ssh.run_sftp('create',self.prepare_queue_script(), self.remote_script)
        (stdin, stdout, stderr) = ssh.run_command(
            self.remote_queue.settings['submit_command'] + ' '\
                + self.self.remote_script) 
        if not stderr:
            return stdout

    def cancel(self):
        pass
    
    def status(self):
        pass
    
    def get_logs(self):
        pass
    
    def send_input_data(self, data):
        pass
    
    def get_output_data(self):
        pass
    
    
        
     
    
