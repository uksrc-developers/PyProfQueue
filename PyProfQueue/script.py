# Built in Modules
from importlib import resources as impresources
import itertools
import sys
# Local package imports
from . import data


class Script:
    """
        Bash class to read existing bash scripts, pull out the options and create new file to be submitted so the
        work in the script gets profiled.

        Parameters to initiate
        ----------
        queue_system : str
            str of the queue system to be used. [sbatch, torque]
        work_script : str
            str of the path and name of the original bash script to be profiled
        read_queue_system : str = None
            str of the queue system that the work_script was written for, if not specified it is assumed
            it is the same as queue_system. [sbatch, torque]
        queue_options : dict = None
            dictionary of options to be passed to the queue system.
        likwid : bool = False
            bool determining if likwid should be used to measure the performance such that a roofline
            model can be plotted
        likwid_req: list = None
            list of the required lines that need to be added to a bash script in order to allow likwid
            to be used. For example, lines that load the likwid module if modules is being used on the
            system.
        prometheus : bool = False
            bool determining if prometheus should be used to measure the metrics of the node on which
            the script is being run.
        prometheus_req: list = None
            list of the required lines that need to be added to a bash script in order to allow prometheus
            to be used. In order to run prometheus this list will need at least one entry:
                'export PROMETHEUS_SOFTWARE=<path to the Prometheus software to be used>'
            with an optional entry to change the python executable to use by declaring:
                'export PROMETHEUS_PYTHON=<path to the Python version to be used to scrape the prometheus database>'
            any additional entries will be added, but are at users discretion

        Notes
        -----
        The Script class is intended to manage the components necessary in order to take an existing bash script,
        extract any options for a queue system it has, add any desired options, and initiate the information needed
        for prometheus and likwid to perform their metric collections. This object can then be passed on to the
        submit() function in order to create the profiling bash script and submit it to the queue that it is
        designed to be submitted to.

        Adding new queue systems
        -----
        To add a new queue system, go to the sections marked Queue System specifics {1}, {2}, {3} and {4} in order to
        follow the instructions there

        Examples
        -------- # As of now this example doesn't apply to this class.
        #>>> from PyProfQueue.script import Script
        #>>> ProfileScript = Script(queue_system='slurm',
                                    work_script='./example.sh',
                                    read_queue_system='slurm',
                                    likwid=True,
                                    likwid_req=['module load oneAPI_comp',
                                                'module load likwid'],
                                    prometheus=True,
                                    prometheus_req=['export PROMETHEUS_SOFTWARE=~/Software/prometheus'],
                                    queue_options={'user': 'user_name'})
    """
    def __init__(self, queue_system: str,
                 work_script: str,
                 read_queue_system: str = None,
                 queue_options: dict = None,
                 likwid: bool = False, likwid_req: list = None,
                 prometheus: bool = False, prometheus_req: list = None):
        if True: # If statement added to allow for the collapse of the initiation of variables
            self.queue_system = queue_system
            self.work_script = work_script
            self.tmp_work_script = None
            self.tmp_profile_script = None
            self.works = None
            self.work_dir = None
            self.likwid = likwid
            self.likwid_file = None
            self.likwid_initEndSplit = None
            self.likwid_req = None
            self.prometheus = prometheus
            self.prometheus_file = None
            self.prometheus_initEndSplit = None
            self.prometheus_location = None
            self.read_queue_system = read_queue_system

        if self.likwid:
            self.add_likwid(likwid_req)
        if self.prometheus:
            self.add_prometheus(prometheus_req)

        if bool(queue_options):
            self.obj_options = self.Options(queue_options)
        else:
            self.obj_options = self.Options()

        # Queue System specifics {1}
        '''
        -----
        To add a new queue system, this section needs two cases to be added.
        - First, add one to 'match self.queue_system'
            with the following:
            case '<queue name>'
                self.option_start = '<Format of how to declare queue options>'
                self.submission = '<terminal command to submit scripts>'
                job_name = '<Variable to give Job Name>'
                job_id = '<Variable to give Job ID>'
        
        - Second, add a case to 'match self.read_queue_system' with the format of:
            case '<queue name>'
                self.read_option_start = '<Format of how to read queue options>'
                options = self.option_pass()
                self.obj_options.<OBJ Option function name for this queue>_options(options)
                self.outputvariable_convert(job_directory)
        
        Template 1:
        =====
        case '<queue_name>':
            self.option_start = ''
            job_name = '${}'
            job_id = '${}'
        =====
        Template 2:
        =====
        case '<queue_name>':
            self.read_option_start = ''
            read_job_name = '${}'
            read_job_id = '${}'
            options = self.option_pass()
            self.obj_options.<queue_name>_options(options)
            self.outputvariable_convert(job_name, job_id, read_job_name, read_job_id)
        =====
        -----
        '''
        # ==========================
        match self.queue_system:
            case 'slurm':
                self.option_start = '#SBATCH '
                self.submission = 'sbatch'
            case 'torque':
                self.option_start = '#PBS '
                self.submission = 'qsub'
            case None:
                if queue_options is None:

                    print("No queue system was selected, therefore only queue_options['workdir'] is needed.")

            case _:
                exit('No queue system chosen')

        match self.read_queue_system:
            case 'slurm':
                self.read_option_start = '#SBATCH '
                options = self.option_pass()
                self.obj_options.slurm_options(options)
                self.outputvariable_convert()
            case 'torque':
                self.read_option_start = '#PBS '
                options = self.option_pass()
                self.obj_options.torque_options(options)
                self.outputvariable_convert()
            case None:
                if self.queue_system is None:
                    if self.obj_options.workdir is None:
                        self.obj_options.workdir = './'
                elif queue_options is None:
                    exit('"read_queue_system" was left as None, but no queue options were provided with "queue_options"')
                else:
                    self.outputvariable_convert()

            case _:
                exit('Provided queue system, {}, is not supported in the initialisation '
                     '"match self.read_queue_system"'.format(self.read_queue_system))
        # ==========================
        self.obj_options.remove_empty_options()

    def add_likwid(self, likwid_req):
        self.likwid = True
        self.likwid_file = impresources.files(data) / "likwid_commands.txt"
        self.likwid_initEndSplit = -1
        self.likwid_req = likwid_req

    def add_prometheus(self, prometheus_req):
        contains_ps = False
        contains_pp = False
        for req in prometheus_req:
            if 'PROMETHEUS_SOFTWARE' in req:
                contains_ps = True
                continue
            if 'PROMETHEUS_PYTHON' in req:
                contains_pp = True
                continue
            else:
                prometheus_req += ['export PROMETHEUS_PYTHON={}'.format(sys.executable)]
                contains_pp = True
                continue
        if not contains_pp:
            prometheus_req += ['export PROMETHEUS_PYTHON={}'.format(sys.executable)]
            contains_pp = True

        if not contains_ps or not contains_pp:
            exit('When requesting prometheus profiling, prometheus_req must include "export PROMETHEUS_SOFTWARE=".')
        self.prometheus = True
        self.prometheus_file = impresources.files(data) / "prometheus_commands.txt"
        self.prometheus_initEndSplit = -1
        self.prometheus_req = prometheus_req

    def option_pass(self):
        options, self.works = self.read_script()
        return options

    # Queue System specifics {2}
    '''
    -----
    To add a new queue system, this section needs two things. First, a new case has to be created which handles a 
    file using the new queue system being read in, which then needs a nested case to translate the output variable
    to all other queue system formats to handle a file being written out. Second, the nested case of all older 
    queue system need to have a new case added to them that handles how to translate reading the output variable from
    the old queue system to the new queue system.
    
    To demonstrate the meaning we look at slurm to torque
    Example:
    #####
    If we read in a slurm script but want to output a torque script, then the output variable defined through:
        #SBATCH -o ./%x.%j.out
    where %x is how slurm states ${SLURM_JOB_NAME} in the option section and %j is how slurm states ${SLURM_JOB_ID} in 
    the option section, would need to become:
        #PBS -o ./${PBS_JOBNAME}.${PBS_JOBID}.out
    While the same is true in reverse, it only applies to the formating of the option declaration, in the script itself
    slurm needs to use ${SLURM_JOB_NAME} or ${SLURM_JOB_ID} for %x and %j respectively.
    #####
    Template for new read_queue_system case:
    =====
    case '<queue_name>':
        match self.queue_system:
            case 'slurm':
                self.obj_options.output = self.obj_options.output\
                    .replace('<Job_Name_Variable>', '%x')\
                    .replace('<Job_ID_Variable>', '%j')
                if self.obj_options.workdir is not None:
                    self.work_dir = self.obj_options.workdir\
                        .replace('%x', '${SLURM_JOB_NAME}')\
                        .replace('%j', '${SLURM_JOB_ID}')
                else:
                    self.work_dir = self.obj_options.output[:-4]\
                        .replace('%x', '<Job_Name_Variable>')\
                        .replace('%j', '<Job_ID_Variable>')
            case 'torque':
                self.obj_options.output = self.obj_options.output \
                    .replace('<Job_Name_Variable>', '${PBS_JOBNAME}') \
                    .replace('<Job_ID_Variable>', '${PBS_JOBID}')
                if self.obj_options.workdir is not None:
                    self.work_dir = self.obj_options.workdir
                else:
                    self.work_dir = self.obj_options.output[:-4]
            case '<queue_name>':
                # if the new queue system doesn't have special formats for designating Job_Name and Job_ID in options
                # like slurm does, use this:
                if self.obj_options.workdir is not None:
                    self.work_dir = self.obj_options.workdir
                else:
                    self.work_dir = self.obj_options.output[:-4]
                # if, like slurm, it has a special option only format for Job_Name and Job_ID use:
                self.obj_options.output = self.obj_options.output\
                    .replace('<Script_Job_Name_Variable>', '<Option_Job_Name_Variable>')\
                    .replace('<Script_Job_ID_Variable>', '<Option_Job_ID_Variable>')
                if self.obj_options.workdir is not None:
                    self.work_dir = self.obj_options.workdir\
                        .replace('<Script_Job_Name_Variable>', '<Option_Job_Name_Variable>')\
                        .replace('<Script_Job_ID_Variable>', '<Option_Job_ID_Variable>')
                else:
                    self.work_dir = self.obj_options.output[:-4]\
                        .replace('<Script_Job_Name_Variable>', '<Option_Job_Name_Variable>')\
                        .replace('<Script_Job_ID_Variable>', '<Option_Job_ID_Variable>')
            case None:
                pass
            case _:
                exit('queue_system was unknown  when translating from <queue_name> to {}'.format(self.queue_system))
    =====
    Template for the nested case in old queue systems:
    =====
    # For Slurm
    case '<queue_name>':
        self.obj_options.output = self.obj_options.output.replace('%x.%j', <'<special format>' or job_directory>)
        working_dir = self.obj_options.output[:-4].replace('<special format>', job_directory)
    # For systems like Torque that don't have special formating in the option section
    case '<queue_name>':
        self.obj_options.output = self.obj_options.output.replace(job_directory, <'<special format>' or job_directory>)
        working_dir = self.obj_options.output[:-4]
    =====
    -----
    '''
    # ==========================
    def outputvariable_convert(self):
        match self.read_queue_system:
            case 'slurm':
                match self.queue_system:
                    case 'slurm':
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir\
                                .replace('%x', '${SLURM_JOB_NAME}')\
                                .replace('%j', '${SLURM_JOB_ID}')
                        else:
                            self.work_dir = self.obj_options.output[:-4]\
                                .replace('%x', '${SLURM_JOB_NAME}')\
                                .replace('%j', '${SLURM_JOB_ID}')
                    case 'torque':
                        self.obj_options.output = self.obj_options.output \
                            .replace('%x', '${PBS_JOBNAME}') \
                            .replace('%j', '${PBS_JOBID}')
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir
                        else:
                            self.work_dir = self.obj_options.output[:-4]
                    case None:
                        pass
                    case _:
                        exit('queue_system was unknown when translating from slurm to {}'.format(self.queue_system))
            case 'torque':
                match self.queue_system:
                    case 'slurm':
                        self.obj_options.output = self.obj_options.output\
                            .replace('${PBS_JOBNAME}', '%x')\
                            .replace('${PBS_JOBID}', '%j')
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir\
                                .replace('%x', '${SLURM_JOB_NAME}')\
                                .replace('%j', '${SLURM_JOB_ID}')
                        else:
                            self.work_dir = self.obj_options.output[:-4]\
                                .replace('%x', '${SLURM_JOB_NAME}')\
                                .replace('%j', '${SLURM_JOB_ID}')
                    case 'torque':
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir
                        else:
                            self.work_dir = self.obj_options.output[:-4]
                    case None:
                        pass
                    case _:
                        exit('queue_system was unknown when translating from torque to {}'.format(self.queue_system))
            case None:
                match self.queue_system:
                    case 'slurm':
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir\
                                .replace('%x', '${SLURM_JOB_NAME}')\
                                .replace('%j', '${SLURM_JOB_ID}')
                        else:
                            self.work_dir = self.obj_options.output[:-4] \
                                .replace('%x', '${SLURM_JOB_NAME}') \
                                .replace('%j', '${SLURM_JOB_ID}')
                    case 'torque':
                        if self.obj_options.workdir is not None:
                            self.work_dir = self.obj_options.workdir
                        else:
                            self.work_dir = self.obj_options.output[:-4]
                    case _:
                        exit('queue_system was unknown when translating from no queue '
                             'system to {}'.format(self.queue_system))
            case _:
                exit('read_queue_system was unknown with value: {}'.format(self.read_queue_system))
    # ==========================
    class Options:
        def __init__(self, queue_options: dict = None):
            self.user = None
            self.nodes = None
            self.cores = None
            self.tasks = None
            self.time = None
            self.partition = None
            self.account = None
            self.subname = None
            self.output = None
            self.workdir = None
            if queue_options is not None:
                self.pass_options(queue_options)

        def pass_options(self, stated_options):
            for key, value in stated_options.items():
                match key:
                    case 'user':
                        self.user = value
                    case 'nodes':
                        self.nodes = value
                    case 'cores':
                        self.cores = value
                    case 'tasks':
                        self.tasks = value
                    case 'time':
                        self.time = value
                    case 'partition':
                        self.partition = value
                    case 'account':
                        self.account = value
                    case 'name':
                        self.subname = value
                    case 'workdir':
                        self.workdir = value
                    case 'output':
                        self.output = value
                    case _:
                        exit('Unknown option value in key: {}, with value: {} passed to pass_options'.format(key, value))

        def remove_empty_options(self):
            empty_attributes = [a for a in dir(self) if (not a.startswith('__') and
                                                         not callable(getattr(self, a)) and
                                                         getattr(self, a) is None)]
            for attribute in empty_attributes:
                delattr(self, attribute)

        # Queue System specifics {3}
        '''
        -----
        To add a new queue system, this section needs to have a new function declared.
        This function needs to take self and a dictionary of options. This dictionary will use the queue options
        from the bash script provided as keys, with the values being the declared options in the bash script.
        The match function will then match each option to the correct variables. These variables are:
        - user          The user ID of the system with which to submit the job.
        - nodes         The number of nodes to be requested.
        - cores         The number of cores each task will need.
        - tasks         The number of tasks to perform.
        - time          The walltime this job is allowed to run for in hh:mm:ss.
        - partition     The specific queue/partition to submit to.
        - account       The account to charge for the used resources.
        - subname       Name of the submitted job.
        - workdir       The directory in which the work should be done.
        - output        The file, including path, to write the STDOUT to.
        
        Template
        =====
        def <queue_name>_options(self, <queue_name>_options):
            for key, value in <queue_name>_options.items():
                match key:
                    case '':
                        if self.user is not None:
                            continue
                        else:
                            self.user = value
                    case '':
                        if self.nodes is not None:
                            continue
                        else:
                            self.nodes = value
                    case '':
                        if self.cores is not None:
                            continue
                        else:
                            self.cores = value
                    case '':
                        if self.tasks is not None:
                            continue
                        else:
                            self.tasks = value
                    case '':
                        if self.time is not None:
                            continue
                        else:
                            self.time = value
                    case '':
                        if self.partition is not None:
                            continue
                        else:
                            self.partition = value
                    case '':
                        if self.account is not None:
                            continue
                        else:
                            self.account = value
                    case '':
                        if self.subname is not None:
                            continue
                        else:
                            self.subname = value
                    case '':
                        if self.workdir is not None:
                            continue
                        else:
                            self.workdir = value
                    case '':
                        if self.output is not None:
                            continue
                        else:
                            self.output = value
                    case _:
                        exit('Unknown option value in key: {}, with value: {} passed to <queue_name>_options'.format(key, value))
        =====
        '''
        # ==========================
        def slurm_options(self, slurm_options):
            for key, value in slurm_options.items():
                match key:
                    case 'uid':
                        if self.user is not None:
                            continue
                        else:
                            self.user = value
                    case 'N' | 'nodes':
                        if self.nodes is not None:
                            continue
                        else:
                            self.nodes = value
                    case 'c' | 'cpus-per-task':
                        if self.cores is not None:
                            continue
                        else:
                            self.cores = value
                    case 'n' | 'ntasks':
                        if self.tasks is not None:
                            continue
                        else:
                            self.tasks = value
                    case 't' | 'time':
                        if self.time is not None:
                            continue
                        else:
                            self.time = value
                    case 'p' | 'partition':
                        if self.partition is not None:
                            continue
                        else:
                            self.partition = value
                    case 'A' | 'account':
                        if self.account is not None:
                            continue
                        else:
                            self.account = value
                    case 'J' | 'job-name':
                        if self.subname is not None:
                            continue
                        else:
                            self.subname = value
                    case 'D' | 'chdir':
                        if self.workdir is not None:
                            continue
                        else:
                            self.workdir = value
                    case 'o' | 'output':
                        if self.output is not None:
                            continue
                        else:
                            self.output = value
                    case _:
                        exit('Unknown option value in key: {}, with value: {} passed to slurm_options'.format(key, value))

        def torque_options(self, torque_options):
            for key, value in torque_options.items():
                match key:
                    case 'P':
                        if self.user is not None:
                            continue
                        else:
                            self.user = value
                    case 'l nodes':
                        if self.nodes is not None:
                            continue
                        else:
                            self.nodes = value
                    case 'l ncpus':
                        if self.cores is not None:
                            continue
                        else:
                            self.cores = value
                    case 'l ppn':
                        if self.tasks is not None:
                            continue
                        else:
                            self.tasks = value
                    case 'l walltime':
                        if self.time is not None:
                            continue
                        else:
                            self.time = value
                    case 'q':
                        if self.partition is not None:
                            continue
                        else:
                            self.partition = value
                    case 'A':
                        if self.account is not None:
                            continue
                        else:
                            self.account = value
                    case 'N':
                        if self.subname is not None:
                            continue
                        else:
                            self.subname = value
                    case 'd':
                        if self.workdir is not None:
                            continue
                        else:
                            self.workdir = value
                    case 'o':
                        if self.output is not None:
                            continue
                        else:
                            self.output = value
                    case _:
                        exit('Unknown option value in key: {}, with value: {} passed to torque_options'.format(key, value))
        # ==========================

    def change_options(self, queue_options: dict):
        self.obj_options.pass_options(queue_options)

    # Queue System specifics {4}
    '''
    -----
    To add a new queue system one cases need to be added in this section.
    This case needs to have the following format:
        case <queue name>
            match option:
                case <option name>:
                    return '<format to declare option in bash file>'
                ...
    the case that matches on option, needs to include the following options:
    - user
    - nodes
    - cores
    - tasks
    - time
    - partition
    - account
    - subname
    - workdir
    - output
    The <format to declare option in bash file> needs to include '-', '--', and or any space or '=' as it would
    appear in a bash script. 
    We use slurm options as an example:
        case 'user':
            return '--uid='
        case 'nodes':
            return '-n '
    
    Template:
    =====
    case '':
        match option:
            case 'user':
                return ''
            case 'nodes':
                return ''
            case 'cores':
                return ''
            case 'tasks':
                return ''
            case 'time':
                return ''
            case 'partition':
                return ''
            case 'account':
                return ''
            case 'subname':
                return ''
            case 'workdir':
                return ''
            case 'output':
                return ''
    =====
    '''
    # ==========================
    def option_converter(self, option):
        match self.queue_system:
            case 'slurm':
                match option:
                    case 'user':
                        return '--uid='
                    case 'nodes':
                        return '-N '
                    case 'cores':
                        return '-c '
                    case 'tasks':
                        return '-n '
                    case 'time':
                        return '-t '
                    case 'partition':
                        return '-p '
                    case 'account':
                        return '-A '
                    case 'subname':
                        return '-J '
                    case 'workdir':
                        return '-D '
                    case 'output':
                        return '-o '
            case 'torque':
                match option:
                    case 'user':
                        return '-P '
                    case 'nodes':
                        return '--l nodes='
                    case 'cores':
                        return '--l ncpus='
                    case 'tasks':
                        return '--l ppn='
                    case 'time':
                        return '--l walltime='
                    case 'partition':
                        return '-q '
                    case 'account':
                        return '-A '
                    case 'subname':
                        return '-N '
                    case 'workdir':
                        return '-d '
                    case 'output':
                        return '-o '
    # ==========================

    def read_script(self):
        options = {}
        work = []
        with open(self.work_script, 'r') as script:
            for line in script.readlines():
                if self.read_option_start in line:
                    if line[line.find("-"):][1:2] == '-':
                        option_end = line.find("-") + line[line.find("-"):].find('=')
                        option_name = line[line.find("-") + 2:option_end]
                    else:
                        option_end = line.find("-") + 2
                        option_name = line[line.find("-") + 1:option_end]
                    option_end += 1
                    option_value_end = line[option_end:].find(' ')
                    if option_value_end == -1:
                        option_value = line[option_end:-1]
                    else:
                        option_value_end += option_end
                        option_value = line[option_end:option_value_end]
                    options[option_name] = option_value
                else:
                    work += [line]
        return options, work

    def create_workfile(self):
        with open(self.tmp_work_script, 'w') as workfile:
            workfile.seek(0)
            for line in self.works:
                workfile.write(line)
        return

    def create_profilefile(self, tmp_work_script='./tmp_workfile.sh',
                           tmp_profile_script='./tmp_profilefile.sh',
                           bash_options=['']):
        if self.read_queue_system is not None:
            self.tmp_work_script = tmp_work_script
            self.create_workfile()
        else:
            self.tmp_work_script = self.work_script
        self.tmp_profile_script = tmp_profile_script

        with open(self.tmp_profile_script, 'w') as profilefile:
            profilefile.seek(0)
            profilefile.write('#!/bin/bash\n')
            if self.queue_system is not None:
                self.add_options(profilefile)

            profilefile.write('export WORKING_DIR={}\n'.format(self.work_dir))
            profilefile.write('if [ ! -d  "${WORKING_DIR}" ]; then\n')
            profilefile.write('  mkdir ${WORKING_DIR}\n')
            profilefile.write('fi\n')
            if self.queue_system is None:
                profilefile.write('cd ${WORKING_DIR}\n')
            profilefile.write('\n')

            if self.likwid:
                self.init_likwid(profilefile)

            if self.prometheus:
                self.init_prometheus(profilefile)

            if self.likwid:
                self.run_likwid(profilefile, bash_options)
            else:
                self.run_work(profilefile, bash_options)

            if self.prometheus:
                self.end_prometheus(profilefile)

            if self.likwid:
                self.end_likwid(profilefile)

        return

    def add_options(self, profilefile):
        to_write = [a for a in dir(self.obj_options) if not a.startswith('__') and
                    not callable(getattr(self.obj_options, a))]
        for option in to_write:
            if option is not None:
                profilefile.write(self.option_start + self.option_converter(option) +
                                  self.obj_options.__getattribute__(option) + '\n')
        profilefile.write('\n')

    def run_work(self, profilefile, bash_options=['']):
        profilefile.write('bash {} {}\n'.format(self.tmp_work_script,
                                                ' '.join(str(x) for x in bash_options)))
        profilefile.write('\n')
        return

    def init_likwid(self, profilefile):
        profilefile.write('# Likwid initialisation declarations\n')
        for i in self.likwid_req:
            profilefile.write(i)
            profilefile.write('\n')
        profilefile.write('\n')
        profilefile.write('export LIKWID_RUNNING_DIR=${WORKING_DIR}/Likwid\n')
        with open(self.likwid_file, 'r') as likwid_file:
            for number, line in enumerate(likwid_file):
                if line == '# *=*\n':
                    self.likwid_initEndSplit = number + 1
                    break
                profilefile.write(line)
        profilefile.write('# Likwid initialisation done\n')
        profilefile.write('\n')

    def run_likwid(self, profilefile, bash_options=['']):
        profilefile.write('likwid-perfctr -g MEM_DP -f bash {} {}\n'.format(self.tmp_work_script,
                                                                            ' '.join(str(x) for x in bash_options)))
        profilefile.write('\n')
        return

    def end_likwid(self, profilefile):
        profilefile.write('# Likwid final steps declarations\n')
        with open(self.likwid_file, 'r') as likwid_file:
            for line in itertools.islice(likwid_file, self.likwid_initEndSplit, None):
                profilefile.write(line)
        profilefile.write('# Likwid final steps done\n')
        profilefile.write('\n')
        return

    def init_prometheus(self, profilefile):
        profilefile.write('# Prometheus initialisation declarations\n')
        for i in self.prometheus_req:
            profilefile.write(i)
            profilefile.write('\n')
        profilefile.write('export PROMETHEUS_RUNNING_DIR=${WORKING_DIR}/Prometheus\n')
        scrape_path = str(impresources.path(data, 'read_prometheus.py'))[:-19]
        profilefile.write('export PROFILE_SCRAPE={}\n'.format(scrape_path))
        profilefile.write('\n')
        with open(self.prometheus_file, 'r') as prometheus_file:
            for number, line in enumerate(prometheus_file):
                if line == '# *=*\n':
                    self.prometheus_initEndSplit = number + 1
                    break
                profilefile.write(line)
        profilefile.write('# Prometheus initialisation done\n')
        profilefile.write('\n')

    def end_prometheus(self, profilefile):
        profilefile.write('# Prometheus final steps declarations\n')
        with open(self.prometheus_file, 'r') as prometheus_file:
            for line in itertools.islice(prometheus_file, self.prometheus_initEndSplit, None):
                profilefile.write(line)
        profilefile.write('# Prometheus final steps done\n')
        profilefile.write('\n')
