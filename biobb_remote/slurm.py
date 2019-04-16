

from biobb_remote.task import Task
from biobb_remote.ssh_session import SSHSession

COMMANDS = {
    'submit' : 'sbatch',
    'queue' : 'squeue',
    'cancel': 'scancel'
}

SLURM_CODES = {
    'job': '-J ',
    'stdout': '-o ',
    'stderr': '-e ',
    'working_dir' : '-D ',
    'ntasks': '--ntasks=',
    'cpus-per-task': '--cpus-per-task=',
    'ntasks-per-node': '--ntasks-per-node=',
    'nodes': '--nodes=',
    'time': '-t '
}

class Slurm(Task):
    def __init__(self):
        Task.__init__(self)
        self.commands = COMMANDS
        
    def get_queue_settings_ar(self):
        scr_lines = []
        for key in self.task_data['queue_settings']:
            scr_lines.append(
                '#SBATCH {}{}'.format(
                    SLURM_CODES[key],
                    self.task_data['queue_settings'][key]
                )
            )
        return scr_lines
    
    