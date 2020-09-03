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
(void) credentials.save(output_path, public_key_path=None, private_key_path=None)
~~~
Stores SSHCredentials object in a external file
* output_path (**str**): Path to file  
* public_key_path (**str**): Path to a standard public key file
* private_key_path (**str**): Path to a standard private key file

~~~
(void) credentials.load_from_file(credentials_path) 
~~~
Recovers SSHCredentials object from disk file
* credentials_path (**str**): Path to packed credentials file. 

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
(str) credentials.get_private_key()
~~~
Returns a readable private key
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
ssh_session = SSHSession(ssh_data=None, credentials_path=None)
~~~
* ssh_data (**SSHCredentials**) : SSHCredentials object
* credentials_path (**str**) : Path to packed credentials file to use

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

## data_bundle.py
Class to manage bundles of input/output files
~~~
data_bundle = DataBundle(bundle_id)
~~~
* bundle_id (**str**): Id for the data bundle

~~~
data_bundle.add_file(file_path)
~~~
Adds a single file to the data bundle
* file_path (**str**): Path to the file

~~~
data_bundle.add_dir(dir_path)
~~~
Adds all files from a directory
* dir_path (**str**): Path to the directory

~~~
([str]) data_bundle.get_file_names()
~~~
Generates a list of names or included files

~~~
(str) data_bundle.to_json()
~~~
Generates a Json dump

## task.py
Abstract module to handle remote tasks. Not for direct use, extended to include specific queueing systems

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
task=Task(host=None, userid=None, look_for_keys=True)
~~~
 Classe to handle task execution 
* host (**str**): Remote host
* userid (**str**): Remote user id
* look_for_keys (**bool**): Look for keys in user's .ssh directory

~~~
(void) task.load_data_from_file(file_path, mode='json')
~~~
Loads accumulated task data from external file
* file_path (**str**): Path to file
* mode (**str**): Format. Json | Pickle

~~~
(void) task.set_credentials(credentials):
~~~
Loads ssh credentials from SSHCredentials object or from a external file
credentials (**SSHCredentials** | **str**): SSHCredentials object or a path to a file containing the data

~~~
(void) task.load_host_config(host_config_path)
~~~
Loads a pre-defined host configuration file

~~~
(void) task.set_modules(module_set)
~~~
Selects a predefined set of HPC modules to use. Module sets are defined in host configuration
* module_set (**str**): Label of the module set

~~~
(void) task.set_conda_env(conda_env)
~~~
Selects a conda environment to activate
* conda_env (**str**): Environment to activate

~~~
(void) task.set_queue_settings(setting_id='default')
~~~
Selects a set of queueing settings from host configuration.
* setting_id (**str**): Set to include

~~~
(void) task.set_local_data_bundle(local_data_path, add_files=True):
~~~
Builds local data bundle from a local directory
* local_data_path (**str**): Path to local data directory
* add_files (**bool**): On create add all files in the directory.

~~~
(void) task.send_input_data(remote_base_path, overwrite=True)
~~~
Uploads data bundle files to remote working dir
* remote_base_path (**str**): Remote base path for all task activites. Each task will create a unique working dir.
* overwrite (**bool**): Upload files even if they already exists in the remote working dir. 

~~~
(str) task.get_remote_py_script(python_import, files, command, properties='')
~~~
Generates 1 line python code to be executed in the queue script using python -c
* python_import (**str**): Python import line(s) to include (; separated)
* files (**dict**): File names to associate to biobb required path parameters
* command (**str**): biobb class to launch
* properties (**str**): 1 line Json with the required biobb parameters

~~~
(str) task.get_remote_comm_line(command, files, properties=''):
~~~
Generates a command line for queue script using command line version of the biobb module
* files (**dict**): File names to associate to biobb required path parameters
* command (**str**): biobb command (biobb_XX part of the path, base path provided by host configuration)
* properties (**str**): 1 line Json with the required biobb parameters

~~~
(str) task.prepare_queue_script(queue_settings, modules, conda_env):
~~~
Generates remote script including queue settings and necessary modules
* queue_settings (**str**): Label for set of queue controls (defined in host configuration)
* modules (**str**): modules to activate (defined in host configuration)
* conda_env (**str**): Conda environment to activate

~~~
([str]) task.get_queue_settings_string_array()
~~~
Generates queue settings to include in script. Developed in inherited queue classes

~~~
(void) task.submit(queue_settings, modules, local_run_script, conda_env='', poll_time=0)
~~~
Submits task 
* queue_settings (**str**): Label for set of queue controls (defined in host configuration)
* modules (**str**): modules to activate (defined in host configuration)
* conda_env (**str**): Conda environment to activate
* local_run_script (**str**): Path to local script to run or a string with the script itself (identified by leading '#' tag)
* poll_time (**int**): if set polls periodically for job completion (seconds)

~~~
(str) task.get_submitted_job_id()
~~~
Reports job id after submission, developed in inherited classes

~~~
(void) taskcancel(remove_data=False)
~~~
Cancels running task
* remove_data (**bool**): removes remote working directory

~~~
(str) task.check_queue()
~~~
Check queue status. Returns output of the remote appropriate command

~~~
(int) check_job_status()
~~~
Checks and reports job status

~~~
(void) check_job(update=True, poll_time=0)
~~~
Prints job status to stdout
* update (**bool**): update status before printing it
* poll_time (**int**): poll until job finished. Poll interval in seconds.

~~~
(void) task.get_remote_file(file):
~~~
Gets file from remote working dir
* file (**str**): File name

~~~
([stdout, strerr]) task.get_logs()
~~~
Get queue logs

~~~
(void) task.get_output_data(local_data_path='', overwrite=False)
~~~
Downloads remote working dir contents to local path
* local_data_path (**str**): Path to local directory 
* overwrite (**bool**): Overwrite local files if they exist

~~~
(void) task.save(save_file_path, mode='json')
~~~
Saves current task status in a external file. Can be used to recover session at a later time.
* save_file_path (**str**): Path to file
* mode (**str**): Format to use json|pickle.

~~~
(void) task.clean_remote()
~~~
Remove remote working dir

## slurm.py
Task Class extended to include specific settings for Slurm queueing system

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
v0.2.0 August 2020

### Copyright & Licensing
This software has been developed in the MMB group (http://mmb.irbbarcelona.org) at the
BSC (http://www.bsc.es/) & IRB (https://www.irbbarcelona.org/) for the European BioExcel (http://bioexcel.eu/), funded by the European Commission
(EU H2020 [675728](http://cordis.europa.eu/projects/675728)).

* (c) 2015-2020 [Barcelona Supercomputing Center](https://www.bsc.es/)
* (c) 2015-2020 [Institute for Research in Biomedicine](https://www.irbbarcelona.org/)

Licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), see the file
[LICENSE](LICENSE) for details.

![](https://bioexcel.eu/wp-content/uploads/2015/12/Bioexcell_logo_1080px_transp.png "Bioexcel")
