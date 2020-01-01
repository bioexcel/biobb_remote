""" Task adjusted to SLURM manager"""

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

QSETTINGS = {
    'sl1.bsc.es': {
        'serial': {
            'ntasks': 1,
            'cpus-per-task' : 1,
            'time' : '3-00:00:00'
        },
        'serial_full_node':{
            'ntasks': 1,
            'cpus-per-task' : 1,
            'ntasks-per-node': 1,
            'time' : '3-00:00:00'
        },
        'openMP_full_node': {
            'ntasks': 1,
            'cpus-per-task' : 40,
            'ntasks-per-node' : 1,
            'nodes' : 1,
            'time' : '3-00:00:00'
            },
        'mpi_only_node': {
            'ntasks': 40,
            'cpus-per-task':1,
            'ntasks-per-node': 40,
            'nodes': 1,
            'time' : '3-00:00:00'
        },
        'mpi_8_nodes': {
            'ntasks': 320,
            'cpus-per-task':1,
            'ntasks-per-node': 40,
            'nodes': 8,
            'time' : '3-00:00:00'
        },
        'default' : 'openMP_full_node'
    }
}

MODULES = {
    'sl1.bsc.es': {
        'gromacs': ['impi', 'intel', 'fftw/3.3.8', 'gromacs/2018.0']
    }
}

class Slurm(Task):
    def __init__(self):
        Task.__init__(self)
        self.commands = SLURM_COMMANDS

    def set_modules(self, host, module_set):
        if module_set in MODULES[host]:
            self.task_data['modules'] = MODULES[host][module_set]
        else:
            sys.exit('slurm: error: module set unknown')

    def set_settings(self, host, setting_id='default'):
        if setting_id is None:
            setting_id = 'serial'
        if setting_id == 'default':
            self.task_data['queue_settings'] = QSETTINGS[host][QSETTINGS[host]['default']]
        else:
            self.task_data['queue_settings'] = QSETTINGS[host][setting_id]

    def get_queue_settings_string_array(self):
        scr_lines = []
        for key in self.task_data['queue_settings']:
            scr_lines.append(
                '#SBATCH {}{}'.format(
                    SLURM_CODES[key],
                    self.task_data['queue_settings'][key]
                )
            )
        return scr_lines

    def get_submitted_job_id(self, submit_output):
        wds = submit_output.split(' ')
        return wds[3].strip('\n')
