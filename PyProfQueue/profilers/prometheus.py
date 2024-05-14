from importlib import resources as impresources
import itertools
import io

from . import data

prometheus_file_path = impresources.files(data) / "prometheus_commands.txt"
prometheus_initEndSplit = -1
IP_address = None


def define_initialise(profilefile: io.TextIOWrapper, profilerdict: dict = None):
    '''
    define_initialise creates any needed variables, and writes the required arguments into the profile_file in order
    to initialise the profiling for a user, in this case that is <template_profiler>.

    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.
    profilerdict: dict = dictionary containing required arguments that prometheus has or a preexisting ip_address for
        a prometheus instance.
    Returns
    -------
    None
    '''
    global prometheus_file_path
    global prometheus_initEndSplit
    global IP_address
    if 'ip_address' not in profilerdict.keys() and 'requirements' not in profilerdict.keys():
        exit("Must provide prometheus requirements list, or existing prometheus IP address, neither was given.")
    profilefile.write('# Prometheus initialisation declarations\n')
    if 'ip_address' not in profilerdict.keys():
        profilefile.write("export PROMETHEUS_IP=http://localhost:9090\n")
        for i in profilerdict['requirements']:
            profilefile.write(i)
            profilefile.write('\n')
    else:
        IP_address = profilerdict['ip_address']
        profilefile.write(f"export PROMETHEUS_IP={IP_address}\n")
    profilefile.write('export PROMETHEUS_RUNNING_DIR=${WORKING_DIR}/Prometheus\n')
    scrape_path = str(impresources.path(data, 'read_prometheus.py'))[:-19]
    profilefile.write('export PROFILE_SCRAPE={}\n'.format(scrape_path))
    profilefile.write('\n')
    final_init_indicator = 2
    if IP_address is None:
        read_indicators = [0, 1, 2]
    else:
        read_indicators = [0, 2]
    indicator = 0
    with open(prometheus_file_path, 'r') as read_file:
        for number, line in enumerate(read_file):
            if line == '# *=*\n' and indicator >= final_init_indicator:
                prometheus_initEndSplit = number + 1
                break
            elif line == '# *=*\n':
                indicator += 1
                continue
            if indicator in read_indicators:
                profilefile.write(line)
    profilefile.write('# Prometheus initialisation done\n')
    profilefile.write('\n')


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
    global prometheus_file_path
    global prometheus_initEndSplit
    profilefile.write('# Prometheus final steps declarations\n')
    if IP_address is None:
        read_indicators = [0, 1, 2]
    else:
        read_indicators = [0, 2]
    indicator = 0
    with open(prometheus_file_path, 'r') as read_file:
        for line in itertools.islice(read_file, prometheus_initEndSplit, None):
            if line == '# *=*\n':
                indicator += 1
                continue
            if indicator in read_indicators:
                profilefile.write(line)
    profilefile.write('# Prometheus final steps done\n')
    profilefile.write('\n')
