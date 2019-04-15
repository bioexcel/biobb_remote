#! /usr/bin/python3

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "gelpi"
__date__ = "$08-March-2019  17:32:38$"

import sys
import argparse
import fileinput
from ssh_session import SshSession

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description='SCP wapper for biobb_remote'
    )
    argparser.add_argument(
        dest='operation',
        help='SCP command',
        choices=['get','put','create']
    )
    argparser.add_argument(
        '--keys_path',
        dest='keys_path',
        help='Credentials file path',
        required=True
    )
    argparser.add_argument(
        '-i',
        dest='input_file_path',
        help='Input file path | input string'
    )
    argparser.add_argument(
        '-o',
        dest='output_file_path',
        help='Output file path',
        required=True
    )
    args = argparser.parse_args()
    if args.input_file_path is None:
        if args.operation != 'create':
            sys.exit("scp_service: error: input_file_path is required ")
        else:
            args.input_file_path=''
            line = sys.stdin.readline()
            while line:
                args.input_file_path += line
                line = sys.stdin.readline()
        
    session = SshSession(credentials_path=args.keys_path)
    session.run_sftp(
        oper=args.operation,
        input_file_path=args.input_file_path, 
        output_file_path=args.output_file_path
    )
