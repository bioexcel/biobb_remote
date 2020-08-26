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
        self.user_ssh = None
        self.remote_auth_keys = None
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

    def check_host_auth(self):
        if not self.remote_auth_keys:
            self._get_remote_auth_keys()
        return self.get_public_str() in self.remote_auth_keys
    
    def install_host_auth(self, file_bck='bck'):
        if file_bck:
            self._put_remote_auth_keys(file_bck)
        self.remote_auth_keys = self.remote_auth_keys + [self.get_public_str()]
        self._put_remote_auth_keys()
    
    def remove_host_auth(self, file_bck='biobb'):
        if file_bck:
            self._put_remote_auth_keys(file_bck)
        self.remote_auth_keys = [pkey for pkey in self.remote_auth_keys if pkey != self.get_public_str()]
        self._put_remote_auth_keys()
    
    def _set_user_ssh_session(self, sftp=True):
        self.user_ssh = SSHClient()
        self.user_ssh.set_missing_host_key_policy(AutoAddPolicy())
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        try:
            self.user_ssh.connect(
                self.host,
                username=self.userid,
            )
        except AuthenticationException:
            sys.exit("Authentication Error using user's credentials")

        if sftp:
            self.sftp = self.user_ssh.open_sftp()

    def _get_remote_auth_keys(self):
        if not self.user_ssh:
            self._set_user_ssh_session(sftp=True)
        
        with self.sftp.file('.ssh/authorized_keys', mode='r') as ak_file:
            self.remote_auth_keys = ak_file.readlines()

    def _put_remote_auth_keys(self, file_ext=''):
        if not self.remote_auth_keys:
            return True
    
        if not self.user_ssh:
            self._set_user_ssh_session(sftp=True)
        
        auth_file = '.ssh/authorized_keys'
        if file_ext:
            auth_file += '.' + file_ext
        
        with self.sftp.file(auth_file, 'w') as bck_file:
            bck_file.writelines(self.remote_auth_keys)
        
        return False
        

