#! /usr/bin/python3
""" Module to handle ssh credentials (userid, host, private_keys) """

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
from ssh_session import SshCredentials

ARGPARSE = argparse.ArgumentParser(
    description='Credentials manager for biobb_remote'
)
ARGPARSE.add_argument(
    dest='operation',
    help='Operation: create|get_pubkey',
    choices=['create', 'get_pubkey', 'get_private']
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
            credentials = SshCredentials(
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
            print("Credentials stored in", args.keys_path)
            if self.args.pubkey_path is None:
                print("Public key, add to authorized_keys on remote host")
                print(credentials.get_public_str())

        else:
            credentials = SshCredentials()
            credentials.load_from_file(self.args.keys_path)
            if self.args.operation == 'get_pubkey':
                print(credentials.get_public_str())
            elif self.args.operation == 'get_private':
                print(credentials.get_private())
            else:
                sys.exit("credentials: error: unknown op")

if __name__ == "__main__":

    args = ARGPARSE.parse_args()

    if args.operation == 'create':
        if args.userid is None or args.hostname is None:
            sys.exit("ssh_command: error: Userid and hostname are required to create credentials")

    Credentials(args).launch()
