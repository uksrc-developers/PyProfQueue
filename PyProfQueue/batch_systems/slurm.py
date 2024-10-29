parameters = {
    'queue_name': 'Slurm',
    'Option_Flag': '#SBATCH',
    'submission_command': 'sbatch',
    'environment_variable':
        {
            'job_array_index': '${SLURM_ARRAY_TASK_ID}',
            'job_id': '${SLURM_JOB_ID}',
            'job_name': '${SLURM_JOB_NAME}',
            'node_list': '${SLURM_JOB_NODELIST}',
            'submit_directory': '${SLURM_SUBMIT_DIR}',
            'submit_host': '${SLURM_SUBMIT_HOST}'
        },
    'option_environment_variable': {'${SLURM_JOB_NAME}': '%x', '${SLURM_JOB_ID}': '%j'},
    'options':
        {
            'account': ['A', 'account'],
            'work_dir': ['D', 'chdir'],
            'cores': ['c', 'cpus-per-task'],        # CPU per Task
            'error_file': ['e'],
            'job_dependency': ['d', 'dependency'],
            'GPUs': ['G', 'gpus'],
            'Generic_resource_list': ['gres'],
            'GPUS_perN': ['gpus-per-node'],
            'job_name': ['J', 'job-name'],
            'event_notification': ['mail-type'],
            'event_email': ['mail-user'],
            'memory': ['mem'],
            'mpc': ['mem-per-cpu'],                 # Memory per CPU
            'nodes': ['N', 'nodes'],
            'n_tasks': ['n', 'ntasks'],
            'tpn': ['ntasks-per-node'],             # Tasks per Node
            'output_file': ['o', 'out'],
            'partition': ['p', 'partition'],
            'time': ['t', 'time'],
            'user': ['uid']
        }
}
