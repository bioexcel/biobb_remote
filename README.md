# biobb_remote

### Introduction
Biobb_remote is a package to allow biobb's to be executed on remote sites
through ssh

## ssh_credentials.py
Provides SSHCredentials to manage the generation, and installation of ssh credentials
~~~
credentials = SSHCredentials(host='', userid='', generate_key=False, look_for_keys=True)
~~~
* host (**str**): remote host name
* userid (**str**): remote user name
* generate_key (**bool**): Generates new public/private keys pair
* look_for_keys (**bool**): Look user's .ssh keys if keys not set

### Methods
~~~
(void) credentials.save(output_path, public_key_path=None, private_key_path=None, passwd=None)
~~~
Stores SSHCredentials object in a external file
* output_path (**str**): Path to file  
* public_key_path (**str**): Path to a standard public key file
* private_key_path (**str**): Path to a standard private key file
* passwd (**str**): Password to encrypt private key (optional)

~~~
(void) credentials.load_from_file(credentials_path, passwd=None)
~~~
Recovers SSHCredentials object from disk file
* credentials_path (**str**): Path to packed credentials file.
* passwd (**str**): Passwd to decrypt private key (optional)

~~~
(void) credentials.load_from_private_key_file(private_path, passwd=None)
~~~
Recovers SSHCredentials object from disk file
* private_path (**str**): Path to private key file.
* passwd (**str**): Passwd to decrypt private key (optional)

~~~
(void) credentials.generate_key(nbits=2048)
~~~
Generates RSA keys pair
* nbits (**int**): number of bits the generated key

~~~
(str) credentials.get_public_key(suffix='@biobb')
~~~
Returns a readable publik key suitable to addto authorized keys
* suffix (**str**): Added to the key for identify it.

~~~
(str) credentials.get_private_key(passwd=None)
~~~
Returns a readable possibly encrypted private key
* passwd (**str**): Password to encrypt private key (optional)

~~~
(bool) credentials.check_host_auth()
~~~
Checks for public_key in remote .ssh/authorized_keys file. Requires users' SSH access to host

~~~
(void) credentials.install_host_auth(file_bck='bck')
~~~
Installs public_key on remote .ssh/authorized_keys file. Requires users' SSH access to host
* file_bck (**str**): Generates an authorized.**file_bck** file with original authorized keys

~~~
(void) credentials.remove_host_auth(file_bck='biobb')
~~~
Removes public_key on remote .ssh/authorized_keys file. Requires users' SSH access to host
* file_bck (**str**): Generates an authorized.**file_bck** file with original authorized keys


## ssh_session.py
Class wrapping ssh operations
~~~
ssh_session = SSHSession(ssh_data=None, credentials_path=None, private_path=None, passwd=None)
~~~
* ssh_data (**SSHCredentials**) : SSHCredentials object
* credentials_path (**str**) : Path to packed credentials file to use
* private_path (**str**): Path to private key file
* passwd (**str**): Password to decrypt credentials (optional)
~~~
(str) ssh_session.run_command(command)
~~~
Runs command on remote. Returns stdout + stderr
* command (**str**): Command line to execute

~~~
(bool | file_handle) ssh_session.run_sftp(oper, input_file_path, output_file_path='')
~~~
Runs SFTP session on remote
* oper (**str**): Operation to perform, one of
        * get (gets a single file from input_file_path (remote) to output_file_path (local) )
        * put (puts a single file from input_file_path (local) to output_file_path (remote)
        * create (creates a file in output_file_path (remote) from input_file_path string-
        * file (opens a remote file in input_file_path for read). Returns a file handle.
        * listdir (returns a list of files in remote input_file_path
* input_file_path (**str**): Input file path or input string
* output_file_path (**str**): Output file path

## task.py
**DataBundle**
Class to manage bundles of input/output files
~~~
data_bundle = DataBundle(bundle_id)
~~~
* bundle_id (**str**): Id for the data bundle

~~~
data_bundle.add_file(file_path)
~~~
Adds a single file to the data bundle
* file_path (**str**): Path to the file to add

~~~
data_bundle.add_dir(dir_path)
~~~
Adds all files from a directory
* dir_path (**str**): Path to the directory to add

~~~
([str]) data_bundle.get_file_names()
~~~
Generates a list of names or included files

~~~
(str) data_bundle.to_json()
~~~
Generates a Json dump

**Task**
Abstract module to handle remote tasks. Not for direct use, extend to include specific queueing systems

### Constants
~~~
task.UNKNOWN = 0
task.SUBMITTED = 1
task.RUNNING = 2
task.CANCELLED = 3
task.FINISHED = 4
task.CLOSING = 5
task.JOB_STATUS (dict)
~~~
### Methods

~~~
task=Task(host=None, userid=None, look_for_keys=True, debug_ssh=False)
~~~
 Classe to handle task execution
* host (**str**): Remote host
* userid (**str**): Remote user id
* look_for_keys (**bool**): Look for keys available in user's .ssh directory
  debug_ssh (**bool**): Open SSH session with debug activated

~~~
(void) task.load_data_from_file(file_path, mode='json')
~~~
Loads accumulated task data from external file
* file_path (**str**): Path to file
* mode (**str**): Format. Json | Pickle

~~~
(void) task.save(save_file_path, mode='json', verbose=Falsse)
~~~
Saves current task status in a external file. Can be used to recover session at a later time.
* save_file_path (**str**): Path to file
* mode (**str**): Format to use json|pickle.
* verbose (**bool**): Print additional information

~~~
(void) task.set_credentials(credentials, passwd=None):
~~~
Loads ssh credentials from SSHCredentials object or from a external file
* credentials (**SSHCredentials** | **str**): SSHCredentials object or a path to a file containing the data
* passwd (**str**): Password to decrypt private key when loaded from file (optional)

~~~
(void) task.set_private_key(private_path, passwd=None):
~~~
Inserts private key from external file
* private_path (**str**): Path to private key file
* passwd (**str**, optional): Password to decrypt private key

~~~
(void) task.load_host_config(host_config_path)
~~~
Loads a pre-defined host configuration file (json format)
* host_config_path (**str**): Path to the configuration file

~~~
(void) task.set_custom_settings(self, ref_setting='default', patch=None, clean=False)
~~~
Generates a custom queue setting based on existing one
* ref_setting (**str**): Base settings to modify
* patch (**dict**): Patch to apply
* clean (**bool**): Clean existing settings

~~~
(void) task.prep_auto_settings(total_cores=0, nodes=0, cpus_per_task=1,  num_gpus=0)
~~~
Generates queue configuration settings for balancing MPI/OMP/GPU.
* total_cores (**int**): Aproximated number of cores to use
* nodes (**int**): Number of complete nodes to use (overrides total_cores)
* cpus_per_task (**int**): OMP processes per MPI task to allocate
* num_gpus (**int**): Num of GPUs per node to allocate

~~~
(void) task.set_local_data_bundle(local_data_path, add_files=True)
~~~
Builds local data bundle from a local directory
* local_data_path (**str**): Path to local data directory
* add_files (**bool**): On create, add all files in the directory.

~~~
(void) task.send_input_data(remote_base_path, overwrite=True, new_only=True)
~~~
Uploads data bundle files to remote working dir
* remote_base_path (**str**): Remote base path for all task activites. Each task will create a unique working dir (re-usable).
* overwrite (**bool**): Upload files even if they already exists in the remote working dir.
* new_only (**bool**): Overwrite only with newer files

~~~
(str) task.get_remote_py_script(python_import, files, command, properties='')
~~~
Generates 1 line python code to be executed in the queue script using python -c
* python_import (**str**): Python import line(s) to include (; separated)
* files (**dict**): File names to associate to biobb required path parameters
* command (**str**): biobb class to launch
* properties (**dict** | **str**): Either a dict, path to a json or yaml config file or a 1-line Json with the required biobb parameters

~~~
(str) task.get_remote_comm_line(command, files, use_biobb=False, properties='', cmd_settings=''):
~~~
Generates a command line for queue script. Can be used to launch a biobb module or any command line remotely.
* job_name (**str**): Job name to display (optional, used to identify queue jobs, and stdout/stderr logs)
* command (**str**): Command to execute
* files (**dict**): Input/output files. "--" prefix added if only a parameter name is provided
* use_biobb (**bool**): Set to prepend biobb path on host
* properties (**dict**): BioBB properties
* cmd_settings (**dict**): Additional settings to add to the command line, pre-set bundles can be configured in host config data.

~~~
(void) task.submit(job_name=None, queue_settings='default', modules=None, local_run_script='', conda_env='', save_file_path=None, poll_time=0)
~~~
Submits task to remote. Optionally waits until completion.
* job_name (**str**): Job name to display in the queuing system. Stdout/stderr logs are named as job.name.(out|err). Optional, defaults to queue default behaviour.
* queue_settings (**str**): Label for set of queue settings (defined in host configuration). Use 'custom' for user defined settings (see set_custom_settings)
* modules (**str**): modules to activate (defined in host configuration)
* conda_env (**str**): Conda environment to activate
* local_run_script (**str**): Path to local script to run or a string with the script itself (identified by leading '#' tag)
* save_file_path (**str**): Path to local task log file to update after submit (Default None),
* poll_time (**int**): if set, polls periodically for job completion (seconds)

~~~
(void) task.cancel(remove_data=False)
~~~
Cancels running task
* remove_data (**bool**): Removes remoted workign directory.

~~~
(str) task.check_queue()
~~~
Check queue status. Returns output of the remote appropriate command

~~~
(void) check_job(update=True, poll_time=0, save_file_path=None)
~~~
Prints job status to stdout
* update (**bool**): update status before printing it
* poll_time (**int**): poll until job finished. Poll interval in seconds.
* save_file_path (**str**): Path to local task log file to update status (Default None),

~~~
(void) task.get_remote_file(file):
~~~
Gets file from remote working dir
* file (**str**): File name

~~~
([stdout, stderr]) task.get_logs()
~~~
Get queue logs

~~~
(void) task.get_output_data(local_data_path='', files_only=None, overwrite=True, new_only=True)
~~~
Downloads remote working dir contents to local path
* local_data_path (**str**): Path to local directory
* files_only (**[str]**): Only download files in list, if empty download all files
* overwrite (**bool**): Overwrite local files if they exist
* new_only (**bool**): Overwrite only with newer files

~~~
(void) task.clean_remote()
~~~
Remove remote working dir

## slurm.py
Task Class extended to include specific settings for Slurm queueing system

## conf/XXX.json
Host configuration files

### Utilities
## credentials
Generates kay pairs to be consumed by other utilities

~~~
credentials [-h] [--user USERID] [--host HOSTNAME]
            [--pubkey_path PUBKEY_PATH] [--nbits NBITS] --keys_path
            KEYS_PATH [--privkey_path PRIVKEY_PATH]
            {create,get_pubkey,get_private}
~~~

## scp_service
Simple sftp service
~~~
scp_service [-h] --keys_path KEYS_PATH [-i INPUT_FILE_PATH]
                   [-o OUTPUT_FILE_PATH]
                   {get,put,create,file,listdir}
~~~

## ssh_command
Simple remote ssh command
~~~
ssh_command [-h] --keys_path KEYS_PATH [command [command ...]]
~~~

## slurm_test
Complete set of functions to manage slurm submissions remotely
~~~
slurm_test [-h] --keys_path KEYS_PATH [--script SCRIPT_PATH]
                  [--local_data LOCAL_DATA_PATH] [--remote REMOTE_PATH]
                  [--queue_settings Q_SETTINGS] [--module MODULE]
                  [--task_data TASK_FILE_PATH]
                  {submit,queue,cancel,status,get_data,put_data}
~~~

### Version
v1.2.1 November 2021

### Copyright & Licensing
This software has been developed in the MMB group (http://mmb.irbbarcelona.org) at the
BSC (http://www.bsc.es/) & IRB (https://www.irbbarcelona.org/) for the European BioExcel (http://bioexcel.eu/), funded by the European Commission
(EU H2020 [675728](http://cordis.europa.eu/projects/675728)).

* (c) 2015-2021 [Barcelona Supercomputing Center](https://www.bsc.es/)
* (c) 2015-2021 [Institute for Research in Biomedicine](https://www.irbbarcelona.org/)

Licensed under the
[GNU Lesser General Public License v2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html), see the file
[LICENSE](LICENSE) for details.

![](https://bioexcel.eu/wp-content/uploads/2015/12/Bioexcell_logo_1080px_transp.png "Bioexcel")
