#! /usr/bin/python3

__author__ = "gelpi"
__date__ = "$08-March-2019 17:32:38$"

import sys
import argparse
from ssh_session import SshSession

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description='SSH command wapper for biobb_remote'
    )
    argparser.add_argument(
        dest='command',
        help='Remote command',
        nargs='*'
    )
    argparser.add_argument(
        '--keys_path',
        dest='keys_path',
        help='Credentials file path',
        required=True
    )
    args = argparser.parse_args()
    
    session = SshSession(credentials_path=args.keys_path)
    (stdin, stdout, stderr) = session.run_command(' '.join(args.command))
    print(''.join(stdout))
    print(''.join(stderr), file=sys.stderr)
