#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
#import paramiko
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException
from credentials import sshCredentials


class sshExec():
    def __init__(self, credentials_path, command):
        self.command = command
        self.ssh_data = sshCredentials()
        self.ssh_data.load_from_file(credentials_path)

    def launch(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            ssh.connect(self.ssh_data.host, username=self.ssh_data.userid, pkey=self.ssh_data.key, look_for_keys=False)
        except AuthenticationException:
            print("Authentication Error", file=sys.stderr)
        (stdin, stdout, stderr) = ssh.exec_command(command)
        print(''.join(stdout))
        print(''.join(stderr), file=sys.stderr)
        ssh.close()


if __name__ == "__main__":
    cmd = sshExec(sys.argv[1], sys.argv[2]).launch()
