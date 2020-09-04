""" Base module to handle remote tasks """

import os
import sys
import uuid
import pickle
import json
import time

from biobb_remote.ssh_session import SSHSession
from biobb_remote.ssh_credentials import SSHCredentials
from biobb_remote.data_bundle import DataBundle

UNKNOWN = 0
SUBMITTED = 1
RUNNING = 2
CANCELLED = 3
FINISHED = 4
CLOSING = 5
JOB_STATUS = {
    UNKNOWN: 'Unknown',
    SUBMITTED: 'Submitted',
    RUNNING: 'Running',
    CANCELLED: 'Cancelled',
    FINISHED: 'Finished',
    CLOSING: 'Closing'
}

class Task():
    """ Classe to handle task execution 
            * host: Remote host
            * userid: remote user id
            * look_for_keys: Look for keys in user's .ssh directory
    """
    def __init__(self, host=None, userid=None, look_for_keys=True):
        self.id = str(uuid.uuid4())
        #self.description = description
        self.ssh_data = SSHCredentials(host=host, userid=userid, look_for_keys=look_for_keys)
        self.task_data = {'id':self.id}
        self.ssh_session = None
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

    def set_credentials(self, credentials):
        """ Loads ssh credentials from SSHCredentials object or from a external file"""
        if isinstance(credentials, SSHCredentials):
            self.ssh_data = credentials
        else:
            self.ssh_data.load_from_file(credentials)
            
    def load_host_config(self, host_config_path):
        try:
            with open(host_config_path, 'r') as host_config_file:
                self.host_config = json.load(host_config_file)
        except IOError as err:
            sys.exit(err)

    def set_modules(self, module_set):
        if module_set in self.host_config['modules']:
            self.task_data['modules'] = self.host_config['modules'][module_set]
        else:
            sys.exit('slurm: error: unknown module set')

    def set_queue_settings(self, setting_id='default', settings=None):

        host = self.ssh_data.host
        if host not in self.host_config['login_hosts']:
            sys.exit("Error. No configuration available for", host)
        
        if setting_id is None:
            setting_id = 'serial'
        
        if settings:
            self.task_data['queue_settings'] = settings
        elif setting_id == 'default':
            self.task_data['queue_settings'] = self.host_config['qsettings'][self.host_config['qsettings']['default']]
        else:
            self.task_data['queue_settings'] = self.host_config['qsettings'][setting_id]

        self.task_data['queue_settings']['job'] = self.id
        self.task_data['queue_settings']['stdout'] = 'job.out'
        self.task_data['queue_settings']['stderr'] = 'job.err'
        self.task_data['queue_settings']['working_dir'] = self._remote_wdir()
        self.task_data['biobb_apps_path'] = self.host_config['biobb_apps_path']

    def set_local_data_bundle(self, local_data_path, add_files=True):
        """ Builds local data bundle from a local directory"""
        self.task_data['local_data_bundle'] = DataBundle(self.id)
        self.task_data['local_data_path'] = local_data_path
        if add_files:
            self.task_data['local_data_bundle'].add_dir(local_data_path)
        self.modified = True

    def send_input_data(self, remote_base_path, overwrite=True):
        """ Uploads data to remote working dir """

        self._open_ssh_session()

        self.task_data['remote_base_path'] = remote_base_path
        stdout, stderr = self.ssh_session.run_command('mkdir -p ' + self._remote_wdir())
        if stderr:
            sys.exit('Error while creating remote working directory: ' + stderr)

        if not self.task_data['local_data_bundle']:
            sys.exit("Error: Create input data bundle first")
           
        remote_files = self.ssh_session.run_sftp('listdir', self._remote_wdir())
        ##TODO overwrite based on file timestamp
        for file_path in self.task_data['local_data_bundle'].files:
            remote_file_path = self._remote_wdir() + '/' + os.path.basename(file_path)
            if overwrite or os.path.basename(file_path) not in remote_files:
                self.ssh_session.run_sftp('put', file_path, remote_file_path)
                print("sending_file: {} -> {}".format(file_path, remote_file_path))
        self.task_data['input_data_loaded'] = True
        self.modified = True

    def get_remote_py_script(self, python_import, files, command, properties=''):
        """ Generates 1 line python command for queue script """
        cmd = python_import
        if properties:
            cmd += ";from biobb_common.configuration import settings;"
        cmd += command + "("
        file_str = []
        for file in files.keys():
            if files[file]:
                file_str.append(file + "='" + files[file] + "'")
        cmd += ','.join(file_str)
        if properties:
            if isinstance(properties, dict):
                prop = json.dumps(properties)
            else:
                prop = properties
            cmd += ", properties=settings.ConfReader(config='" + prop.replace('"', '\\"') + "').get_prop_dic()"
        cmd += ").launch()"
        return '#script\npython -c "' + cmd + '"\n'

    def get_remote_comm_line(self, command, files, properties=''):
        """ Generates a command line for queue script """
        cmd = [self.task_data['biobb_apps_path'] + command]
        for file in files.keys():
            if files[file]:
                cmd.append('--' + file + " " + files[file] )
        if properties:
            cmd.append("-c '" + json.dumps(properties) + "'")
        return '#script\n' + ' '.join(cmd) + '\n'

    def prepare_queue_script(self, queue_settings, modules):
        """ Generates remote script including queue settings"""
        ##TODO add custum queue_settings
        self.set_queue_settings(queue_settings)
        self.set_modules(modules)
        
        scr_lines = ["#!/bin/sh"]
        scr_lines += self.get_queue_settings_string_array()
        
        for mod in self.task_data['modules']:
            scr_lines.append('module load ' + mod)
        
        if self.task_data['local_run_script'].find('#') == -1:
            with open(self.task_data['local_run_script'], 'r') as scr_file:
                script = '\n'.join(scr_lines) + '\n' + scr_file.read()
        else:
            script = '\n'.join(scr_lines) + '\n' + self.task_data['local_run_script']
        return script

    def get_queue_settings_string_array(self):
        """ Generates queue settings to include in script
            Developed in inherited queue classes
        """
        return []

    def submit(self, queue_settings, modules, local_run_script, 
        poll_time=0):
        """ Submits task 
                * poll_time (seconds): if set polls periodically for job completion
        """
        self._open_ssh_session()
        
        self.task_data['local_run_script'] = local_run_script
        self.task_data['remote_run_script'] = self._remote_wdir() + '/run_script.sh'
        self.ssh_session.run_sftp(
            'create',
            self.prepare_queue_script(queue_settings, modules),
            self.task_data['remote_run_script']
        )
        stdout, stderr = self.ssh_session.run_command(
            self.commands['submit'] + ' ' + self.task_data['remote_run_script']
        )
        if stderr:
            sys.exit(stderr)
        self.task_data['remote_job_id'] = self.get_submitted_job_id(stdout)
        self.task_data['status'] = SUBMITTED
        self.modified = True
        print('Submitted job {}'.format(self.task_data['remote_job_id']))
        if poll_time:
            self.check_job(poll_time=poll_time)


    def get_submitted_job_id(self):
        """ Reports job id after submission, developed in inherited classes """
        return ''

    def cancel(self, remove_data=False):
        """ Cancels running task """

        if self.task_data['status'] in [SUBMITTED, RUNNING]:
            self._open_ssh_session()
            stdout, stderr = self.ssh_session.run_command(
                self.commands['cancel'] + ' ' + self.task_data['remote_job_id']
            )
            print("Job {} cancelled".format(self.task_data['remote_job_id']))
            if remove_data:
                self.clean_remote()
            self.task_data['status'] = CANCELLED
            self.modified = True
        else:
            print("Job {} not running".format(self.task_data['remote_job_id']))

    def check_queue(self):
        """ Check queue status """
        self._open_ssh_session()
        
        data = self.ssh_session.run_command(self.commands['queue'])
        return data

    def check_job_status(self):
        """ Checks job status """
        self._open_ssh_session()
        
        old_status = self.task_data['status']
        if self.task_data['status'] is not CANCELLED:
            stdout, stderr = self.ssh_session.run_command(
                self.commands['queue'] \
                + ' -h --job ' \
                + self.task_data['remote_job_id']
            )
            if not stdout:
                self.task_data['status'] = FINISHED
            else:
                jobid, partition, name, user, st, time, nodes, nodelist = stdout.split()
                if not st:
                    self.task_data['status'] = FINISHED
                elif st == 'R':
                    self.task_data['status'] = RUNNING
                elif st == 'CG':
                    self.task_data['status'] = CLOSING
                elif st == 'PD':
                    self.task_data['status'] = SUBMITTED
            self.modified = old_status != self.task_data['status']
        return self.task_data['status']

    def check_job(self, update=True, poll_time=0):
        """ Prints job status 
                * update: update status before printing it
                * poll_time (Seconds): poll until job finished
        """
        self.check_job_status()
        current_time = 0
        if self.task_data['status'] is CANCELLED:
            print ("Job cancelled by user")
        else:
            if poll_time:
                while self.check_job_status() != FINISHED:
                    self._print_job_status(prefix=current_time)
                    time.sleep(poll_time)
                    current_time += poll_time
            self._print_job_status()

    def _print_job_status(self, prefix=''):
        """ Prints readable job status """
        print("{} Job {} is {}".format(prefix, self.task_data['remote_job_id'], JOB_STATUS[self.task_data['status']]))

    def get_remote_file(self, file):
        """ Get file from remote working dir"""
        self._open_ssh_session()
        #TODO check remote file exists
        return self.ssh_session.run_sftp('file', self._remote_wdir() + "/" + file)

    def get_logs(self):
        """ Get specific queue logs"""
        self.check_job()
        stdout = self.get_remote_file(self.task_data['queue_settings']['stdout'])
        stderr = self.get_remote_file(self.task_data['queue_settings']['stderr'])

        return stdout, stderr


    def get_output_data(self, local_data_path='', overwrite=False):
        """ Downloads remote working dir contents to local """
        self._open_ssh_session()

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

        remote_file_list = self.ssh_session.run_sftp('listdir', self._remote_wdir())

        output_data_bundle = DataBundle(self.task_data['id'] + '_output')

        local_file_names = os.listdir(local_data_path)
        
        # TODO check for file time stamps
        for file in remote_file_list:
            if overwrite or (file not in local_file_names):
                output_data_bundle.add_file(file)

        for file in output_data_bundle.files:
            local_file_path = local_data_path + '/' + file
            remote_file_path = self._remote_wdir() + '/' + file
            self.ssh_session.run_sftp('get', remote_file_path, local_file_path)
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

    def clean_remote(self):
        """ Remove data from remote host """
        self._open_ssh_session()
        print("Removing remote data for job {}".format(self.task_data['remote_job_id']))
        self.ssh_session.run_command('rm -rf ' + self._remote_wdir())
        del self.task_data['output_data_path']
        del self.task_data['output_data_bundle']

    def _remote_wdir(self):
        """ Builds remote working directory """
        return self.task_data['remote_base_path'] + '/biobb_' + self.id

    def _open_ssh_session(self):
        if self.ssh_session:
            return False
        if not self.ssh_data:
            sys.exit("No credentials available")
        self.ssh_session = SSHSession(ssh_data=self.ssh_data)
        return False