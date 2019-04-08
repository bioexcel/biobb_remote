#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import pickle
import paramiko
from paramiko import SSHClient, AutoAddPolicy, RSAKey, AuthenticationException
from io import StringIO
from credentials import sshCredentials
import base64


class sshExec():
    def __init__(self, credFn, command):
        self.command = command
        fh=open(credFn,'rb')
        self.sshData = pickle.load(fh)
        fh.close()

        self.key = RSAKey.from_private_key(StringIO(self.sshData.private.decode('utf-8')))
      
    def launch(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            ssh.connect(self.sshData.host, username=self.sshData.userid, pkey=self.key, look_for_keys=False)
        except AuthenticationException:
            sys.stderr.write("Authentication Error\n")
        (stdin, stdout, stderr) = ssh.exec_command(command)
        print(''.join(stdout))
        print(''.join(stderr), file=sys.stderr)
        ssh.close()


if __name__ == "__main__":
    credFn = sys.argv[1]
    command = sys.argv[2]
    cmd = sshExec(credFn, command).launch()
