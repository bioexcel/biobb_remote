""" Module to manage ssl credentials and session """
__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import os
import stat
import pickle
import paramiko
from io import StringIO
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException, RSAKey


class SSHCredentials():
    """ Generation of ssl credentials for remote execution """
    def __init__(self, host='', userid='', generate_key=False):
        self.host = host
        self.userid = userid
        self.key = None
        if generate_key:
            self.generate_key()

    def load_from_file(self, credentials_path):
        """ Obtain credentials from file """
        try:
            file = open(credentials_path, 'rb')
            data = pickle.load(file)
        except IOError as err:
            sys.exit(err)
        self.host = data['host']
        self.userid = data['userid']
        self.key = RSAKey.from_private_key(StringIO(data['data'].getvalue()))

    def generate_key(self, nbits=2048):
        """ Generates new Private Key """
        self.key = RSAKey.generate(nbits)

    def get_public_str(self, suffix='@biobb'):
        """ Returns a readable public key suitable to add to authorized_keys """
        return '{} {} {}{}\n'.format(
            self.key.get_name(), self.key.get_base64(), self.userid, suffix
        )
    def get_private(self):
        """ Return a readable private key"""
        private = StringIO()
        self.key.write_private_key(private)
        return private.getvalue()

    def save(self, output_path='', public_key_path=None, private_key_path=None):
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
                with open(public_key_path, 'w') as pubkey_file:
                    pubkey_file.write(self.get_public_str())
            if private_key_path:
                with open(private_key_path, 'w') as privkey_file:
                    privkey_file.write(self.get_private())
                os.chmod(private_key_path, stat.S_IREAD + stat.S_IWRITE)

class SSHSession():
    """ Class wrapping ssh operations """
    def __init__(self, ssh_data=None, credentials_path=None):
        if ssh_data is None:
            self.ssh_data = SSHCredentials(credentials_path is None)
            if credentials_path:
                self.ssh_data.load_from_file(credentials_path)
        else:
            self.ssh_data = ssh_data
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            self.ssh.connect(
                self.ssh_data.host,
                username=self.ssh_data.userid,
                pkey=self.ssh_data.key,
                look_for_keys=False
            )
        except AuthenticationException:
            sys.exit("Authentication Error")

    def run_command(self, command):
        """ Runs SSH command on remote"""
        if self.ssh:
            stdin, stdout, stderr = self.ssh.exec_command(command)
        return ''.join(stdout), ''.join(stderr)


    def run_sftp(self, oper, input_file_path, output_file_path=''):
        """ Runs SFTP session on remote"""
        sftp = self.ssh.open_sftp()
        try:
            if oper == 'get':
                sftp.get(input_file_path, output_file_path)
            elif oper == 'put':
                sftp.put(input_file_path, output_file_path)
            elif oper == 'create':
                with sftp.file(output_file_path, "w") as remote_fileh:
                    remote_fileh.write(input_file_path)
            elif oper == 'open':
                return sftp.open(output_file_path)
            elif oper == 'file':
                with sftp.file(input_file_path, "r") as remote_file:
                    return remote_file.read().decode()
            elif oper == "listdir":
                return sftp.listdir(input_file_path)
            else:
                print('Unknown sftp command', oper)
                return True
        #TODO check appropriate errors
        except IOError as err:
            sys.exit(err)
        return False
