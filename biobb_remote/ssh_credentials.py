""" Module to generate and manage SSL credentials"""
__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import os
import stat
import pickle
import paramiko
from io import StringIO
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException, RSAKey
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger


class SSHCredentials():
    """ 
    | biobb_remote SSHCredentials
    | Class to generate and manage SSL key-pairs for remote execution.
         
    Args:
        host (str) (Optional): Target host name.
        userid (str) (Optional): Target user id.
        generate_key (bool) (Optional): (False) Generate a pub/private key pair.
        look_for_keys (bool) (Optional): (True) Look for keys in user's .ssh directory if no key provided.
    """
    def __init__(self, host='', userid='', generate_key=False, look_for_keys=True, out_log=None, err_log=None):
        self.host = host
        self.userid = userid
        self.key = None
        self.user_ssh = None
        self.sftp = None
        self.look_for_keys = look_for_keys
        self.remote_auth_keys = []
        if generate_key:
            self.generate_key()
        self.out_log = out_log
        self.err_log = err_log
            
    def _log(self, msg, label='INFO'):
        if label != 'ERROR':
            if self.out_log is not None:
                fu.log(msg, self.out_log)
            else:
                print(f"[{label}] {msg}")
        else:
            if self.err_log is not None:
                fu.log(msg, self.err_log)
            else:
                print(f"[ERROR] {msg}", file=sys.stderr)

    def load_from_file(self, credentials_path, passwd=None):
        """
        | SSHCredentials.load_from_file
        | Recovers SSHCredentials object from disk file.
            
        Args:
            credentials_path (str): Path to packed credentials file.
            passwd (str) (Optional): (None) Use to decrypt private key.
        
        """
        try:
            file = open(credentials_path, 'rb')
            data = pickle.load(file)
        except IOError as err:
            self._log(err, 'ERROR')
            sys.exit()
        self.host = data['host']
        self.userid = data['userid']
        self.look_for_keys = data['look_for_keys']
        self.key = RSAKey.from_private_key(StringIO(data['data'].getvalue()), passwd)

    def load_from_private_key_file(self, private_path, passwd=None):
        """ 
        | SSHCredentials.load_from_private_key_file
        | Loads private key from an standard file.
            
        Args:
            private_path (str): Path to private key file.
            passwd (str) (Optional): (None) Password to decrypt private key.
        """
        try:
            self.key = RSAKey.from_private_key_file(private_path, passwd)
        except IOError as err:
            self._log(err, 'ERROR')
            sys.exit()
        
    def generate_key(self, nbits=2048):
        """ 
        | SSHCredentials.generate_key
        | Generates RSA keys pair
            
        Args:
            nbits (int) (Optional): (2048) Number of bits of the generated key.
        """
        self.key = RSAKey.generate(nbits)
        
    def get_public_key(self, suffix='@biobb'):
        """ 
        | SSHCredentials.get_public_key
        | Returns a readable public key suitable to add to authorized keys.
            
        Args:
            suffix (str) (Optional): (@biobb) Suffix added to the key for identify it.
        """
        if self.key:
            return '{} {} {}{}\n'.format(
                self.key.get_name(), self.key.get_base64(), self.userid, suffix
            )
        else:
            return None

    def get_private_key(self, passwd=None):
        """ 
        | SSHCredentials.get_private_key
        | Returns a readable private key.
            
        Args:
            passwd (str) (Optional): (None) Use passwd to encrypt key.
        """
        if self.key:
            private = StringIO()
            self.key.write_private_key(private, passwd)
            return private.getvalue()
        else:
            return None

    def save(self, output_path, public_key_path=None, private_key_path=None, passwd=None):
        """ 
        | SSHCredentials.save
        | Save packed credentials on external file for re-usage.
            
        Args:
            output_path (str): Path to file  
            public_key_path (str) (Optional): (None) Path to a standard public key file.
            private_key_path (str) (Optional): (None) Path to a standard private key file.
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
        """
        | SSHCredentials.check_host_auth
        | Checks for public_key in remote .ssh/authorized_keys file.
        | Requires users' SSH access to host.
            
        """
        if not self.remote_auth_keys:
            self._get_remote_auth_keys()
        return self.get_public_key() in self.remote_auth_keys

    def install_host_auth(self, file_bck='bck'):
        """ 
        | SSHCredentials.install_host_auth
        | Installs public_key on remote .ssh/authorized_keys file.
        | Requires users' SSH access to host.
            
        Args:
            file_bck (str) (Optional): (bck) Extension to add to backed-up authorized_keys file.
        """
        if not self.check_host_auth():
            if file_bck:
                self._put_remote_auth_keys(file_bck)
                self._log("Previous authorized keys backed up at", ".ssh/authorized_keys." + file_bck)
            self.remote_auth_keys = self.remote_auth_keys + [self.get_public_key()]
            self._put_remote_auth_keys()
            self._log('Biobb Public key installed on host')
        else:
            self._log('Biobb Public key already authorized')

    def remove_host_auth(self, file_bck='biobb'):
        """ 
        | SSHCredentials.remove_host_auth
        | Removes public_key from remote .ssh/authorized_keys file.
        | Requires users' SSH access to host.
            
        Args:
            file_bck (str) (Optional): (biobb) Extension to add to backed-up authorized_keys.
        """
        if self.check_host_auth():
            if file_bck:
                self._put_remote_auth_keys(file_bck)
                self._log("Previous authorized keys backed up at", ".ssh/authorized_keys." + file_bck)
            self.remote_auth_keys = [pkey for pkey in self.remote_auth_keys if pkey != self.get_public_key()]
            self._put_remote_auth_keys()
            self._log("Biobb Public key removed from host")
        else:
            self._log("Biobb Public key not found in remote")
            
#=================================================================================================================
    def _set_user_ssh_session(self, debug=False):
        """ 
        | Private. 
        | Opens a ssh session using user's keys 
            
        Args:
            debug (bool) (Optional): (False) Retrieve debug information from SSH 
        """
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
            self._log(err, 'ERROR')
            sys.exit()

        self.sftp = self.user_ssh.open_sftp()

    def _get_remote_auth_keys(self):
        """ 
        | Private. 
        | Obtains authorized keys on remote
        """
        if not self.sftp:
            self._set_user_ssh_session()

        try:
            with self.sftp.file('.ssh/authorized_keys', mode='r') as ak_file:
                self.remote_auth_keys = ak_file.readlines()
        except IOError:
            self.remote_auth_keys = []

    def _put_remote_auth_keys(self, file_ext=''):
        """ 
        | Private 
        | Adds public_key to remote authorized_keys
        
        Args:
            file_ext (str) (Optional): (No default) file extension for backup of the original file.
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
