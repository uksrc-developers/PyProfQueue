# Built in Modules
import subprocess
import time
# Local package imports
from .script import Script


def submit(script: Script,
           tmp_work_script: str = './tmp_workfile.sh',
           tmp_profile_script: str = './tmp_profilefile.sh',
           bash_options: list = [''],
           leave_scripts: bool = False,
           verbose: bool = False,
           test: bool = False):
    '''
    Submission
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
    leave_scripts : bool = False
        If True, leave scripts after submission.
    verbose : bool =  False
        If True, steps taken will be printed to stdout.
    '''
    script.create_profilefile(tmp_work_script, tmp_profile_script, bash_options)
    if verbose or test:
        if verbose:
            print('Submitting script to profile using the following command:')
        if test:
            print('The following command would be used to submit a job to the queue:')
            print(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]))
    if not test:
        subprocess.run(' '.join([getattr(script, 'submission'), getattr(script, 'tmp_profile_script')]), shell=True)
        time.sleep(1)

    if verbose or test:
        print('Submitted script.')
    if leave_scripts:
        if verbose or test:
            print('Leaving scripts after submission.')
        return
    else:
        subprocess.run('rm {}'.format(getattr(script, 'tmp_profile_script')), shell=True)
        subprocess.run('rm {}'.format(getattr(script, 'tmp_work_script')), shell=True)
        if verbose or test:
            print('Removed temporary scripts after submission.')
        return
