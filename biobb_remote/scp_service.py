#! /usr/bin/python3

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "gelpi"
__date__ = "$08-March-2019  17:32:38$"

import sys
#import paramiko
from paramiko import AuthenticationException
from paramiko import AutoAddPolicy
from paramiko import SSHClient
from credentials import sshCredentials


class sshExec():
    def __init__(self, oper, credFn, input_file_path, output_file_path):
        self.ssh_data = sshCredentials()
        self.ssh_data.load_from_file(credFn)
        self.op = oper
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def launch(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            ssh.connect(
                self.ssh_data.host,
                username=self.ssh_data.userid,
                pkey=self.ssh_data.key,
                look_for_keys=False
            )
        except AuthenticationException:
            sys.stderr.write("Authentication Error\n")
        sftp = ssh.open_sftp()
        try:
            if self.op == 'get':
                sftp.get(self.input_file_path, self.output_file_path)
            elif self.op == 'put':
                sftp.put(self.input_file_path, self.output_file_path)
        except IOError as err:
            print(err)

        ssh.close()


if __name__ == "__main__":
    cmd = sshExec(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]).launch()
