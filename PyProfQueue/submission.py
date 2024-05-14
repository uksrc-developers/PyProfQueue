# Built in Modules
import subprocess
import time

# Local package imports
from .script import Script


def submit(script: Script,
           tmp_work_script: str = './tmp_workfile.sh',
           tmp_profile_script: str = './tmp_profilefile.sh',
           bash_options: list = [''],
           leave_scripts: bool = True,
           test: bool = False):
    '''
    Create the temporary profile file and temporary work script in order to submit them to the appropriate queuing
    system.

    Parameters
    ----------
    script : pyprofbash.Script
        pyprofbash.Script created prior to submission.
    tmp_work_script : str = './tmp_workfile.sh'
        Optional Parameter to change the name of the temporary work script which should be the original script
        used to initiate the Script object, but all queue options should have been removed.
    tmp_profile_script : str = './tmp_profilefile.sh'
        Optional Parameter to change the name of the temporary profile script which will be submitted to the queue
    bash_options : list = ['']
        Optional parameter to add additional strings to the end of the call of the original work script in case
        that script has options it needs to have passed to it.
    leave_scripts : bool = True
        If True, leave scripts after submission.
    test : bool =  False
        If True, leaves scripts that are created, but does not submit them. Instead, it prints out the command it would
        have used if it had submitted them.
    '''
    script.create_profilefile(tmp_work_script, tmp_profile_script, bash_options)
    if test:
        print('The following command would be used to submit a job to the queue:')
        print(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]))
    else:
        subprocess.run(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]), shell=True)
        time.sleep(1)

    if leave_scripts or test:
        return
    else:
        subprocess.run(f'rm {tmp_profile_script}', shell=True)
        subprocess.run(f'rm {tmp_work_script}', shell=True)
        return
