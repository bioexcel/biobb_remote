""" Module to manage ssl credentials and session """
__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import pickle
#import paramiko
from io import StringIO
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException, RSAKey


class sshCredentials():
    """ Generation of ssl credentials for remote execution """
    def __init__(self, host='', userid='', generate_key=False):
        self.host = host
        self.userid = userid
        self.key = None
        if generate_key:
            self.generate()

    def load_from_file(self, credentials_path):
        """ Obtain credentials from file """
        try:
            file = open(credentials_path, 'rb')
            data = pickle.load(file)
        except IOError as err:
            print(err, file=sys.stderr)
            sys.exit()
        self.host = data['host']
        self.userid = data['userid']
        self.key = RSAKey.from_private_key(StringIO(data['data'].getvalue()))

    def generate_key(self, nbits=2048):
        """ Generates new Private Key """
        self.key = RSAKey.generate(nbits)
 
    def get_public_str(self, suffix='@biobb'):
        return '{} {} {}{}\n'.format(
            self.key.get_name(), self.key.get_base64(), self.userid, suffix
        )
    
    def save(self, output_path='', public_key_path=None):
        """ Save packed credentials on external file"""
        if output_path != '':
            with open(output_path, 'wb') as keys_file:
                private = StringIO()
                self.key.write_private_key(private)
                pickle.dump(
                    {
                        'userid': self.userid,
                        'host': self.host,
                        'data': private
                    }, keys_file)
            if public_key_path:
                with open(public_key_path, "w") as pubkey_file:
                    pubkey_file.write(self.get_public_str())

class SshSession():
    def __init__(self, credentials_path):
        self.ssh_data = sshCredentials()
        self.ssh_data.load_from_file(credentials_path)
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            self.ssh.connect(self.ssh_data.host, username=self.ssh_data.userid, pkey=self.ssh_data.key, look_for_keys=False)
        except AuthenticationException:
            print("Authentication Error", file=sys.stderr)
        
    def run_command(self, command):
        return self.ssh.exec_command(command)
    
    def run_sftp(self, oper, input_file_path, output_file_path): 
    
        sftp = self.ssh.open_sftp()
        try:
            if oper == 'get':
                sftp.get(input_file_path, output_file_path)
            elif oper == 'put':
                sftp.put(input_file_path, output_file_path)
            elif oper == 'create':
                remote_fileh = sftp.file(output_file_path, "w")
                remote_fileh.write(input_file_path)
                remote_fileh.close()
            elif oper == 'open':
                return sftp.open(output_file_path)
            else:
                raise
        except IOError as err:
            print(err, file=sys.stderr)

        
