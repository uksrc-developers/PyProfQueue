from importlib import resources as impresources
import itertools
import io

import matplotlib.collections as collection
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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
    profilerdict: dict = dictionary containing required arguments that the profiler has or other values.

    Returns
    -------
    None
    '''
    global likwid_file_path
    global likwid_initEndSplit
    profilefile.write('# Likwid initialisation declarations\n')
    if 'requirements' in profilerdict.keys():
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


def define_run(profilefile: io.TextIOWrapper, bash_options: list = [''], works: list = None,
               tmp_work_script: str = './tmp_workfile.sh', profilerdict: dict = None):
    """
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
    """
    if tmp_work_script is not None:
        profilefile.write('likwid-perfctr -g MEM_DP -t 300s -o ${LIKWID_RUNNING_DIR}/likwid_output.txt -O -f bash ' +
                      '{} {}\n'.format(tmp_work_script, ' '.join(str(x) for x in bash_options)))
    else:
        profilefile.write('likwid-perfctr -g MEM_DP -t 300s -o ${LIKWID_RUNNING_DIR}/likwid_output.txt -O -f ' +
                          ' '.join(works) + ' {}\n'.format(' '.join(str(x) for x in bash_options)))
    profilefile.write('\n')
    return works


def define_end(profilefile: io.TextIOWrapper):
    """
    define_end terminates and scrapes any data from the profiler that was used to profile the user specified bash
    script, in this case that is likwid.
    Parameters
    ----------
    profilefile: io.TextIOWrapper = Open text file that can be written to and is being used to initiate, call and
        terminate all profiling codes that are to be executed with the user specified bash script.

    Returns
    -------
    None
    """
    global likwid_file_path
    global likwid_initEndSplit
    profilefile.write('# Likwid final steps declarations\n')
    with open(likwid_file_path, 'r') as read_file:
        for line in itertools.islice(read_file, likwid_initEndSplit, None):
            profilefile.write(line)
    profilefile.write('# Likwid final steps done\n')
    profilefile.write('\n')
    return


def plot_likwid_roof_single(name_prefix: str,
                            maxperf: float,
                            maxband: float,
                            code_name: str = 'code',
                            code_mflop: float = None,
                            code_opint: float = None):
    if code_mflop is not None:
        if code_opint * maxband < maxperf:
            Percentage = int((code_mflop / (code_opint * maxband)) * 100)
        else:
            Percentage = int((code_mflop / maxperf) * 100)
        Dot = True
    else:
        Dot = False

    if maxperf / maxband > 1:
        maxX = (maxperf / maxband) * 2
        if Dot:
            if (maxX < code_opint):
                maxX = code_opint
    else:
        maxX = 1
        if Dot:
            if (maxX < code_opint):
                maxX = code_opint

    x_Axis = np.append(np.linspace(0, maxperf / maxband, 10), maxX)
    y = np.array([x * maxband if ((x * maxband) < maxperf) else maxperf for x in x_Axis])
    Roofline = plt.figure(figsize=(10, 7))
    Roofline.suptitle("Roofline Model", fontsize=20)
    plt.plot(x_Axis, y, label="Roofline")
    plt.vlines(maxperf / maxband, 0, maxperf, linestyle='--', color='gray', alpha=0.5,
               label='Bandwidth to CPU limit boarder')
    plt.xlabel("Operational Intensity")
    plt.ylabel("Performance [MFLOP/s]")
    if Dot:
        plt.plot(code_opint, code_mflop, 'ro', label=f'{code_name} Performance [~{Percentage}% of roofline]')
        plt.xlim([0, x_Axis.max()])
    plt.ylim([0, maxperf * 1.1])
    plt.legend(loc='upper left')
    plt.savefig(name_prefix + '_Roofline.png', bbox_inches='tight')
    return


def read_timeseries(likwid_file: str):
    likwid_header = pd.read_csv(likwid_file, header=None, skiprows=1, nrows=1)
    likwid_dataframe = pd.read_csv(likwid_file, skiprows=[0, 1], header=None)
    metrics = likwid_dataframe.iloc[0, 1]
    cpu_count = likwid_dataframe.iloc[0, 2]
    header = ["GID", "MetricsCount", "CPUCount", "Total runtime [s]"]
    for metric in range(4, metrics + 4):
        for cpu in range(cpu_count):
            header += [f"Thread {cpu}: {likwid_header.iloc[0, metric]}"]
    likwid_dataframe.columns = header

    keep = []
    for name in header:
        if 'Operational intensity' in name or ": MFLOP/s" in name or "Total runtime [s]" in name:
            keep += [True]
        else:
            keep += [False]
    len(keep)
    reduced_dataframe = likwid_dataframe.loc[:, keep]

    time = reduced_dataframe.filter(like='Total runtime [s]').sum(1).values
    op_int = reduced_dataframe.filter(like='Operational intensity').sum(1).values
    flop_s = reduced_dataframe.filter(like='MFLOP/s').sum(1).values
    return time, op_int, flop_s


def plot_roof_timeseries(likwid_file: str,
                         name_prefix: str,
                         maxperf: float,
                         maxband: float,
                         code_name: str = 'code',
                         log_plot: bool = False):
    time_series, code_opint, code_mflop = read_timeseries(likwid_file)
    points = np.array([code_opint, code_mflop]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    if maxperf / maxband > 1:
        max_x = (maxperf / maxband) * 2
    else:
        max_x = 1

    if max_x < code_opint.mean():
        max_x = code_opint.mean()

    x_axis = np.append(np.linspace(0, maxperf / maxband, 10), max_x)
    y = np.array([x * maxband if ((x * maxband) < maxperf) else maxperf for x in x_axis])

    fig, axs = plt.subplots(1, 1, sharex=True, sharey=True)
    norm = plt.Normalize(time_series.min(), time_series.max())

    lc = collection.LineCollection(segments, cmap='viridis', norm=norm)
    lc.set_array(time_series)
    lc.set_linewidth(2)

    pc = collection.RegularPolyCollection(numsides=4, offsets=points.reshape(-1, 2), offset_transform=axs.transData,
                                          cmap='viridis', norm=norm, sizes=[100] * len(time_series))
    pc.set_array(time_series)
    pc.set_label(code_name)

    axs.plot(x_axis, y, label="Hardware Roofline")
    axs.vlines(maxperf / maxband, 0, maxperf, linestyle='--', color='gray', alpha=0.5,
               label='Mem BandWidth to CPU limit boarder')
    line = axs.add_collection(lc)
    points = axs.add_collection(pc)
    fig.colorbar(line, ax=axs, label='Time [s]')

    axs.set_xlim(0, max_x)
    if log_plot:
        axs.set_yscale('log')
        axs.set_ylim(code_mflop.min(), maxperf * 10)
    else:
        axs.set_ylim(0, maxperf*1.1)
    axs.set_xlabel('Operational Intensity')
    axs.set_ylabel('Performance log([MFLOP/s])')
    plt.savefig(name_prefix + '_TimeSeriesRoofline.png', bbox_inches='tight')
