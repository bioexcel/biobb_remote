#!/usr/bin/env python
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
    choices=['submit', 'queue', 'cancel', 'status', 'get_data', 'put_data', 'logs', 'get_file']
)
ARGPARSER.add_argument(
    '--keys_path',
    dest='keys_path',
    help='Credentials file path',
    required=True
)
ARGPARSER.add_argument(
    '--script',
    dest='local_run_script',
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
    dest='queue_settings',
    help='Predefined queue settings'
)
ARGPARSER.add_argument(
    '--modules',
    dest='modules',
    help='Software modules to load'
)
ARGPARSER.add_argument(
    '--task_data_file',
    dest='task_file_path',
    help='Store for task data'
)

ARGPARSER.add_argument(
    '--overwrite',
    dest='overwrite',
    action='store_true',
    help='Overwrite data in output local directory'
)

ARGPARSER.add_argument(
    '--task_file_type',
    dest='task_file_type',
    default='json',
    help='Format for task data file (json, pickle). Default:json'
)

ARGPARSER.add_argument(
    '--poll',
    dest='polling_int',
    default=0,
    type=int,
    help='Polling interval (min), 0: No polling (default)'
)

ARGPARSER.add_argument(
    '--remote_file',
    dest='remote_file',
    help='Remote file name to download (get_file)'
)

class Slurm_test():
    def __init__(self, args):
        self.args = args

    def launch(self):
        slurm_task = Slurm()
        slurm_task.set_credentials(self.args.keys_path)

        if self.args.command not in ('queue', 'submit'):
            try:
                slurm_task.load_data_from_file(self.args.task_file_path)
                print("Task data loaded from", self.args.task_file_path)
            except IOError:
                print("Task data not loaded")

        if self.args.command == 'submit':
            slurm_task.set_local_data_bundle(self.args.local_data_path)
            if 'input_data_loaded' not in slurm_task.task_data:
                slurm_task.send_input_data(self.args.remote_path)
            slurm_task.submit(self.args.queue_settings, self.args.modules, self.args.local_run_script)
            print("job id", slurm_task.task_data['remote_job_id'])

        elif self.args.command == 'cancel':
            slurm_task.cancel(remove_data=True)
            print('job ' + slurm_task.task_data['remote_job_id'] + '  cancelled')

        elif self.args.command == 'queue':
            stdout, stderr = slurm_task.check_queue()
            print(''.join(stdout))
            print(''.join(stderr), file=sys.stderr)

        elif self.args.command == 'status':
            slurm_task.check_job()

        elif self.args.command == 'get_data':
            slurm_task.get_output_data(self.args.local_data_path, False)

        elif self.args.command == 'put_data':
            slurm_task.set_local_data_bundle(self.args.local_data_path)
            slurm_task.send_input_data(self.args.remote_path)

        elif self.args.command == 'logs':
            stdout, stderr = slurm_task.get_logs()
            print("Job Output log")
            print(stdout)
            print("Jog Error log")
            print(stderr)

        elif self.args.command == 'get_file':
            print(slurm_task.get_remote_file(self.args.remote_file))

        else:
            sys.exit("test_slurm: error: unknown command " + self.args.command)

        if slurm_task.modified:
            if not self.args.task_file_path:
                self.args.task_file_path = slurm_task.id + ".task"
            try:
                slurm_task.save(self.args.task_file_path)
                print("Task data saved on", self.args.task_file_path)
            except IOError as e:
                sys.exit(e)

def main():
    args = ARGPARSER.parse_args()
    stest = Slurm_test(args).launch()

if __name__ == '__main__':
    main()
