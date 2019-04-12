#! /usr/bin/python3

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "gelpi"
__date__ = "$08-March-2019  17:32:38$"

from credentials import sshCredentials
from io import StringIO
import json
import paramiko
from paramiko import AuthenticationException
from paramiko import AutoAddPolicy
from paramiko import RSAKey
from paramiko import SSHClient
import pickle
import sys


class sshExec():
    def __init__(self, op, credFn, input_file_path, output_file_path):
        fh = open(credFn, 'rb')
        self.sshData = pickle.load(fh)    
        self.sshData['key'] = RSAKey.from_private_key(StringIO(self.sshData['key'].getvalue()))
        fh.close()
        self.op = op
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
      
    def launch(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            ssh.connect(self.sshData['host'], username=self.sshData['userid'], pkey=self.sshData['key'], look_for_keys=False)
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
    op = sys.argv[1]
    credFn = sys.argv[2]
    input_file_path = sys.argv[3]
    output_file_path = sys.argv[4]
    cmd = sshExec(op, credFn, input_file_path, output_file_path).launch()
