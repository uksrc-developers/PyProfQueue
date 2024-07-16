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
            'user': ['uid'],
            'account': ['A', 'account'],
            'partition': ['p', 'partition'],
            'job_name': ['J', 'job-name'],
            'job_dependency': ['depend'],
            'work_dir': ['D', 'chdir'],
            'output_file': ['o', 'out'],
            'error_file': ['e'],
            'event_notification': ['mail-type'],
            'event_email': ['mail-user'],
            'nodes': ['N', 'nodes'],
            'cores': ['c', 'cpus-per-task'],          # CPU per Task
            'memory': ['mem'],
            'tpn': ['ntasks-per-node'],             # Tasks per Node
            'mpc': ['mem-per-cpu'],                 # Memory per CPU
            'n_tasks': ['n', 'ntasks'],
            'time': ['t', 'time']
        }
}
