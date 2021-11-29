""" Module to define characteristics of SLURM queue manager"""

import sys

from biobb_remote.task import Task

SLURM_COMMANDS = {
    'submit' : 'sbatch',
    'queue' : 'squeue',
    'cancel': 'scancel'
}

SLURM_CODES = {
    'queue': '-p ', # SLURM queue name.
    'working_dir': '-D ', #Working directory.
    'time': '-t ', #Time of execution in the format days-hours:min:sec
    'job': '-J ', #SLURM Job name.
    'stdout': '-o ', #Job standard output file.
    'stderr': '-e ', #Job standard error file.
    'qos': '--qos=', #Request a quality of service for the job (i.e. the xlong queue)
    'gres': '--gres=', #Generic consumable resources (e.g. 1 GPU --> gpu:titan:1).
    'ntasks': '--ntasks=', # Number of requested MPI processes.
    'cpus-per-task': '--cpus-per-task=', # Number of OpenMP threads per MPI process.
    'ntasks-per-node': '--ntasks-per-node=', #Number of tasks in --ntasks per node.
    'nodes': '--nodes=' # Number of nodes
}

class Slurm(Task):
    """
    | biobb_remote slurm.Slurm
    | Task Class to set specific SLURM settings
    | Extends biobb_remote.task.Task
    
    Args:
        host (str) (Optional): (None) FQD for remote host.
        userid (str) (Optional): (None) Remote user id
        look_for_keys (bool) (Optional): (True) Allow using local user's credentials
    
    """
    def __init__(self, host=None, userid=None, look_for_keys=True):
        Task.__init__(self, host, userid, look_for_keys)
        self.commands = SLURM_COMMANDS

    def _get_queue_settings_string_array(self):
        """
        | Private, Slurm._get_queue_settings_string_array
        | Builds SLURM queue directives array
        
        """
        scr_lines = []

        for key in self.task_data['queue_settings']:
            scr_lines.append(
                '#SBATCH {}{}'.format(
                    SLURM_CODES[key],
                    self.task_data['queue_settings'][key]
                )
            )

        return scr_lines

    def _get_submitted_job_id(self, submit_output):
        """
        | Private: Slurm._get_submitted_job_id
        | Return Slurm job id after submission
        
        Args:
            submit_output (str): Output of the submit command
        """
        wds = submit_output.split(' ')
        return wds[3].strip('\n')
