from importlib import resources as impresources
import subprocess, itertools, io, os

import matplotlib.collections as collection
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pyarrow import output_stream

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
               tmp_work_script: str = None, work_script: str = None, profilerdict: dict = None):
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
    profiling_call = f'likwid-perfctr -g PYPROFQUEUE -t 120s -O -f '
    output_call = " 2> ${LIKWID_RUNNING_DIR}/temp_likwid.txt > ${LIKWID_RUNNING_DIR}/temp_out.txt\n"

    if tmp_work_script is None and (profilerdict is None or 'code_line' not in profilerdict.keys()):
        profilefile.write(profiling_call + 'bash ' +
                          '{} {}'.format(work_script, ' '.join([str(x) for x in bash_options])) +
                          output_call)
    elif (profilerdict is None or 'code_line' not in profilerdict.keys()):
        profilefile.write(profiling_call + 'bash ' +
                          '{} {}'.format(tmp_work_script, ' '.join([str(x) for x in bash_options])) +
                          output_call)
    elif ('code_line' in profilerdict.keys()):
        with open(tmp_work_script, 'r') as workfile:
            workfile.seek(0)
            data = workfile.readlines()
        for line in range(len(data)):
            for profile_line in profilerdict['code_line']:
                if data[line] == profile_line+'\n':
                    data[line] = profiling_call + data[line].strip() + output_call
        with open(tmp_work_script, 'w') as workfile:
            workfile.seek(0)
            workfile.writelines(data)
        profilefile.write('bash {} {}\n'.format(tmp_work_script, ' '.join([str(x) for x in bash_options])))
    else:
        profilefile.write(profiling_call +
                          ' '.join(works) +
                          ' {}'.format(' '.join([str(x) for x in bash_options]))
                          + output_call)
    profilefile.write('\n')
    return


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

def create_custom_group():
    architecture = subprocess.run(
        "likwid-perfctr -i | awk '/CPU short:/ {print $NF}'",
        capture_output=True,
        shell = True,
        text=True
    ).stdout.strip("\n")
    if architecture == "":
        architecture = subprocess.run(
            "likwid-perfctr -i | awk '/cpu short:/ {print $NF}'",
            capture_output=True,
            shell = True,
            text=True
        ).stdout.strip("\n")
    if 'Cannot access directory' in architecture:
        SystemExit("Unknown Architecture for likwid, unable to use likwid on this system")
    groups_location = subprocess.run(
        ['which', 'likwid-perfctr'],
        capture_output=True,
        text=True
    ).stdout[:-2]
    perfgroups_location = os.path.abspath(
        os.path.join(
            groups_location,
            '..' if '/bin' not in groups_location else '../..',
            f'share/likwid/perfgroups/{architecture}'
        )
    )
    ls_results = subprocess.run(f"ls {perfgroups_location}", shell=True, capture_output=True, text=True).stdout.strip().split('\n')
    memory_variables = {}
    memory_long_line = ""
    flop_variables = {}
    flop_metric_lines = []
    flop_long_line = ""
    for group in ls_results:
        if "MEM" in group:
            lines = subprocess.run(f"cat {perfgroups_location}/{group}", shell=True, capture_output=True, text=True).stdout.strip().split('\n')
            counter_name_format = ""
            counter_variables = []
            passed_long = False
            for line in lines:
                if "LONG" in line:
                    passed_long = True
                elif "Memory" in line and "bandwidth" in line:
                    output_of_interest = line[line.find('1.0E-06*(') + 9:line.find(')*64.0')]
                    if passed_long:
                        if "SUM(" in line and "_*" in line:
                            counter_name_format = output_of_interest[4:-2]
                        elif "SUM(" in line:
                            counter_name_format = output_of_interest[4:]
                        elif "_*" in line:
                            counter_name_format = output_of_interest[-2]
                        elif "+" in line:
                            counter_name_format = output_of_interest.split("+")[0]
                        memory_long_line = line
                    else:
                        counter_variables += [v for v in output_of_interest.split("+")]
            for variable in counter_variables:
                if variable in memory_variables:
                    pass
                memory_variables[variable] = counter_name_format + (
                    variable[-2:] if variable[-2].isdigit() else variable[-1:])
        elif "FLOPS" in group:
            lines = subprocess.run(["cat", perfgroups_location + "/" + group], capture_output=True,
                                   text=True).stdout.strip().split('\n')
            counter_names = []
            counter_variables = []
            passed_long = False
            for line in lines:
                if "LONG" in line:
                    passed_long = True
                elif "[MFLOP/s]" in line:
                    output_of_interest = line[line.find('1.0E-06*(') + 9:line.find(')/time')]
                    if passed_long:
                        flop_long_line = line
                        counter_names += [v[:(v.find('*') if v.find('*') > 0 else None)] for v in
                                          output_of_interest.split("+")]
                        break
                    else:
                        flop_metric_lines += [line]
                        counter_variables += [v[:(v.find('*') if v.find('*') > 0 else None)] for v in
                                              output_of_interest.split("+")]
            for variable in range(len(counter_variables)):
                if variable in flop_variables:
                    pass
                flop_variables[counter_variables[variable]] = counter_names[variable]

    group_doc_lines = [
        f"SHORT  Custom group to extract FLOP/s, Memory bandwidth in Bytes/s and Operational Intensity in FLOP/Byte for {architecture} architecture\n",
        "\n",
        "EVENTSET\n",
        "FIXC1  ACTUAL_CPU_CLOCK\n",
        "FIXC2  MAX_CPU_CLOCK\n",
        "PMC0   RETIRED_INSTRUCTIONS\n",
        "PMC1   CPU_CLOCKS_UNHALTED\n",
    ]
    group_doc_lines += [f'{k}   {v}\n' for k, v in flop_variables.items()]
    group_doc_lines += f'PMC{len(list(flop_variables.keys()))+2}   MERGE\n'
    group_doc_lines += [f'{k}   {v}\n' for k, v in memory_variables.items()]
    group_doc_lines += [
        "\n",
        "METRICS\n",
    ]
    metric_DP_lines = "+".join(list(flop_variables.keys()))
    metric_memory_sum = "+".join(list(memory_variables.keys()))
    group_doc_lines += [
        f'DP [FLOP/s]  ({metric_DP_lines})/time\n',
        f'Memory Bandwidth [Bytes/s]  ({metric_memory_sum})*64.0/time\n',
        f'Memory data volume [Bytes] ({metric_memory_sum})*64.0\n'
        f'Operational intensity [FLOP/Byte] ({"+".join([k for k in list(flop_variables.keys())])})/(({metric_memory_sum})*64.0)\n',
        "\n",
        "LONG\n",
        "Formulas:\n"
    ]

    group_doc_lines += [
        flop_long_line.replace("[MFLOP/s]", "[FLOP/s]").replace("1.0E-06*", "") + "\n",
        memory_long_line.replace("[MBytes/s]", "[Bytes/s]").replace("1.0E-06*", "") + '\n',
        memory_long_line.replace("bandwidth [MBytes/s]", "data volume [Bytes]")[:-5] + '\n',
        f'Operational intensity [FLOP/Byte] ({list(flop_variables.values())[0] if "ALL" in list(flop_variables.values())[0] else list(flop_variables.values())[0][:-1] + "*"})/(({list(memory_variables.values())[0][:-1]}*)*64.0)\n'
        "-\n"
        "Custom group for PyProfQueue to calculate Operational Intensity for Roofline model"
    ]

    with open(f"{os.getcwd()}/PYPROFQUEUE.txt", 'w') as fp:
        for line in group_doc_lines:
            fp.write(line)

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
        max_x = (maxperf / maxband) * 2
    else:
        max_x = 1

    if Dot:
        if (max_x < code_opint):
            max_x = code_opint

    x_Axis = np.append(np.linspace(0, maxperf / maxband, 10), max_x)
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
    likwid_header = pd.read_csv(likwid_file, header=None, skiprows=1, nrows=1, delimiter='|')
    likwid_dataframe = pd.read_csv(likwid_file, skiprows=[0, 1], header=None, delimiter=',')
    metrics = likwid_dataframe.iloc[0, 1]
    cpu_count = likwid_dataframe.iloc[0, 2]
    header = ["GID", "MetricsCount", "CpuCount", "Total runtime [s]"]
    for metric in range(4, metrics + 4):
        for cpu in range(cpu_count):
            header += [f"Thread {cpu}: {likwid_header.iloc[0, metric]}"]
    likwid_dataframe.columns = header

    keep = []
    for name in header:
        if 'Operational intensity' in name or "[FLOP/s]" in name or "Total runtime [s]" in name:
            keep += [True]
        else:
            keep += [False]
    reduced_dataframe = likwid_dataframe.loc[:, keep]
    time = reduced_dataframe.filter(like='Total runtime [s]').sum(1).values
    op_int = reduced_dataframe.filter(like='Operational intensity').sum(1).values
    flop_s = reduced_dataframe.filter(like='[FLOP/s]').sum(1).values
    return time, op_int, flop_s


def plot_roof_timeseries(likwid_file: str,
                         name_prefix: str,
                         maxperf: float,
                         maxband: float,
                         code_name: str = 'code',
                         log_plot: bool = False):
    time_series, code_opint, code_mflop = read_timeseries(likwid_file)
    points = np.array([code_opint, code_mflop*1.0e-6]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    if maxperf / maxband > 1:
        max_x = (maxperf / maxband) * 2
    else:
        max_x = 1

    if max_x < code_opint.max():
        max_x = code_opint.max()

    x_axis = np.append(np.linspace(0, maxperf / maxband, 10), max_x*1.1)
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
    fig.colorbar(line, ax=axs, label='Time [s]')

    axs.set_xlim(0, max_x*1.1)
    if log_plot:
        axs.set_yscale('log')
        axs.set_ylim(1e-10, maxperf * 3)
        axs.set_ylabel('Performance log([MFLOP/s])')
    else:
        axs.set_ylim(0, maxperf*1.05)
        axs.set_ylabel('Performance [MFLOP/s]')
    axs.set_xlabel('Operational Intensity')
    plt.savefig(name_prefix + '_TimeSeriesRoofline.png', bbox_inches='tight')
