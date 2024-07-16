parameters = {
    'queue_name': 'PBS',
    'Option_Flag': '#PBS',
    'submission_command': 'qsub',
    'environment_variable':
        {
            'job_array_index': '${PBS_ARRAYID}',
            'job_id': '${PBS_JOBID}',
            'job_name': '${PBS_JOBNAME}',
            'node_list': '${PBS_NODEFILE}',
            'submit_directory': '${PBS_O_WORKDIR}',
            'submit_host': '${PBS_O_HOST}'
        },
    'option_prefixes': ['l', 'm'],
    'options':
        {
            'user': ['P'],
            'account': ['A'],
            'partition': ['q'],
            'job_name': ['J', 'job-name'],
            'job_dependency': ['d'],
            'work_dir': ['D', 'chdir'],
            'output_file': ['o'],
            'error_file': ['e'],
            'event_notification': ['m abe'],
            'event_email': ['M'],
            'nodes': ['l nodes'],
            'cores': ['l ncpus'],
            'memory': ['l mem'],
            'tpn': ['l mppnppn'],             # Tasks per Node
            'n_tasks': ['l ppn', 'l mppwidth'],
            'time': ['l walltime'],
            'cpu_time': ['l cput']
        }
}
