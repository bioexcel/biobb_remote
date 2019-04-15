#! /usr/bin/python3
""" Command line utility for remote ssh command in biobb_remote"""
__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
from ssh_session import SshSession

ARGPARSER = argparse.ArgumentParser(
    description='SSH command wapper for biobb_remote'
)
ARGPARSER.add_argument(
    dest='command',
    help='Remote command',
    nargs='*'
)
ARGPARSER.add_argument(
    '--keys_path',
    dest='keys_path',
    help='Credentials file path',
    required=True
)

class SshCommand():
    """ Class wrapping ssh_command following biobb_template"""
    def __init__(self, args):
        self.args = args

    def launch(self):
        """ Execute ssh command"""
        session = SshSession(credentials_path=self.args.keys_path)
        (stdin, stdout, stderr) = session.run_command(' '.join(self.args.command))
        print(''.join(stdout))
        print(''.join(stderr), file=sys.stderr)

if __name__ == "__main__":
    args = ARGPARSER.parse_args()
    SshCommand(args).launch()
