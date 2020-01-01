# biobb_remote

### Introduction
Biobb_remote is a set of utilities to allow biobb blocks to be executed on remote sites
through ssh

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
v0.1.0 December 2019

### Copyright & Licensing
This software has been developed in the MMB group (http://mmb.irbbarcelona.org) at the
BSC (http://www.bsc.es/) & IRB (https://www.irbbarcelona.org/) for the European BioExcel (http://bioexcel.eu/), funded by the European Commission
(EU H2020 [675728](http://cordis.europa.eu/projects/675728)).

* (c) 2015-2019 [Barcelona Supercomputing Center](https://www.bsc.es/)
* (c) 2015-2019 [Institute for Research in Biomedicine](https://www.irbbarcelona.org/)

Licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), see the file
[LICENSE](LICENSE) for details.

![](https://bioexcel.eu/wp-content/uploads/2015/12/Bioexcell_logo_1080px_transp.png "Bioexcel")
