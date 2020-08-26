#! /usr/bin/python3
""" Module to handle ssh credentials (userid, host, private_keys) """

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
import os
from biobb_remote.ssh_session import SSHCredentials
import paramiko
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException

ARGPARSE = argparse.ArgumentParser(
    description='Credentials manager for biobb_remote'
)
ARGPARSE.add_argument(
    dest='operation',
    help='Operation: create|get_pubkey',
    choices=['create', 'get_pubkey', 'get_private', 'host_install', 'host_remove', 'host_check']
)
ARGPARSE.add_argument(
    '--user',
    dest='userid',
    help='User id'
)
ARGPARSE.add_argument(
    '--host',
    dest='hostname',
    help='Host name'
)
ARGPARSE.add_argument(
    '--pubkey_path',
    dest='pubkey_path',
    help='Public key file path'
)
ARGPARSE.add_argument(
    '--nbits',
    dest='nbits',
    type=int,
    default=2048,
    help='Number of key bits'
)
ARGPARSE.add_argument(
    '--keys_path',
    dest='keys_path',
    help='Credentials file path',
    required=True
)
ARGPARSE.add_argument(
    '--privkey_path',
    dest='privkey_path',
    help='Private key file path'
)

class Credentials():
    """ Class to wrap credentials management following biobb_template"""
    def __init__(self, line_args):
        self.args = line_args

    def launch(self):
        """ Launch execution following biobb_template"""
        if self.args.operation == 'create':
            credentials = SSHCredentials(
                host=self.args.hostname,
                userid=self.args.userid,
                generate_key=False
            )
            credentials.generate_key(self.args.nbits)
            credentials.save(
                output_path=self.args.keys_path,
                public_key_path=self.args.pubkey_path,
                private_key_path=self.args.privkey_path
            )
            print("Credentials stored in", self.args.keys_path)
            if self.args.pubkey_path is None:
                print("Public key, add to authorized_keys on remote host")
                print(credentials.get_public_str())
        else:
            credentials = SSHCredentials()
            credentials.load_from_file(self.args.keys_path)

            if self.args.operation == 'get_pubkey':
                print(credentials.get_public_str())

            elif self.args.operation == 'get_private':
                print(credentials.get_private())

            elif self.args.operation in ('host_install', 'host_remove', 'host_check'):
                # Opening a ssh session with user's credentials
                user_ssh = SSHClient()
                user_ssh.set_missing_host_key_policy(AutoAddPolicy())
                #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
                try:
                    user_ssh.connect(
                        credentials.host,
                        username=credentials.userid,
                    )
                except AuthenticationException:
                    sys.exit("Authentication Error using user's credentials")

                sftp = user_ssh.open_sftp()
                sftp.chdir('.ssh')

                remote_auth_keys = []

                with sftp.file('authorized_keys', mode='r') as ak_file:
                    remote_auth_keys = ak_file.readlines()

                pub_key = credentials.get_public_str()
                host_str = '{}@{}'.format(credentials.userid, credentials.host)

                if self.args.operation == 'host_check':
                    print('Biobb public key {} at {}'.format(
                        'found' if (pub_key in remote_auth_keys) else 'not found',
                        host_str
                    )
                    )
                else:
                    write_ak_ok = False
                    if self.args.operation == 'host_install' and pub_key not in remote_auth_keys:
                        with sftp.file('authorized_keys.bck', 'w') as bck_file:
                            bck_file.writelines(remote_auth_keys)
                        print("Warning: original .ssh/authorize_keys file stored as .ssh/authorized_keys.bck")

                        new_keys = remote_auth_keys + [pub_key]
                        write_ak_ok = True

                    elif self.args.operation == 'host_remove' and pub_key in remote_auth_keys:
                        with sftp.file('authorized_keys.biobb', 'w') as bck_file:
                            bck_file.writelines(remote_auth_keys)

                        new_keys = [line for line in remote_auth_keys if line != pub_key]
                        print("Warning: .ssh/authorize_keys file stored as .ssh/authorized_keys.biobb")
                        print('Biobb removed from ', host_str)
                        write_ak_ok = True

                    if write_ak_ok:
                        with sftp.file('authorized_keys', mode='w') as ak_file:
                            ak_file.writelines(new_keys)

            else:
                sys.exit("credentials: error: unknown op")

def main():
    args = ARGPARSE.parse_args()

    if args.operation == 'create':
        if args.userid is None or args.hostname is None:
            sys.exit("ssh_command: error: Userid and hostname are required to create credentials")

    Credentials(args).launch()

if __name__ == '__main__':
    main()
