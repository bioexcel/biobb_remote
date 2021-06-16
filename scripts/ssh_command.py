#!/usr/bin/env python
""" Command line utility for remote ssh command in biobb_remote"""
__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
from biobb_remote.ssh_session import SSHSession

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

class SSHCommand():
    """ Class wrapping ssh_command following biobb_template"""
    def __init__(self, args):
        self.args = args

    def launch(self):
        """ Execute ssh command"""
        session = SSHSession(credentials_path=self.args.keys_path)
        if session:
            stdout, stderr = session.run_command(' '.join(self.args.command))
            print(''.join(stdout))
            print(''.join(stderr), file=sys.stderr)


def main():
    args = ARGPARSER.parse_args()
    SSHCommand(args).launch()

if __name__ == "__main__":
    main()
