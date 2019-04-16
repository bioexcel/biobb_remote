

from biobb_remote.slurm import Slurm

SETTINGS = {
    'serial': {},
    'serial_full_node':{},
    'openMP': {
        'ntasks': 1,
        'cpus-per-task' : 40,
        'ntasks-per-node' : 1,
        'nodes' : 1,
        'time' : '24:00:00'
        },
    'mpi': {}
}

MODULES = {
    'gromacs': ['impi', 'intel', 'fftw/3.3.8', 'gromacs/2018.0']
}

class SlurmSL1(Slurm):

    def set_modules(self, module_set):
        if module_set in MODULES:
            self.task_data['modules'] = MODULES[module_set]
        else:
            sys_exit('slurm_sl1: error: module set unknown')
            
    def set_settings(self, setting_id):
        if setting_id is None:
            setting_id = 'serial'
        if setting_id in SETTINGS:
            self.task_data['queue_settings'] = SETTINGS[setting_id]

    def get_submitted_job_id(self, submit_output):
        print(submit_output)
        wds = submit_output.split(' ')
        return wds[3]
    