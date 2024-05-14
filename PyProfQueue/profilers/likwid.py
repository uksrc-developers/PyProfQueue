from importlib import resources as impresources
import itertools
import io

from . import data

likwid_file_path = impresources.files(data) / 'likwid_commands.txt'
likwid_initEndSplit = -1



def define_initialise(profilefile: io.TextIOWrapper, profilerdict: dict = None):
    '''
    define_initialise creates any needed variables, and writes the required arguments into the profile_file in order
    to initialise the profiling for a user, in this case that is likwid.

    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.
    requirements: list = dictionary containing required arguments that the profiler has or other values.

    Returns
    -------
    None
    '''
    global likwid_file_path
    global likwid_initEndSplit
    profilefile.write('# Likwid initialisation declarations\n')
    for i in profilerdict['requirements']:
        profilefile.write(i)
        profilefile.write('\n')
    profilefile.write('\n')
    profilefile.write('export LIKWID_RUNNING_DIR=${WORKING_DIR}/Likwid\n')
    with open(likwid_file_path, 'r') as read_file:
        for number, line in enumerate(read_file):
            if line == '# *=*\n':
                likwid_initEndSplit = number + 1
                break
            profilefile.write(line)
    profilefile.write('# Likwid initialisation done\n')
    profilefile.write('\n')


def define_run(profilefile: io.TextIOWrapper, bash_options: list = [''], tmp_work_script: str = './tmp_workfile.sh'):
    '''
    define_run calls the user given bash script using likwid to execute and profile the work done.

    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.
    bash_options: list = List of bash options that the user specified bash script needs to execute as intended
    tmp_work_script: str = Path and name of the temporary work script that contains all the users code minus
        queue options.

    Returns
    -------
    None
    '''
    profilefile.write('likwid-perfctr -g MEM_DP -f bash {} {}\n'.format(tmp_work_script,
                                                                        ' '.join(str(x) for x in bash_options)))
    profilefile.write('\n')
    return


def define_end(profilefile: io.TextIOWrapper):
    '''
    define_end terminates and scrapes any data from the profiler that was used to profile the user specified bash
    script, in this case that is likwid.
    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.

    Returns
    -------
    None
    '''
    global likwid_file_path
    global likwid_initEndSplit
    profilefile.write('# Likwid final steps declarations\n')
    with open(likwid_file_path, 'r') as read_file:
        for line in itertools.islice(read_file, likwid_initEndSplit, None):
            profilefile.write(line)
    profilefile.write('# Likwid final steps done\n')
    profilefile.write('\n')
    return
