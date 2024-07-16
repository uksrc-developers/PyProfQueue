import importlib
import sys


class Script:
    """
    Class to read existing bash scripts, pull out the options and create an object that contains all the
    queue options, bash options, and desired profiling methods to be injected

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
    profiling : dict = None
        dictionary where keys are the name of the profiler to use, and the values are dictionaries containing
        "requirements" or other optional commands depending on the profiler being used.

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
                 read_queue_system: str = 'None',
                 queue_options: dict = None,
                 profiling: dict = None
                 ):
        if True:  # If statement added to allow for the collapse of the initiation of variables
            self.queue_system = queue_system
            if self.queue_system is not None:
                try:
                    module = ".batch_systems." + self.queue_system
                    self.queue_system_parameters = importlib.import_module(module, package="PyProfQueue").parameters
                except:
                    exit(f'No compatible queue system was specified, instead {self.queue_system} was provided as a queue system')
                if bool(queue_options):
                    self.obj_options = Options(queue_system_parameters=self.queue_system_parameters,
                                               queue_options=queue_options)
                else:
                    self.obj_options = Options(queue_system_parameters=self.queue_system_parameters)
            else:
                self.queue_system_parameters = None
                self.obj_options = Options(queue_system_parameters=None, queue_options=queue_options)
            self.work_script = work_script
            self.tmp_work_script = None
            self.tmp_profile_script = None
            self.works = None
            self.work_dir = None
            self.profiling = profiling
            self.at_execute = False  # boolean to see if a profiler is already used at the execution line.

            self.read_queue_system = read_queue_system
            if self.read_queue_system is not None:
                try:
                    module = ".batch_systems." + self.read_queue_system
                    self.read_queue_system_parameters = importlib.import_module(module, package="PyProfQueue").parameters
                except:
                    exit(f'No compatible read queue system was specified, instead {self.read_queue_system} was provided as a queue system')
            else:
                self.read_queue_system_parameters = None

        if self.queue_system != 'None':
            self.option_start = self.queue_system_parameters['Option_Flag']
            self.submission = self.queue_system_parameters['submission_command']

        if self.read_queue_system != 'None':
            self.read_option_start = self.read_queue_system_parameters['Option_Flag']
            self.works = self.read_script()

    def initialise_profiling(self, profiler, profilefile):
        """
        initialse_profiling is used to call the define_initialise() function of the different profilers
        Parameters

        ----------
        profiler: str
            name of the profiler to be used, must match the .py file name located in PyProfQueue.profilers
                Currently supports: ["likwid", "prometheus"]
        profilefile: io.TextIOWrapper
            open profile file with write permissions.

        Returns None
        -------

        """
        if self.profiling[profiler] is None:
            exit(f"Each profiling type, has to have a value that is not None. Profiling {profiler} "
                 f"had a value of None")
        else:
            module = ".profilers."+profiler
            current_prof = importlib.import_module(module, package="PyProfQueue")
            current_prof.define_initialise(profilefile=profilefile,
                                           profilerdict=self.profiling[profiler])

    def run_work_profiling(self, profiler, profilefile, bash_options):
        """
        run_work_profiling is used to call the define_run() function of the different profilers. This function makes
        it so that the user specified bash script is executed using the chosen profiler. This can only occur once,
        listing multiple profilers that rely on this functions will cause an error.

        Parameters
        ----------
        profiler: str
            name of the profiler to be used, must match the .py file name located in PyProfQueue.profilers
            Currently supports: ["likwid", "prometheus"]
        profilefile: io.TextIOWrapper
            open profile file with write permissions.
        bash_options: list
            List of bash options to pass to the user defined bash script.

        Returns None
        -------

        """
        module = ".profilers."+profiler
        current_prof = importlib.import_module(module, package="PyProfQueue")
        if hasattr(current_prof, "define_run"):
            if not self.at_execute:
                self.works = current_prof.define_run(profilefile=profilefile,
                                                     bash_options=bash_options,
                                                     tmp_work_script=self.tmp_work_script,
                                                     works=self.works,
                                                     profilerdict=self.profiling[profiler])
                self.at_execute = True
            else:
                exit(f"Multiple at execution profilers were defined. Failed when adding profiler {profiler}")

    def run_work(self, profilefile, bash_options=['']):
        """
        run_work writes into the profile bash script the call to run the user defined bash script. This is
        used when no profiler needs to execute the user defined bash script.

        Parameters
        ----------
        profilefile: io.TextIOWrapper
            open profile file with write permissions.
        bash_options: list
            List of bash options to pass to the user defined bash script.

        Returns
        -------

        """
        profilefile.write('bash {} {}\n'.format(self.tmp_work_script,
                                                ' '.join(str(x) for x in bash_options)))
        profilefile.write('\n')
        return

    def end_profiling(self, profiler, profilefile):
        """
        end_profiling is used to call the define_end() function of the different profilers.

        Parameters
        ----------
        profiler: str
            name of the profiler to be used, must match the .py file name located in PyProfQueue.profilers
                Currently supports: ["likwid", "prometheus"]
        profilefile: io.TextIOWrapper
            pen profile file with write permissions.

        Returns
        -------

        """
        module = ".profilers."+profiler
        current_prof = importlib.import_module(module, package="PyProfQueue")
        current_prof.define_end(profilefile=profilefile)

    def change_options(self, queue_options: dict):
        """
        change_options allows users to change the options they specified, after initialising their object.

        Parameters
        ----------
        queue_options: dict
            dictionary containing all the queue options to be used. These will overwrite queue options inside the
            user defined bash script.

        Returns None
        -------
        """
        self.obj_options.overwrite_options(queue_options)
        return

    def read_script(self):
        """
        read_script reads the user defined bash script and returns the options as a dictionary, and all the work
        that is to be run as a list of strings.

        Returns options (dict), work (list[str])
        -------
        """
        options = {}
        work = []
        with open(self.work_script, 'r') as script:
            for line in script.readlines():
                if self.read_option_start in line:
                    if line[line.find("-"):][1:2] == '-':
                        option_end = line.find("-") + line[line.find("-"):].find('=')
                        option_name = line[line.find("-") + 2:option_end]
                    elif ('option_prefixes' in self.read_queue_system_parameters and
                        line[line.find("-"):][1:2] in self.read_queue_system_parameters['option_prefixes']):
                        prefix = line[line.find("-"):][1:2]
                        prefix_loc = line.find("-" + prefix) + 3
                        option_end = prefix_loc + line[prefix_loc:].find(' ')
                        option_name = prefix + ' ' + line[prefix_loc:option_end]
                    else:
                        option_end = line.find("-") + 2
                        option_name = line[line.find("-") + 1:option_end]
                    key_found = False
                    for key, value_list in self.read_queue_system_parameters['options'].items():
                        if option_name in value_list:
                            option_name = key
                            key_found = True
                    if key_found is False:
                        exit(f'{option_name} not found in {self.read_queue_system} as configured for PyProfQueue.')

                    option_end += 1
                    option_value_end = line[option_end:].find(' ')
                    if option_value_end == -1:
                        option_value = line[option_end:-1]
                    else:
                        option_value_end += option_end
                        option_value = line[option_end:option_value_end]
                    if self.read_queue_system != self.queue_system:
                        if 'option_environment_variable' in self.read_queue_system_parameters:
                            for key, value in self.read_queue_system_parameters['option_environment_variable'].items():
                                if value in option_value:
                                    option_value = option_value.replace(value, key)
                        for key, value in self.read_queue_system_parameters['environment_variable'].items():
                            if value in option_value:
                                option_value = option_value.replace(value, self.queue_system_parameters['environment_variable'][key])
                                if 'option_environment_variable' in self.queue_system_parameters:
                                    if self.queue_system_parameters['environment_variable'][key] in self.queue_system_parameters['option_environment_variable'].keys():
                                        option_value = option_value.replace(self.queue_system_parameters['environment_variable'][key],
                                                                            self.queue_system_parameters['option_environment_variable'][self.queue_system_parameters['environment_variable'][key]])
                    options[option_name] = option_value
                else:
                    work += [line]
        self.obj_options.append_options(options)
        return work

    def create_workfile(self):
        """
        create_workfile creates the work file based on the user defined bash script by simply removing the options.
        This is not used, when the work script has no queue options.
        Returns
        -------

        """
        with open(self.tmp_work_script, 'w') as workfile:
            workfile.seek(0)
            for line in self.works:
                workfile.write(line)
        return

    def add_options(self, profilefile):
        """
        add_options adds the queue options from the Script object to the profile file.
        Parameters
        ----------
        profilefile: io.TextIOWrapper
            open profile file with write access.
        Returns None
        -------

        """
        for key, value in self.obj_options.option_dictionary.items():
            if key is not None and key != 'workdir':
                if (len(self.queue_system_parameters['options'][key][0]) > 1 and
                        self.queue_system_parameters['options'][key][0][1] != ' '):
                    pre_option_gap = ' --'
                    post_option_gap = '='
                else:
                    pre_option_gap = ' -'
                    post_option_gap = ' '
                profilefile.write(self.queue_system_parameters['Option_Flag'] + pre_option_gap +
                                  self.queue_system_parameters['options'][key][0] + post_option_gap +
                                  value + '\n')
        profilefile.write('\n')
        return

    def create_profilefile(self, tmp_work_script='./tmp_workfile.sh',
                           tmp_profile_script='./tmp_profilefile.sh',
                           bash_options=None):
        """
        create_profilefile uses the attributes of the Script object, and creates the temporary profile file that will
        be submitted to the queue on behalf of the user.

        Parameters
        ----------
        tmp_work_script: str
            path and name of the temporary work file that should be created. This file is the user defined bash script
            with any queue options removed.
        tmp_profile_script: str
            path and name of the temporary profile file that should be created. This will contain any profiling
            initialisations, calls and terminations needed to profile the user defined work with the desired profiling
            software.
        bash_options: list[str]
            list of bash options that should be passed to the user defined bash script.
        Returns None
        -------
        """
        if bash_options is None:
            bash_options = ['']
        self.tmp_profile_script = tmp_profile_script
        self.tmp_work_script = tmp_work_script
        with open(self.tmp_profile_script, 'w') as profilefile:
            profilefile.seek(0)
            profilefile.write('#!/bin/bash\n')
            if self.queue_system is not None:
                self.add_options(profilefile)

            profilefile.write('export WORKING_DIR={}\n'.format(self.work_dir))
            profilefile.write('if [ ! -d  "${WORKING_DIR}" ]; then\n')
            profilefile.write('  mkdir ${WORKING_DIR}\n')
            profilefile.write('fi\n')
            profilefile.write('cd ${WORKING_DIR}\n')
            profilefile.write(f'export PYTHON_INSTANCE={sys.executable}')
            profilefile.write('\n')
            if self.profiling is not None:
                for key in self.profiling.keys():
                    self.initialise_profiling(key, profilefile)

                profilefile.write('export START_TIME=$(date +%s)\n')
                profilefile.write('sleep 10\n\n')
                for key in self.profiling.keys():
                    self.run_work_profiling(key, profilefile, bash_options)
                if not self.at_execute:
                    self.run_work(profilefile, bash_options)
                profilefile.write('sleep 10\n')
                profilefile.write('export END_TIME=$(date +%s)\n')
                profilefile.write('export DURATION=$((${END_TIME} - ${START_TIME}))\n')
                profilefile.write('export START=$(date -d @${START_TIME} +"%Y-%m-%d %H:%M:%S")\n')
                profilefile.write('export END=$(date -d @${END_TIME} +"%Y-%m-%d %H:%M:%S")\n\n')
                for key in self.profiling.keys():
                    self.end_profiling(key, profilefile)
            else:
                profilefile.write('export START_TIME=$(date +%s)\n')
                profilefile.write('sleep 10\n')
                self.run_work(profilefile, bash_options)
                profilefile.write('sleep 10\n')
                profilefile.write('export END_TIME=$(date +%s)\n')
                profilefile.write('export DURATION=$((${END_TIME} - ${START_TIME}))\n')
                profilefile.write('export START=$(date -d @${START_TIME} +"%Y-%m-%d %H:%M:%S")\n')
                profilefile.write('export END=$(date -d @${END_TIME} +"%Y-%m-%d %H:%M:%S")\n\n')
            profilefile.write("echo 'Run time: '$((${DURATION}/60/60))':'$((${DURATION}/60%60 ))':'$((${DURATION}%60))\n")

        if self.read_queue_system is not None:
            self.create_workfile()
        else:
            self.tmp_work_script = self.work_script

        return


class Options:
    """
    Class to read existing bash scripts, pull out the options and create an object that contains all the
    queue options, bash options, and desired profiling methods to be injected

    Parameters to initiate
    ----------
    queue_options: dict
        dictionary containing all the queue options to be used. These will overwrite queue options inside the
        user defined bash script.
    """

    def __init__(self, queue_system_parameters: dict | None, queue_options: dict = None):
        self.option_dictionary = {}
        if queue_system_parameters is None:
            if queue_options is not None:
                if 'work_dir' not in queue_options.keys():
                    exit('work_dir parameter is required for queue_options if no batch system is being used.')
                else:
                    self.overwrite_options(queue_options)
            else:
                exit('work_dir parameter is required for queue_options if no batch system is being used.')
        elif queue_options is None:
            self.queue_system_parameters = queue_system_parameters
        else:
            self.queue_system_parameters = queue_system_parameters
            self.overwrite_options(queue_options)

    def check_options(self, queue_system_parameters: dict):
        """
        check_options takes a dictionary containing all the queue options to be used and verifies that the batch system
        chosen has been configured in PyProfQueue to be compatible with this option.

        Parameters
        ----------
        queue_system_parameters: dict
            dictionary containing all the parameters that the queue is has.

        Returns None
        -------

        """
        for key in self.option_dictionary.keys():
            if key not in queue_system_parameters['options']:
                exit(f"Queue option {key} is not compatible with the queue {queue_system_parameters['queue_name']}"
                     f" as configured with PyProfQueue.")

    def overwrite_options(self, queue_options: dict):
        """
        overwrite_options takes a dictionary containing all the queue options to be used, verifies that the batch system
        chosen has been configured in PyProfQueue to be compatible with this option and then overwrites the existing
        value of the option or adds it to the queue options dictionary.

        Parameters
        ----------
        queue_options: dict
            dictionary containing all options that are to be changed and overwritten.

        Returns None
        -------

        """
        for key, value in queue_options.items():
            if key in self.queue_system_parameters['options'].keys():
                if any(val in value for val in self.queue_system_parameters['environment_variable'].keys()):
                    new_value = value
                    for env_key, env_value in self.queue_system_parameters['environment_variable'].items():
                        new_value = new_value.replace(env_key, env_value)
                    if "option_environment_variable" in self.queue_system_parameters:
                        if any(short_val in new_value for short_val in self.queue_system_parameters['option_environment_variable'].keys()):
                            for short_key, short_value in self.queue_system_parameters['option_environment_variable'].items():
                                new_value = new_value.replace(short_key, short_value)
                    self.option_dictionary[key] = new_value
                else:
                    self.option_dictionary[key] = value
            else:
                print(f"during overwrite_options: {key} is not a valid queue option, continuing with remaining options.")

    def append_options(self, queue_options: dict):
        """
        append_options takes a dictionary containing all the queue options to be used, verifies that the batch system
        chosen has been configured in PyProfQueue to be compatible with this option and then appends it to the queue
        options dictionary if it is not already present. It does not overwrite the existing options.

        Parameters
        ----------
        queue_options: dict
            dictionary containing all options that are to be changed and overwritten.

        Returns None
        -------

        """
        for key, value in queue_options.items():
            if key in self.queue_system_parameters['options'].keys() and key not in self.option_dictionary:
                self.option_dictionary[key] = value
            elif key not in self.queue_system_parameters['options'].keys():
                print(f"during append_options: {key} is not a valid queue option, continuing with remaining options.")
