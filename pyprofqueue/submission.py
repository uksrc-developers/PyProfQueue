# Built in Modules
import subprocess
import time

# Local package imports
from .script import Script


def submit(script: Script,
           bash_options: list = None,
           test: bool = False):
    '''
    Create the temporary profile file and temporary work script in order to submit them to the appropriate queuing
    system.

    Parameters
    ----------
    script : pyprofbash.Script
        pyprofbash.Script created prior to submission.
    bash_options : list = ['']
        Optional parameter to add additional strings to the end of the call of the original work script in case
        that script has options it needs to have passed to it.
    test : bool =  False
        If True, it prints out the command it would
        have used if it had submitted them.
    '''
    write_files(script, bash_options)

    if test:
        print('The following command would be used to submit a job to the queue:')
        print(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]))
    else:
        subprocess.run(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]), shell=True)
        time.sleep(1)
    return


def write_files(script: Script, bash_options: list = None):
    '''
    Create the temporary profile file and temporary work script in order to submit them to the appropriate queuing
    system.

    Parameters
    ----------
    script : pyprofbash.Script
        pyprofbash.Script created prior to submission.
    bash_options : list = ['']
        Optional parameter to add additional strings to the end of the call of the original work script in case
        that script has options it needs to have passed to it.
    '''
    if bash_options is None:
        bash_options = ['']
    script.create_profilefile(bash_options)
    return