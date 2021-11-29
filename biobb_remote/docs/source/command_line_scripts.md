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
