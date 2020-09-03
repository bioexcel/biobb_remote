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
(**void**) credentials.save(output_path, public_key_path=None, private_key_path=None)
~~~
Stores SSHCredentials object in a external file
* output_path (**str**): Path to file  
* public_key_path (**str**): Path to a standard public key file
* private_key_path (**str**): Path to a standard private key file

~~~
(**void**) credentials.load_from_file(credentials_path) 
~~~
Recovers SSHCredentials object from disk file
* credentials_path (**str**): Path to packed credentials file. 

~~~
(**void**) credentials.generate_key(nbits=2048)
~~~
Generates RSA keys pair
* nbits (**int**): number of bits the generated key

~~~
(**str**) credentials.get_public_key(suffix='@biobb')
~~~
Returns a readable publik key suitable to addto authorized keys
* suffix (**str**): Added to the key for identify it.

~~~
(**str**) credentials.get_private_key()
~~~
Returns a readable private key
~~~
(**bool**) credentials.check_host_auth()
~~~
Checks for public_key in remote .ssh/authorized_keys file. Requires users' SSH access to host

~~~
(**void**) credentials.install_host_auth(file_bck='bck')
~~~
Installs public_key on remote .ssh/authorized_keys file. Requires users' SSH access to host
* file_bck (**str**): Generates an authorized.**file_bck** file with original authorized keys

~~~
(**void**) credentials.remove_host_auth(file_bck='biobb')
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
(**str**) ssh_session.run_command(command)
~~~
Runs command on remote. Returns stdout + stderr
* command (**str**): Command line to execute

~~~
(**bool** | **file_handle**) ssh_session.run_sftp(oper, input_file_path, output_file_path='')
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
