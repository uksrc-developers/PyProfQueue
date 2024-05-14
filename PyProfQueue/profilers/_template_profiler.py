from importlib import resources as impresources
import itertools
import io

from . import data

_NEW_PROFILER_file_path = impresources.files(data) / "_template_commands.txt"
_NEW_PROFILER_initEndSplit = -1

def define_initialise(profilefile: io.TextIOWrapper, requirements):
    '''
    define_initialise creates any needed variables, and writes the required arguments into the profile_file in order
    to initialise the profiling for a user, in this case that is <template_profiler>.

    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.
    requirements: dict = dictionary containing required arguments that the profiler has or other values.

    Returns
    -------
    None
    '''
    print('Template Function')
    return

def define_run(profilefile: io.TextIOWrapper, bash_options: list, tmp_work_script: str = './tmp_workfile.sh'):
    '''
    define_run calls the user given bash script using <template_profiler> to execute and profile the work done.
    Parameters. This only has to be defined, if the profiler in question is used to execute the user given bash script.
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
    print('Template Function')
    return


def define_end(profilefile: io.TextIOWrapper):
    '''
    define_end terminates and scrapes any data from the profiler that was used to profile the user specified bash
    script, in this case that is <template_profiler>.
    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.

    Returns
    -------
    None
    '''
    print('Template Function')
    return