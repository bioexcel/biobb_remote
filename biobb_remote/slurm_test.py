#!/usr/bin/python3
""" Test script for slurm remote interface """

import sys
import argparse
from biobb_remote.slurm import Slurm

ARGPARSER = argparse.ArgumentParser(
    description='Test Slurm script for biobb_remote'
)
ARGPARSER.add_argument(
    dest='command',
    help='Remote command',
    choices=['submit', 'queue', 'cancel', 'status', 'get_data', 'put_data']
)
ARGPARSER.add_argument(
    '--keys_path',
    dest='keys_path',
    help='Credentials file path',
    required=True
)
ARGPARSER.add_argument(
    '--script',
    dest='script_path',
    help='Path to local script'
)
ARGPARSER.add_argument(
    '--local_data',
    dest='local_data_path',
    help='Local data bundle'
)
ARGPARSER.add_argument(
    '--remote',
    dest='remote_path',
    help='Remote working dir'
)
ARGPARSER.add_argument(
    '--queue_settings',
    dest='q_settings',
    help='Predefined queue settings'
)
ARGPARSER.add_argument(
    '--module',
    dest='module',
    help='Software module to load'
)
ARGPARSER.add_argument(
    '--task_data',
    dest='task_file_path',
    help='Store for task data'
)


class Slurm_test():
    def __init__(self, args):
        self.args = args

    def launch(self):
        slurm_task = Slurm()
        slurm_task.set_credentials(self.args.keys_path)

        if self.args.command != 'queue':
            try:
                slurm_task.load_data_from_file(self.args.task_file_path)
                print("Task data loaded from", self.args.task_file_path)
            except IOError:
                print("Task data not loaded")

        if self.args.command == 'submit':
            slurm_task.set_settings(self.args.q_settings)
            slurm_task.set_modules(self.args.module)
            slurm_task.set_local_data(self.args.local_data_path)
            if not slurm_task.task_data['loaded']:
                slurm_task.task_data['remote_base_path'] = self.args.remote_path
                slurm_task.task_data['script'] = self.args.script_path
                slurm_task.send_input_data()
            slurm_task.submit()
            print("job id", slurm_task.task_data['remote_job_id'])
        elif self.args.command == 'cancel':
            print("TODO:cancel job")
        elif self.args.command == 'queue':
            (stdin, stdout, stderr) = slurm_task.check_queue()
            print(''.join(stdout))
            print(''.join(stderr), file=sys.stderr)

        elif self.args.command == 'status':
            (stdin, stdout, stderr) = slurm_task.check_job()
            print(''.join(stdout))
            print(''.join(stderr), file=sys.stderr)

        elif self.args.command == 'get_data':
            if not slurm_task.task_data:
                slurm_task.set_local_data(self.args.local_data_path)
                slurm_task.task_data['remote_base_path'] = self.args.remote_path
            print("TODO: get output data")
        elif self.args.command == 'put_data':
            if not slurm_task.task_data:
                slurm_task.set_local_data(self.args.local_data_path)
                slurm_task.task_data['remote_base_path'] = self.args.remote_path
            slurm_task.send_input_data()
            slurm_task.modified = True

        else:
            sys.exit("test_slurm: error: unknown command " + self.args.command)

        if slurm_task.modified:
            try:
                slurm_task.save(args.task_file_path)
                print("Task data saved on", args.task_file_path)
            except IOError as e:
                sys.exit(e)
def main():
    args = ARGPARSER.parse_args()
    stest = Slurm_test(args).launch()

if __name__ == '__main__':
    main()
