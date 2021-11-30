## credentials
Credentials manager. Generates key pairs to be consumed by other utilities

~~~
credentials [-h] [--user USERID] [--host HOSTNAME]
            [--pubkey_path PUBKEY_PATH] [--nbits NBITS] --keys_path
            KEYS_PATH [--privkey_path PRIVKEY_PATH]
            command
~~~

### Commands:
  * **create**: Create key pair
  * **get_pubkey**: Print Public key
  * **get_private**: Print Private key
  * **host_install**: Authorize key in remote host (requires authorized local keys)
  * **host_remove**: Revert authorization on remote host (requires authorized local keys)
  * **host_check**: Check authorization status on remote host.
                        Operation: create|get_pubkey
### optional arguments:
    -h, --help                show this help message and exit
    --user USERID             User id
    --host HOSTNAME           Host name
    --pubkey_path PUBKEY_PATH Public key file path
    --nbits NBITS             Number of key bits
    --keys_path KEYS_PATH     Credentials file path
    --privkey_path PRIVKEY_PATH Private key file path
    -v                        Output extra information

***
## scp_service
Simple sftp service
~~~
scp_service [-h] --keys_path KEYS_PATH [-i INPUT_FILE_PATH]
                   [-o OUTPUT_FILE_PATH]
                   command
~~~
### commands
 * **get**: Get remote file
 * **put**: Put file to remote
 * **create**: Create text file on remote
 * **file**: Print remote text file
 * **listdir**: List remote directory

### optional arguments:  
    -h, --help            - Show this help message and exit  
    --keys_path KEYS_PATH - Credentials file path  
    -i INPUT_FILE_PATH    - Input file path | input string
    -o OUTPUT_FILE_PATH   - Output file path
***
## ssh_command
Simple remote ssh command
~~~
ssh_command [-h] --keys_path KEYS_PATH [command [command ...]]
~~~

    command               - Remote command

    -h, --help            - show this help message and exit
    --keys_path KEYS_PATH - Credentials file path
***
## slurm_test
Complete set of functions to manage slurm submissions remotely
~~~
slurm_test [-h] --keys_path KEYS_PATH [--script SCRIPT_PATH]
                  [--local_data LOCAL_DATA_PATH] [--remote REMOTE_PATH]
                  [--queue_settings Q_SETTINGS] [--module MODULE]
                  [--task_data TASK_FILE_PATH]
                  command
~~~
### Command
* **submit**: Submit job
* **queue**: Check queue status
* **cancel**: Cancel submitted job
* **status**: Check job status
* **get_data**: Download remote files
* **put_data**: Upload local files to remote
* **log**: Get log files (stdout, stderr)
* **get_file**: Get single remote file

### optional arguments:
    -h, --help                      - show this help message and exit
    --keys_path KEYS_PATH           - Credentials file path
    --script LOCAL_RUN_SCRIPT       - Path to local script
    --local_data LOCAL_DATA_PATH    - Local data bundle
    --remote REMOTE_PATH            - Remote working dir
    --queue_settings QUEUE_SETTINGS - Predefined queue settings
    --modules MODULES               - Software modules to load
    --task_data_file TASK_FILE_PATH - Store for task data
    --overwrite                     - Overwrite data in output local directory
    --task_file_type TASK_FILE_TYPE - Format for task data file (json, pickle). Default:json
    --poll POLLING_INT              - Polling interval (seg), 0: No polling (default)
    --remote_file REMOTE_FILE       - Remote file name to download (get_file)

***


