#! /usr/bin/python3

""" Command-line wrapper to SCP for biobb_remote """

__author__ = "gelpi"
__date__ = "$08-March-2019  17:32:38$"

import sys
import argparse

from ssh_session import SshSession

# COMMAND LINE ARGS
ARGPARSER = argparse.ArgumentParser(
    description='SCP wapper for biobb_remote'
)
ARGPARSER.add_argument(
    dest='operation',
    help='SCP command (get|put: Scp standard,'\
        + 'create: creates text file on remote,'\
        + 'file: prints text file on remote)',
    choices=['get', 'put', 'create', 'file']
)
ARGPARSER.add_argument(
    '--keys_path',
    dest='keys_path',
    help='Credentials file path',
    required=True
)
ARGPARSER.add_argument(
    '-i',
    dest='input_file_path',
    help='Input file path | input string'
)
ARGPARSER.add_argument(
    '-o',
    dest='output_file_path',
    help='Output file path'
)

class ScpService():
    """ Class wrapping scp_service following biobb_template"""
    def __init__(self, args):
        self.args = args

    def launch(self):
        """ Executes scp_service"""
        session = SshSession(credentials_path=self.args.keys_path)
        output_text = session.run_sftp(
            oper=self.args.operation,
            input_file_path=self.args.input_file_path,
            output_file_path=self.args.output_file_path
        )
        if self.args.operation == 'file':
            return output_text
        return ''
    

if __name__ == "__main__":
    args = ARGPARSER.parse_args()
    # Chaching stdin
    if args.input_file_path is None:
        if args.operation != 'create':
            sys.exit("scp_service: error: input_file_path is required ")
        else:
            args.input_file_path = ''
            line = sys.stdin.readline()
            while line:
                args.input_file_path += line
                line = sys.stdin.readline()
    if args.output_file_path is None and args.operation != 'file':
        sys.exit("scp_service: error: output_file_path is required ")

    output = ScpService(args).launch()
    if output:
        print(output)
        