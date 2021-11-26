#!/usr/bin/env python
""" Module to handle ssh credentials (userid, host, private_keys) """

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
import os
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException
from biobb_remote.ssh_credentials import SSHCredentials

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
ARGPARSE.add_argument(
   '-v',
   dest="verbose",
   action="store_true",
   help='Output extra information'
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
            if self.args.verbose:
                print("Credentials stored in", self.args.keys_path)
            if self.args.pubkey_path is None:
                print("Public key, add to authorized_keys on remote host")
                print(credentials.get_public_key())
        else:
            credentials = SSHCredentials()
            credentials.load_from_file(self.args.keys_path)

            if self.args.operation == 'get_pubkey':
                print(credentials.get_public_key())

            elif self.args.operation == 'get_private':
                print(credentials.get_private_key())

            elif self.args.operation in ('host_install', 'host_remove', 'host_check'):
                host_str = '{}@{}'.format(credentials.userid, credentials.host)

                if self.args.operation == 'host_check':
                    print('Biobb public key {} at {}'.format(
                        'found' if credentials.check_host_auth() else 'not found',
                        host_str
                    )
                    )
                elif self.args.operation == 'host_install':
                    if not credentials.check_host_auth():
                        credentials.install_host_auth('bck')
                        if self.args.verbose:
                            print('Biobb keys installed on', host_str)
                            print("Warning: original .ssh/authorize_keys file stored as .ssh/authorized_keys.bck")

                elif self.args.operation == 'host_remove':
                    print(credentials.check_host_auth())
                    if credentials.check_host_auth():
                        credentials.remove_host_auth('biobb')
                        if self.args.verbose:
                            print('Biobb removed from ', host_str)
                            print("Warning: .ssh/authorize_keys file stored as .ssh/authorized_keys.biobb")
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
