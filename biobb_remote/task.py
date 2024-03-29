""" Base module to handle remote tasks """

import os
import sys
import uuid
import pickle
import json
import time

from os.path import join as opj

from biobb_remote.ssh_session import SSHSession
from biobb_remote.ssh_credentials import SSHCredentials

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
BIOBB_COMMON_SETTINGS_IMPORT = 'from biobb_common.configuration import settings'
BIOBB_COMMON_SETTINGS_CALL = "settings.ConfReader(config='{}').get_prop_dic()"


class DataBundle():
    """ 
    | biobb_remote task.DataBundle
    | Class to pack a files manifest
    
    Args:
        bundle_id (str): Id for the data bundle
        remote (bool) (Optional): (False) Marks bundle as remote (no stats are generated)
    
    """
    def __init__(self, bundle_id, remote=False):
        self.id = bundle_id
        self.files = {}
        self.remote = remote

    def add_file(self, file_path):
        """
        | DataBundle.add_file
        | Adds a single file to the data bundle
    
        Args:
            file_path (str): Path to the file.
        """
        if file_path not in self.files:
            file_name = os.path.basename(file_path) 
            self.files[file_name] = {"full_path": file_path, 'stats': None}
        if not self.remote:
            self.files[file_name]['stats'] = os.stat(file_path)

    def add_dir(self, dir_path):
        """ 
        | DataBundle.add_dir
        | Adds all files from a directory
          
        Args:
            dir_path (str): Path to the directory
        """
        try:
            self.files = list(
                map(lambda x: opj(dir_path, x), os.listdir(dir_path)))
        except IOError as err:
            sys.exit(err)

    def get_file_names(self):
        """ 
        | DataBundle.get_file_names
        | Provides a list of names of included files"""
        return self.files.keys()

    def get_full_path(self, file_name):
        """ 
        | DataBundle.get_full_path
        | Gives the full path for a given file
        
        Args:
            file_name (str): Name of the file.
        """
        return self.files[file_name]['file_path']

    def get_mtime(self, file_name):
        """
        | DataBundle.get_mtime
        | Gives the modification time for a given file
        
        Args:
            file_name (str): Name of the file.
        """
        return self.files[file_name]['stats'].st_mtime

    def to_json(self):
        """ 
        | DataBundle.to_json
        | Generates a Json dump of the DataBundle
        """
        return json.dumps(self.__dict__)


class Task():
    """ 
    | task.Task
    | Abstract classe to handle task executions. 
    | Not to be used directly, should be extended with queue specific inherited classes.
    
    Args:
        host (str) (Optional): (None) Remote FQD of remote host.
        userid (str) (Optional): (None) Remote user id.
        look_for_keys (bool) (Optional): (True) Look for keys in user's .ssh directory.
        debug_ssh (bool) (Optional): (False) Open SSH session with debug activated.
    """

    def __init__(self, host=None, userid=None, look_for_keys=True, debug_ssh=False):
        self.id = str(uuid.uuid4())
        #self.description = description
        self.ssh_data = SSHCredentials(
            host=host, userid=userid, look_for_keys=look_for_keys)
        self.task_data = {'id': self.id, 'modules': []}
        self.ssh_session = None
        self.host_config = None
        self.debug = debug_ssh
        self.commands = {}
        self.modified = False

    def load_data_from_file(self, file_path, mode='json'):
        """ 
        | Task.load_data_from_file
        | Loads accumulated task data from local file
        
        Args:
            file_path (str): Path to file
            mode (str) (Optional): (json) File format. Accepted: Json | Pickle
        """
        # TODO detect file type
        if mode == 'pickle':
            file = open(file_path, 'rb')
            self.task_data = pickle.load(file)
        elif mode == 'json':
            file = open(file_path, 'r')
            self.task_data = json.load(file)
            if 'local_data_bundle' in self.task_data:
                local_data_bundle = json.loads(
                    self.task_data['local_data_bundle'])
                self.task_data['local_data_bundle'] = DataBundle(
                    local_data_bundle['id'])
                self.task_data['local_data_bundle'].files = local_data_bundle['files']
            if 'output_data_bundle' in self.task_data:
                output_data_bundle = json.loads(
                    self.task_data['output_data_bundle'])
                self.task_data['output_data_bundle'] = DataBundle(
                    output_data_bundle['id'])
                self.task_data['output_data_bundle'].files = local_data_bundle['files']
        else:
            sys.exit("ERROR: file type ({}) not supported".format(mode))
        self.id = self.task_data['id']

    def save(self, save_file_path, mode='json', verbose=False):
        """
        | Task.save
        | Saves current task status in a local file. 
        | Can be used to recover session at a later time.
        
        Args:
            save_file_path (str): Path to file
            mode (str) (Optional): (json) Format to use json|pickle.
            verbose (bool) (Optional): (False) Print additional information on stdout
        """
        if self.modified:
            self.task_data['id'] = self.id
            if mode == 'json':
                data = {'id': self.id}
                for k in self.task_data:
                    data[k] = self.task_data[k]
                if 'local_data_bundle' in self.task_data:
                    data['local_data_bundle'] = self.task_data['local_data_bundle'].to_json()
                if 'output_data_bundle' in self.task_data:
                    data['output_data_bundle'] = self.task_data['output_data_bundle'].to_json()
                with open(save_file_path, 'w') as task_file:
                    json.dump(data, task_file, indent=3)

            elif mode == "pickle":
                with open(save_file_path, 'wb') as task_file:
                    pickle.dump(self.task_data, task_file)
            else:
                sys.exit("ERROR: Mode ({}) not supported")
        
        self.modified = False
        
        if verbose:
            print("Task log saved on ", save_file_path)

# Credential management
    def set_credentials(self, credentials):
        """ 
        | Task.set_credentials
        | Loads ssh credentials from a SSHCredentials object or from a external file
        
        Args:
            credentials (SSHCredentials | str): SSHCredentials object or a path to a file containing the data.
        """
        if isinstance(credentials, SSHCredentials):
            self.ssh_data = credentials
        else:
            self.ssh_data.load_from_file(credentials)

    def set_private_key(self, private_path, passwd=None):
        """
        | Task.set_private_key
        | Inserts private key from external file
        
        Args:
            private_path (str): Path to private key file.
            passwd (str) (Optional): (None) Password to decrypt private key.
        """
        if not self.ssh_data:
            print("Create credentials first")
        else:
            self.ssh_data.load_from_private_key_file(passwd)
            
# Host config management
    def load_host_config(self, host_config_path):
        """
        | Task.load_host_config
        | Loads a configuration file for the remote host. 
        
        Args:
            host_config_path (str): Path to the configuration file
        """
        try:
            with open(host_config_path, 'r') as host_config_file:
                self.host_config = json.load(host_config_file)
        except IOError as err:
            sys.exit(err)

    def get_queue_info(self):
        """
        | Task.get_queue_info
        | Prints remote queue status.
        | Extended in inherited classes.
        """
        if 'queues_command' in self.host_config and self.host_config['queues_command']:
            self._open_ssh_session()
            data = self.ssh_session.run_command(
                ";".join(self.host_config['queues_command']))
        else:
            print("Warning: command not available on " +
                  self.host_config['description'])
            data = ''
        return data[0]

# Job settings
    def _set_modules(self, module_set):
        """
        | Private. Task._set_modules
        | Add module sets to task data
        
        Args:
            module_set (str | list(str)): module_set(s) to add. Taken from host configuration
        """
        if not isinstance(module_set, list):
            module_set = [module_set]
        self.task_data['modules'] = []
        for mod in module_set:
            if mod in self.host_config['modules']:
                self.task_data['modules'] += self.host_config['modules'][mod]
            else:
                sys.exit('slurm: error: unknown module set')

    def _set_queue_settings(self, setting_id='default', settings=None, set_debug=False):
        """ 
        | Private. Task._set_queue_settings
        | Adds queue settings to task
        
        Args:
            setting_id (str) (Optional): (default) Settings group as defined in host configuration
            settings (dict) (Optional): (None) Settings dict
            set_debub (bool) (Optional): (False) Add debug QOS
        """
        if settings:
            self.task_data['queue_settings'] = settings
        else:
            self.task_data['queue_settings'] = {}
            if setting_id == 'default':
                ref_settings = self.host_config['qsettings'][self.host_config['qsettings']['default']]
            else:
                ref_settings = self.host_config['qsettings'][setting_id]
            for k, v in ref_settings.items():
                self.task_data['queue_settings'][k] = v
        if 'job_name' in self.task_data and self.task_data['job_name']:
            self.task_data['queue_settings']['job'] = self.task_data['job_name']
            self.task_data['queue_settings']['stdout'] = self.task_data['job_name'] + '.out'
            self.task_data['queue_settings']['stderr'] = self.task_data['job_name'] + '.err'
        else:
            self.task_data['queue_settings']['job'] = self.id
            self.task_data['queue_settings']['stdout'] = 'job.out'
            self.task_data['queue_settings']['stderr'] = 'job.err'

        self.task_data['queue_settings']['working_dir'] = self._remote_wdir()

        if 'biobb_apps_path' in self.host_config:
            self.task_data['biobb_apps_path'] = self.host_config['biobb_apps_path']
        else:
            self.task_data['biobb_apps_path'] = '.'

        if set_debug:
            for k, v in self.host_config['qsettings']['debug'].items():
                self.task_data['queue_settings'][k] = v

    def set_custom_settings(self, ref_setting='default', patch=None, clean=False):
        """ 
        | Task.set_custom_settings
        | Adds custom settings to host configuration
        
        Args:
            ref_setting (str) (Optional): (default) Base settings to modify
            patch (dict) (Optional): (None) Patch to apply
            clean (bool) (Optional): (False) Clean settings
        """
        if ref_setting == 'default':
            ref_setting = self.host_config['qsettings']['default']

        if clean:
            qset = {}
        else:
            qset = self.host_config['qsettings'][ref_setting]

        if patch:
            for k in patch.keys():
                qset[k] = patch[k]

        self.host_config['qsettings']['custom'] = qset

    def prep_auto_settings(self, total_cores=0, nodes=0, cpus_per_task=1,  num_gpus=0):
        """
        | Task.prep_auto_settings
        | Prepare queue settings for balancing MPI/OMP/GPU.
        
        Args:
            total_cores (int) (Optional): (0) Aproximated number of cores to use
            nodes (int) (Optional): (0) Number of complete nodes to use (overrides total_cores)
            cpus_per_task (int) (Optional): (1) OMP processes per MPI task to allocate
            num_gpus (int) (Optional): (0) Num of GPUs per node to allocate
        """
        if nodes:
            total_cores = nodes * self.host_config['cores_per_node']

        if num_gpus:
            if self.host_config['gpus_per_node']:
                if cpus_per_task < self.host_config['min_cores_per_gpu']:
                    print("Warning: min cores per gpu is",
                          self.host_config['min_cores_per_gpu'])
                    cpus_per_task = self.host_config['min_cores_per_gpu']
            else:
                print("Warning: GPU not available at " +
                      self.host_config['description'])
                num_gpus = 0

        cpus_per_task = min(cpus_per_task, total_cores)
        ntasks = int(total_cores / cpus_per_task)
        ntasks_per_node = int(min(total_cores / cpus_per_task,
                                  self.host_config['cores_per_node'] / cpus_per_task))
        nodes = int(max(1, total_cores / self.host_config['cores_per_node']))

        if num_gpus:
            if ntasks_per_node > num_gpus:
                print("Warning: Num GPUs cannot be less than ntasks per node")
                num_gpus = ntasks_per_node

        if ntasks != ntasks_per_node * nodes:
            print('Warning: ntasks adjusted to match requested configuration')
            ntasks = ntasks_per_node * nodes

        settings = {
            'ntasks': ntasks,
            'cpus-per-task': cpus_per_task,
            'ntasks-per-node': ntasks_per_node,
            'nodes': nodes
        }
        if num_gpus:
            settings['gres'] = 'gpu:' + str(num_gpus)
        # For Gromacs
        if ntasks > 1 and cpus_per_task > 6:
            print(
                "Warning: requesting more OMP tasks than recommended, use -ntomp to force")

        return settings

# Job submission
    def set_local_data_bundle(self, local_data_path, add_files=True):
        """
        | Task.set_local_data_bundle
        | Builds local data bundle from a local directory
        
        Args:
            local_data_path (str): Path to local data directory
            add_files (bool) (Optional): (True) Add all files in the directory
        """
        self.task_data['local_data_bundle'] = DataBundle(self.id)
        self.task_data['local_data_path'] = local_data_path
        if add_files:
            self.task_data['local_data_bundle'].add_dir(local_data_path)
        self.modified = True

    def prep_remote_workdir(self, remote_base_path):
        """ 
        | Task.prep_remote_workdir
        | Creates a empty remote working dir
        Args:
            remote_base_path (str): Path to remote base directory, task folders created within
        """
        self.task_data['remote_base_path'] = remote_base_path
        stdout, stderr = self.ssh_session.run_command(
            'mkdir -p ' + self._remote_wdir())
        if stderr:
            sys.exit('Error while creating remote working directory: ' + stderr)


    def send_input_data(self, remote_base_path, create_dir=True, overwrite=True, new_only=True):
        """ 
        | Task.send_input_data
        | Uploads data to remote working dir
            
        Args:
            remote_base_path (str): Path to remote base directory, task folders created within
            create_dir (bool) (Optional): (True) Creates remote working dir
            overwrite (bool) (Optional): (True) Allows overwrite files with the same name if any
            new_only (bool) (Optional): (True) Overwrite only with newer files
        """
        self._open_ssh_session()
        
        if create_dir:
            self.prep_remote_workdir(remote_base_path)

        # self.task_data['remote_base_path'] = remote_base_path
        # stdout, stderr = self.ssh_session.run_command(
        #     'mkdir -p ' + self._remote_wdir())
        # if stderr:
        #     sys.exit('Error while creating remote working directory: ' + stderr)

        if not self.task_data['local_data_bundle']:
            sys.exit("Error: Create input data bundle first")

        #remote_files = self.ssh_session.run_sftp('listdir', self._remote_wdir())
        remote_files = self.get_remote_file_stats()

        for file_name in self.task_data['local_data_bundle'].files:            
            file = self.task_data['local_data_bundle'].files[file_name]
            exists = file_name in remote_files
            if exists:
                is_new = file['stats'].st_mtime > remote_files[file_name]['st_mtime']
            else:
                is_new = True
            if not exists or (overwrite and (not new_only or is_new)):
                remote_file_path = opj(self._remote_wdir(), file_name)
                self.ssh_session.run_sftp('put', file['full_path'], remote_file_path)
                print("sending_file: {} -> {}".format(file['full_path'], remote_file_path))
        self.task_data['input_data_loaded'] = True
        self.modified = True

    def get_remote_py_script(self, python_import, files, command, properties=''):
        """ 
        | Task.get_remote_py_script
        | Generates one-line python command to be inserted in the queue script
        Args:
            python_import (str | list(str)): Import(s) required to run the module (; separated).
            files (dict): Files required for module execution (parameter:file_name).
            command (str): Class name to launch.
            properties (dict | str) (Optional): ('') Either a dictionary, a json string, or a file name with properties to pass to the module.
        """
        if not isinstance(python_import, list):
            cmd = [python_import]
        else:
            cmd = python_import

        file_params = []
        for file in files.keys():
            if files[file]:
                file_params.append("{}='{}'".format(file, files[file]))
        files_str = ','.join(file_params)

        if properties:
            cmd.append(BIOBB_COMMON_SETTINGS_IMPORT)
            if isinstance(properties, dict):
                prop = json.dumps(properties)
            else:
                prop = properties
            prop_str = "properties=" + \
                BIOBB_COMMON_SETTINGS_CALL.format(prop.replace('"', '\\"'))
        else:
            prop_str = "properties=None"

        cmd.append("{}({},{}).launch()".format(command, files_str, prop_str))

        return '#script\npython -c "{}"\n'.format(';'.join(cmd))

    def get_remote_comm_line(self, command, files, use_biobb=False, properties='', cmd_settings=''):
        """
        | Task.get_remote_comm_list
        | Generates a command line for queue script
            
        Args:
            command (str): Command to execute
            files (dict): Input/output files. "--" added if not only parameter name is provided
            use_biobb (bool) (Optional): (False) Set to prepend biobb path on host
            properties (dict) (Optional): ('') BioBB properties
            cmd_settings (dict) (Optional): ('') Settings to add to command line (use -x  or --xxx as necessary)
        """

        if use_biobb and 'biobb_apps_path' in self.host_config:
            cmd = [self.host_config['biobb_apps_path'] + command]
        else:
            cmd = [command]

        for file in files.keys():
            if files[file]:
                if file[0] != '-':
                    cmd.append('--' + file)
                else:
                    cmd.append(file)
                cmd.append(" " + files[file])

        if properties:
            cmd_settings['-c'] = "'" + json.dumps(properties) + "'"

        if cmd_settings:
            for k, v in cmd_settings.items():
                if 'cmd_settings' in self.host_config and k in self.host_config['cmd_settings']:
                    cmd += [self.host_config['cmd_settings'][k]]
                else:
                    cmd += [k, str(v)]

        return '#script\n' + ' '.join(cmd) + '\n'

    def _prepare_queue_script(self, queue_settings, modules, conda_env='', set_debug=False):
        """
        | Private. Task._prepare_queue_script
        | Generates the remote queueing script including queue settings
        
        Args:
            queue_settings (sict): Queue settings
            modules (str | list(str)): Modules to load
            conda_env (str) (Optional): ('') Conda environment to activate
            set_debug (bool) (Optional): (False) Add Debug QOS to the settings
        """

        # Add to self.task_data
        if queue_settings:
            self._set_queue_settings(queue_settings, set_debug=set_debug)
        if modules:
            self._set_modules(modules)
        if conda_env:
            self.task_data['conda_env'] = conda_env
        self.modified = True

        # Build bash script

        scr_lines = ["#!/bin/bash"]
        scr_lines += self._get_queue_settings_string_array()

        for mod in self.task_data['modules']:
            scr_lines.append('module load ' + mod)

        if conda_env:
            scr_lines.append('conda activate ' + conda_env)

        if self.task_data['local_run_script'].find('#script') == -1:
            with open(self.task_data['local_run_script'], 'r') as scr_file:
                script = '\n'.join(scr_lines) + '\n' + scr_file.read()
        else:
            script = '\n'.join(scr_lines) + '\n' + \
                self.task_data['local_run_script']

        return script

    def _get_queue_settings_string_array(self):
        """
        | Private. Task._get_queue_settings_string_array
        | Generates queue settings to include in script
        | Developed in inherited queue classes
        """
        return []

    def submit(
            self, 
            job_name=None, 
            set_debug=False, 
            queue_settings='default', 
            modules=None, 
            local_run_script='', 
            conda_env='', 
            save_file_path=None, 
            poll_time=0
            ):
        """
        | Task.submit
        | Submits task to the queue, return job id, optionally polls until job completion
        
        Args:
            job_name (str) (Optional): (None) Job name to display (used to identify queue jobs, and stdout/stderr logs)
            set_debug (bool) (Optional): Adjust queue settings to debug QoS (as defined in host configuration)
            queue_settings (str) (Optional): (default) Label for set of queue controls (as defined in host configuration). Use 'custom' for patched settings
            modules (str) (Optional): (None) Modules to activate (defined in host configuration)
            conda_env (str) (Optional): ('') Conda environment to activate
            local_run_script (str) (Optional): ('') Path to local bash script to run or a string with the script itself (identified by a leading '#script' tag)
            save_file_path (str) (Optional): (None) Path to save task log
            poll_time (int) (Optional): (0) Polling time for job completion (seconds). Set to O to do not wait. 
        """
        # Checking that configuration is a valid one
        if self.ssh_data.host not in self.host_config['login_hosts']:
            sys.exit("Error. Configuration available does not apply to",
                     self.ssh_data.host)

        self._open_ssh_session()

        self.task_data['local_run_script'] = local_run_script
        self.task_data['remote_run_script'] = opj(self._remote_wdir(), 'run_script.sh')

        if job_name:
            self.task_data['job_name'] = job_name

        self.ssh_session.run_sftp(
            'create',
            self._prepare_queue_script(
                queue_settings, modules, conda_env=conda_env, set_debug=set_debug),
            self.task_data['remote_run_script']
        )

        stdout, stderr = self.ssh_session.run_command(
            self.commands['submit'] + ' ' + self.task_data['remote_run_script']
        )

        if stderr:
            sys.exit(stderr)

        self.task_data['remote_job_id'] = self._get_submitted_job_id(stdout)

        self.task_data['status'] = SUBMITTED

        self.modified = True

        print('Submitted job {}'.format(self.task_data['remote_job_id']))
        
        if save_file_path:
            self.save(save_file_path)
        
        if poll_time:
            self.check_job(poll_time=poll_time)

    def _get_submitted_job_id(self):
        """
        | Private. Task._get_submitted_job_id
        | Reports job id after submission.
        | Developed in inherited classes 
        """
        return ''

# Job management
    def cancel(self, remove_data=False):
        """
        | Task.cancel
        | Cancels running task
        
        Args:
            remove_data (bool) (Optional): (False) Removes remote working directory
        """

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
        """ 
        | Task.check_queue
        | Check queue status
        """
        self._open_ssh_session()

        data = self.ssh_session.run_command(self.commands['queue'])
        return data

    def _check_job_status(self):
        """
        | Private. Task._check_job_status
        | Checks currrent job status
        """
        self._open_ssh_session()

        old_status = self.task_data['status']
        if self.task_data['status'] is not CANCELLED:
            stdout, stderr = self.ssh_session.run_command(
                self.commands['queue']
                + ' -h --job '
                + self.task_data['remote_job_id']
            )
            if not stdout:
                self.task_data['status'] = FINISHED
            else:
                jobid, partition, name, user, stat, atime, nodes, nodelist = stdout.split()
                if not stat:
                    self.task_data['status'] = FINISHED
                elif stat == 'R':
                    self.task_data['status'] = RUNNING
                elif stat == 'CG':
                    self.task_data['status'] = CLOSING
                elif stat == 'PD':
                    self.task_data['status'] = SUBMITTED
            self.modified = old_status != self.task_data['status']
        return self.task_data['status']

    def check_job(self, update=True, save_file_path=None,  poll_time=0):
        """
        | Task.check_job
        | Prints current job status
        Args:
            update (bool) (Optional): (True) Update status before printing it.
            save_file_path (str) (Optional): (None) Local task log file to update progress.
            poll_time (int) (Optional): (0) Poll until job finished (seconds).
        """
        if update:
            self._check_job_status()
            if save_file_path:
                self.save(save_file_path)
        current_time = 0
        if self.task_data['status'] is CANCELLED:
            print("Job cancelled by user")
        else:
            if poll_time:
                while self._check_job_status() != FINISHED:
                    self._print_job_status(prefix=current_time)
                    time.sleep(poll_time)
                    current_time += poll_time
            self._print_job_status()
            if save_file_path:
                self.save(save_file_path)

    def _print_job_status(self, prefix=''):
        """
        | Private. Task._print_job_status
        | Prints readable job status
        
        Args:
            prefix(str) (Options): ('') Leading prefix to add to print lines
        """
        print("{} Job {} is {}".format(
            prefix, self.task_data['remote_job_id'], JOB_STATUS[self.task_data['status']]))

# Output data management
    def get_remote_file(self, file):
        """
        | Task.get_remote_file
        | Download file from remote working dir
        
        Args:
            file(str): Name of the remote file to download.
        """
        
        self._open_ssh_session()
        # TODO check remote file exists
        return self.ssh_session.run_sftp('file', opj(self._remote_wdir(), file))

    def get_logs(self):
        """
        | Task.get_logs
        | Get stdout, and stderr queue logs.
        """
        self.check_job()
        stdout = self.get_remote_file(
            self.task_data['queue_settings']['stdout'])
        stderr = self.get_remote_file(
            self.task_data['queue_settings']['stderr'])

        return stdout, stderr

    def get_remote_file_stats(self):
        """
        | Task.get_remote_file_stats
        | Returns remote files stats
        """
        self._open_ssh_session()
        stats = {}
        for file in self.ssh_session.run_sftp('listdir', self._remote_wdir()):
            stats[file] = vars(self.ssh_session.run_sftp(
                'lstat', opj(self._remote_wdir(), file)))
        return stats

    def get_output_data(
        self, 
        local_data_path='', 
        files_only=None, 
        overwrite=True, 
        new_only=True, 
        verbose=False
        ):
        """
        | Task.get_output_data
        | Downloads the contents of remote working dir
        
        Args:
            local_data_path (str) (Optional): ('') Path to local working dir
            files_only (list(str) (Optional)): (None) Only download files in list, if empty download all files
            overwrite (bool) (Optional): (True) Overwrite local files if they exist
            new_only (bool) (Optional): (True) Overwrite only with newer files
            verbose (bool) (Optional): (False) Show file status
        """

        self._open_ssh_session()

        if not self.task_data['remote_base_path']:
            sys.exit('task_recover_data: error: remote base path not available')

        if not local_data_path:
            if 'output_data_path' in self.task_data:
                local_data_path = self.task_data['output_data_path']
            elif 'local_data_path' in self.task_data:
                local_data_path = self.task_data['local_data_path']
                print("Warning: re-using original input folder")
            else:
                sys.exit("ERROR: Local path for output not provided")

        if not os.path.exists(local_data_path):
            os.mkdir(local_data_path)
        if verbose:
            print("Getting remote file stats")
        if new_only:
            remote_files = self.get_remote_file_stats()
        else:
            remote_files = self.ssh_session.run_sftp('listdir', self._remote_wdir())
        
        if files_only:
            for file in files_only:
                if file not in remote_files:
                    print(
                        "Warning: file {} is not in the remote working dir".format(file))

        remote_file_list = []
        for file in remote_files:
            if not files_only or file in files_only:
                remote_file_list.append(file)

        output_data_bundle = DataBundle(
            self.task_data['id'] + '_output', remote=True)

        local_file_names = os.listdir(local_data_path)

        for file in remote_file_list:
            if file in local_file_names:
                is_new = remote_files[file]['st_mtime'] > os.stat(opj(local_data_path, file)).st_mtime
            else:
                is_new = True

            if verbose:
                print('{:20s} Exists: {}, New: {}'.format(file, file in local_file_names, is_new))
            
            if (file not in local_file_names) or (overwrite and (not new_only or is_new)):
                output_data_bundle.add_file(file)
                output_data_bundle.files[file]['stats'] = remote_files[file]

        for file in output_data_bundle.files:
            local_file_path = opj(local_data_path, file)
            remote_file_path = opj(self._remote_wdir(), file)
            self.ssh_session.run_sftp('get', remote_file_path, local_file_path)

            print("getting_file: {} -> {}".format(remote_file_path, local_file_path))

        self.task_data['output_data_bundle'] = output_data_bundle
        self.task_data['output_data_path'] = local_data_path
        self.modified = True

    def clean_remote(self):
        """
        | Task.clean_remote
        | Remove job data from remote host 
        """
        
        self._open_ssh_session()
        
        print("Removing remote data for task {}".format(self.id))
        
        self.ssh_session.run_command('rm -rf ' + self._remote_wdir())
        if 'output_data_path' in self.task_data:
            del self.task_data['output_data_path']
        if 'output_data_bundle' in self.task_data:
            del self.task_data['output_data_bundle']

    def _remote_wdir(self):
        """
        | Private. Task._remote_wdir
        | Builds full path for the remote working directory
        """
        return self.task_data['remote_base_path'] + '/biobb_' + self.id

    def _open_ssh_session(self):
        """
        | Private. Task._open_ssh_session
        | Open SSH session to handle operations. Re-uses existing one if still active
        """
        if self.ssh_session and self.ssh_session.is_active():
            return False
        if not self.ssh_data:
            sys.exit("No credentials available")
        self.ssh_session = SSHSession(ssh_data=self.ssh_data, debug=self.debug)
        return False
