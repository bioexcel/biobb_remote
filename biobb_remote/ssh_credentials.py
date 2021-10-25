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
    """ Generation of ssl credentials for remote execution
        Args 
            * host (str): Target host name
            * userid (str): Target user id
            * generate_key (bool): Generate a pub/private key pair
            * look_for_keys (bool): Look for keys in user's .ssh directory if no key provided
    """
    def __init__(self, host='', userid='', generate_key=False, look_for_keys=True):
        self.host = host
        self.userid = userid
        self.key = None
        self.user_ssh = None
        self.sftp = None
        self.look_for_keys = look_for_keys
        self.remote_auth_keys = []
        if generate_key:
            self.generate_key()

    def load_from_file(self, credentials_path, passwd=None):
        """ Recovers SSHCredentials object from disk file
            * credentials_path (**str**): Path to packed credentials file.
            * passwd (**str**): Use to decrypt private key
        """
        try:
            file = open(credentials_path, 'rb')
            data = pickle.load(file)
        except IOError as err:
            sys.exit(err)
        self.host = data['host']
        self.userid = data['userid']
        self.look_for_keys = data['look_for_keys']
        self.key = RSAKey.from_private_key(StringIO(data['data'].getvalue()), passwd)

    def load_from_private_key_file(self, private_path, passwd=None):
        """ Loads private key from standard file
            * private_path(**str**): Path to private key file
            * passwd(**str**): Password to decrypt private key (optional)
        """
        try:
            self.key = RSAKey.from_private_key_file(private_path, passwd)
        except IOError as err:
            sys.exit(err)
        
    def generate_key(self, nbits=2048):
        """ Generates RSA keys pair
            * nbits (**int**): number of bits the generated key
        """
        self.key=RSAKey.generate(nbits)
        
    def get_public_key(self, suffix='@biobb'):
        """ Returns a readable public key suitable to add to authorized keys
            * suffix (**str**): Added to the key for identify it.
        """
        if self.key:
            return '{} {} {}{}\n'.format(
                self.key.get_name(), self.key.get_base64(), self.userid, suffix
            )
        else:
            return None

    def get_private_key(self, passwd=None):
        """ Return a readable private key
            * passwd (**str**): Use passwd to encrypt key
        """
        if self.key:
            private = StringIO()
            self.key.write_private_key(private, passwd)
            return private.getvalue()
        else:
            return None

    def save(self, output_path, public_key_path=None, private_key_path=None, passwd=None):
        """ Save packed credentials on external file for re-usage
            * output_path (**str**): Path to file  
            * public_key_path (**str**): Path to a standard public key file
            * private_key_path (**str**): Path to a standard private key file
        """
        with open(output_path, 'wb') as keys_file:
            private = StringIO()
            if self.key:
                self.key.write_private_key(private)
            pickle.dump(
                {
                    'userid': self.userid,
                    'host': self.host,
                    'data': private,
                    'look_for_keys': self.look_for_keys
                }, keys_file)
        if public_key_path:
            with open(public_key_path, 'w') as pubkey_file:
                pubkey_file.write(self.get_public_key())
        if private_key_path:
            with open(private_key_path, 'w') as privkey_file:
                privkey_file.write(self.get_private_key(passwd))
            os.chmod(private_key_path, stat.S_IREAD + stat.S_IWRITE)

    def check_host_auth(self):
        """ Check for public_key in remote .ssh/authorized_keys file
            Requires users' SSH access to host
        """
        if not self.remote_auth_keys:
            self._get_remote_auth_keys()
        return self.get_public_key() in self.remote_auth_keys

    def install_host_auth(self, file_bck='bck'):
        """ Installs public_key on remote .ssh/authorized_keys file
            Requires users' SSH access to host
        """
        if not self.check_host_auth():
            if file_bck:
                self._put_remote_auth_keys(file_bck)
                print("Previous authorized keys backed up at", ".ssh/authorized_keys." + file_bck)
            self.remote_auth_keys = self.remote_auth_keys + [self.get_public_key()]
            self._put_remote_auth_keys()
            print('Biobb Public key installed on host')
        else:
            print('Biobb Public key already authorized')

    def remove_host_auth(self, file_bck='biobb'):
        """ Removes public_key from remote .ssh/authorized_keys file
            Requires users' SSH access to host
        """
        if self.check_host_auth():
            if file_bck:
                self._put_remote_auth_keys(file_bck)
                print("Previous authorized keys backed up at", ".ssh/authorized_keys." + file_bck)
            self.remote_auth_keys = [pkey for pkey in self.remote_auth_keys if pkey != self.get_public_key()]
            self._put_remote_auth_keys()
            print("Biobb Public key removed from host")
        else:
            print("Biobb Public key not found in remote")

    def _set_user_ssh_session(self, debug=False):
        """ Internal. Opens a ssh session using user's keys """
        self.user_ssh = SSHClient()
        self.user_ssh.set_missing_host_key_policy(AutoAddPolicy())
        
        if debug:
            paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        
        try:
            self.user_ssh.connect(
                self.host,
                username=self.userid,
            )
        except AuthenticationException as err:
            sys.exit(err)

        self.sftp = self.user_ssh.open_sftp()

    def _get_remote_auth_keys(self):
        """ Internal. Obtains authorized keys on remote """
        if not self.sftp:
            self._set_user_ssh_session()

        try:
            with self.sftp.file('.ssh/authorized_keys', mode='r') as ak_file:
                self.remote_auth_keys = ak_file.readlines()
        except IOError:
            self.remote_auth_keys = []

    def _put_remote_auth_keys(self, file_ext=''):
        """ Internal: Adds public_key to remote authorized_keys
            * file_ext: optional file extension for backup of the original file
        """
        if not self.remote_auth_keys:
            return True

        if not self.sftp:
            self._set_user_ssh_session()

        auth_file = '.ssh/authorized_keys'
        if file_ext:
            auth_file += '.' + file_ext

        with self.sftp.file(auth_file, 'w') as bck_file:
            bck_file.writelines(self.remote_auth_keys)

        return False
