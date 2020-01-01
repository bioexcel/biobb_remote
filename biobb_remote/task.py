""" Base module to handle remote tasks """

import os
import sys
import uuid
import pickle
import json

from biobb_remote.ssh_session import SSHCredentials, SSHSession
from biobb_remote.data_bundle import DataBundle

UNKNOWN = 0
SUBMITTED = 1
RUNNING = 2
CANCELLED = 3
FINISHED = 4

class Task():
    """ Classe to handle task execution """
    def __init__(self):

        self.id = str(uuid.uuid4())
        #self.description = description
        self.ssh_data = SSHCredentials()
        self.task_data = {}
        self.commands = {}
        self.modified = False

    def load_data_from_file(self, file_path, mode='json'):
        """ Loads accumulated task data from external file"""
        #TODO detect file type
        if mode == 'pickle':
            file = open(file_path, 'rb')
            self.task_data = pickle.load(file)
        elif mode == 'json':
            file = open(file_path, 'r')
            self.task_data = json.load(file)
            if 'local_data_bundle'  in self.task_data:
                local_data_bundle = json.loads(self.task_data['local_data_bundle'])
                self.task_data['local_data_bundle'] = DataBundle(local_data_bundle['id'])
                self.task_data['local_data_bundle'].files = local_data_bundle['files']
            if 'output_data_bundle'  in self.task_data:
                output_data_bundle = json.loads(self.task_data['output_data_bundle'])
                self.task_data['output_data_bundle'] = DataBundle(output_data_bundle['id'])
                self.task_data['output_data_bundle'].files = local_data_bundle['files']
        else:
            sys.exit("ERROR: file type ({}) not supported".format(mode))
        self.id = self.task_data['id']

    def set_credentials(self, credentials_path):
        """ Loads ssh credentials from external file"""
        self.ssh_data.load_from_file(credentials_path)

    def set_local_data(self, local_data_path):
        """ Builds local data bundle """
        self.task_data['local_data_bundle'] = DataBundle(self.id)
        self.task_data['local_data_bundle'].add_dir(local_data_path)
        self.task_data['local_data_path'] = local_data_path
        self.modified = True

    def prepare_queue_script(self):
        """ Generates remote script inclunding queue settings"""
        self.task_data['queue_settings']['job'] = self.id
        self.task_data['queue_settings']['stdout'] = 'job.out'
        self.task_data['queue_settings']['stderr'] = 'job.err'
        self.task_data['queue_settings']['working_dir'] = self._remote_wdir()
        scr_lines = ["#!/bin/sh"]
        scr_lines += self.get_queue_settings_string_array()
        for mod in self.task_data['modules']:
            scr_lines.append('module load ' + mod)
        with open(self.task_data['script'], 'r') as scr_file:
            script = '\n'.join(scr_lines) + '\n' + scr_file.read()
        return script
    
    def get_queue_settings_string_array(self):
        """ Generates queue settings to include in script
            Developed in specific queue classes 
        """
        return []

    def submit(self, wait=False):
        """ Submits task """
        if not self.ssh_data:
            print("ERROR: No credentials")
            return
        ssh = SSHSession(ssh_data=self.ssh_data)
        self.task_data['remote_script'] = self._remote_wdir() + '/run_script.sh'
        ssh.run_sftp('create', self.prepare_queue_script(), self.task_data['remote_script'])
        (stdin, stdout, stderr) = ssh.run_command(
            self.commands['submit'] + ' ' + self.task_data['remote_script']
        )
        self.task_data['remote_job_id'] = self.get_submitted_job_id(
            ''.join(stdout)
        )
        self.task_data['status'] = SUBMITTED
        self.modified = True
        
    def get_submitted_job_id(self):
        """ Reports job id after submission, developed in inherited classes """
        return ''

    def cancel(self, remove_data=True):
        """ Cancels running task """
        if not self.ssh_data:
            print("No credentials available")
            return
        if self.task_data['status'] in [SUBMITTED, RUNNING]:
            ssh = SSHSession(ssh_data=self.ssh_data)
            (stdin, stdout, stderr) = ssh.run_command(
                self.commands['cancel'] + ' ' + self.task_data['remote_job_id']
            )
            if remove_data:
                print("Removing remote data")
                ssh.run_command('rm -rf ' + self._remote_wdir())
            self.task_data['status'] = CANCELLED
            self.modified = True
        else:
            print("Job {} not running".format(self.task_data['remote_job_id']))

    def check_queue(self):
        """ Check queue status """
        session = SSHSession(ssh_data=self.ssh_data)
        return session.run_command(self.commands['queue'])

    def check_job(self):
        """ Checks job status """
        session = SSHSession(ssh_data=self.ssh_data)
        return session.run_command(
            self.commands['queue'] \
            + ' -hv --job ' \
            + self.task_data['remote_job_id']
        )

    def get_logs(self):
        """ Get specific queue logs"""
        #TODO
        pass

    def send_input_data(self):
        """ Uploads data to remote working dir """
        session = SSHSession(ssh_data=self.ssh_data)
        if self.task_data['remote_base_path']:
            session.run_command('mkdir ' + self.task_data['remote_base_path'])
            session.run_command('mkdir ' + self._remote_wdir())
        else:
            sys.exit('task_send_data: error: remote base path not provided')
        if self.task_data['local_data_bundle']:
            for file_path in self.task_data['local_data_bundle'].files:
                remote_file_path = self._remote_wdir() + '/' + os.path.basename(file_path)
                session.run_sftp('put', file_path, remote_file_path)
                print("sending_file: {} -> {}".format(file_path, remote_file_path))
        self.task_data['input_data_loaded'] = True
        self.modified = True

    def get_output_data(self, local_data_path='', overwrite=False):
        """ Downloads remote working dir contents to local """
        session = SSHSession(ssh_data=self.ssh_data)

        if not self.task_data['remote_base_path']:
            sys.exit('task_recover_data: error: remote base path not available')

        if not local_data_path:
            if 'output_data_path' in self.task_data:
                local_data_path = self.task_data['output_data_path']
            elif 'local_data_path' in self.task_data:
                local_data_path = self.task_data['local_data_path']
                print("Warning: using input folder")
            else:
                sys.exit("ERROR: Local path for output not provided")

        if not os.path.exists(local_data_path):
            os.mkdir(local_data_path)

        remote_file_list = session.run_sftp('listdir', self._remote_wdir())

        output_data_bundle = DataBundle(self.task_data['id'] + '_output')

        local_file_names = os.listdir(local_data_path)

        for file in remote_file_list:
            if overwrite or (file not in local_file_names):
                output_data_bundle.add_file(file)

        for file in output_data_bundle.files:
            local_file_path = local_data_path + '/' + file
            remote_file_path = self._remote_wdir() + '/' + file
            session.run_sftp('get', remote_file_path, local_file_path)
            print("getting_file: {} -> {}".format(remote_file_path, local_file_path))

        self.task_data['output_data_bundle'] = output_data_bundle
        self.task_data['output_data_path'] = local_data_path
        self.modified = True

    def save(self, save_file_path, mode='json'):
        """ Saves task data in external file """
        self.task_data['id'] = self.id
        if mode == 'json':
            if 'local_data_bundle'  in self.task_data:
                local_data_bundle = self.task_data['local_data_bundle']
                self.task_data['local_data_bundle'] = json.dumps(local_data_bundle.__dict__)
            if 'output_data_bundle'  in self.task_data:
                output_data_bundle = self.task_data['output_data_bundle']
                self.task_data['output_data_bundle'] = json.dumps(output_data_bundle.__dict__)
            print(self.task_data)
            with open(save_file_path, 'w') as task_file:
                json.dump(self.task_data, task_file, indent=3)
            if 'local_data_bundle'  in self.task_data:
                self.task_data['local_data_bundle'] = local_data_bundle
            if 'output_data_bundle'  in self.task_data:
                self.task_data['output_data_bundle'] = output_data_bundle
        elif mode == "pickle":
            with open(save_file_path, 'wb') as task_file:
                pickle.dump(self.task_data, task_file)
        else:
            sys.exit("ERROR: Mode ({}) not supported")
        self.modified = False

    def _remote_wdir(self):
        """ Builds remote working directory """
        return self.task_data['remote_base_path'] + '/biobb_' + self.id
