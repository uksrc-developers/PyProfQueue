from datetime import datetime, timedelta
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import matplotlib.dates as mdt
import pandas as pd
import numpy as np
import pytz

from importlib import resources as impresources
import itertools
import io

from . import data

main_alpha = 0.9
shade_alpha = 0.65
DPI = 100
avg_xSize, avg_ySize = 50, 10
MeanMult = 3
LegCols = 7

tz = pytz.timezone('UTC')

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
    final_init_indicator = 1
    if IP_address is None:
        read_indicators = [0, 1]
    else:
        read_indicators = [0]
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


def load_df(feather_path: str):
    df = pd.read_feather(feather_path)
    df['Time'] = df['Time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    time_series = df['Time'].values
    return df, time_series


def cwl_pass(cwl_output: str):
    df_steps = pd.DataFrame(columns=['Step', 'Start', 'End', 'Status'])
    workflow_steps = []
    with open(cwl_output) as f:
        for line in f.readlines():
            if 'starting step' in line or (
                    '[workflow ' in line and '] start\n' in line) or (
                    ('[step ' in line or '[workflow ' in line) and 'completed success' in line) or (
                    ('[step ' in line or '[workflow ' in line) and 'completed skipped' in line) or (
                    ('[step ' in line or '[workflow ' in line) and 'completed permanentFail' in line):
                    #'completed permanentFail' in line):
                bracketStart = [i for i, x in enumerate(line) if x == '[']
                bracketEnd = [i for i, x in enumerate(line) if x == ']']
                time = tz.localize(datetime.strptime(line[bracketStart[1] + 1:bracketEnd[0]], '%Y-%m-%d %H:%M:%S'))
                if 'starting step' in line:
                    df_steps = pd.concat(
                        [df_steps, pd.DataFrame([{'Step': line[line.index("starting step") + 14:-1], 'Start': time}])],
                        ignore_index=True)
                elif '[workflow ' in line and '] start\n' in line:
                    workflow = line[line.index("[workflow ") + 10:line.index("] start")]
                    df_steps = pd.concat([df_steps, pd.DataFrame([{'Step': workflow, 'Start': time}])],
                                         ignore_index=True)
                    if len(workflow) > 1:
                        if workflow not in workflow_steps:
                            workflow_steps += [workflow]
                else:
                    if '[step ' in line:
                        search = '[step '
                    elif '[workflow ' in line:
                        search = '[workflow '
                    if 'completed success' in line:
                        if 'workflow' in line or line[line.index('[step') + 6:bracketEnd[1]] in workflow_steps:
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'Status'] = 'b'
                        else:
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'Status'] = 'g'
                    elif 'completed skipped' in line:
                        if search == '[workflow ':
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'Status'] = 'm'
                        else:
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'Status'] = 'y'
                    elif 'completed permanentFail' in line:
                        if search == '[workflow ':
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 10:bracketEnd[1]], 'Status'] = 'k'
                        else:
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'End'] = time
                            df_steps.loc[df_steps['Step'] == line[line.index(search) + 6:bracketEnd[1]], 'Status'] = 'r'
    df_steps['Start'] = pd.to_datetime(df_steps['Start'])
    df_steps.loc[df_steps['Status'].isnull(), 'Status'] = 'c'
    df_steps.loc[df_steps['End'].isnull(), 'End'] = df_steps.loc[~df_steps['End'].isnull()]['End'].max()
    df_steps['End'] = pd.to_datetime(df_steps['End'])
    df_steps['Time'] = (df_steps['End'] - df_steps['Start']).dt.total_seconds()
    return df_steps


def plot_shades(df_steps: pd.DataFrame, label: bool = True):
    for index, row in df_steps.iterrows():
        if row['Status'] != 'b' and row['Status'] != 'm' and row['Status'] != 'c':
            try:
                c = next(color)
            except:
                color = iter(cm.terrain(np.linspace(0, 0.9, 8)))
                c = next(color)
            try:
                h = next(hatch)
            except:
                hatch = iter(['/', '|', '-', '+', 'x', 'O', '*'])
                h = next(hatch)

            plt.vlines(row['Start'], 0, 100, colors=c, linestyle='--')
            plt.vlines(row['End'], 0, 100, colors=c, linestyle='--')
            if label:
                plt.axvspan(row['Start'], row['End'] + timedelta(seconds=10), 0, 100,
                            alpha=shade_alpha, color=c, label=row['Step'], linestyle='--', hatch=h)
            else:
                plt.axvspan(row['Start'], row['End'] + timedelta(seconds=10), 0, 100,
                            alpha=shade_alpha, color=c, linestyle='--', hatch=h)


def plot_prom_profiling(df: pd.DataFrame,
                        time_series: np.array,
                        name_prefix: str,
                        mean_cpu: bool = True,
                        all_cpu: bool = True,
                        memory: bool = True,
                        io_plot: bool = True,
                        network: bool = True,
                        network_three_mean: bool = True,
                        gant: bool = True,
                        cwl_file: str = None,
                        label: bool = True):
    if cwl_file is not None:
        df_steps = cwl_pass(cwl_file)
    # Mean CPU
    if mean_cpu:
        MeanCPU_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        MeanCPU_figure.suptitle("Mean CPU usage (Percentage)", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        plt.gca().yaxis.set_major_formatter('{x:.04f}')
        if cwl_file is not None:
            plot_shades(df_steps, label)
        plt.hlines(y=100, linestyle='--', xmin=time_series[0],
                   xmax=time_series[-1], alpha=0.25)
        plt.fill_between(time_series,
                         df[df.filter(like='CPU Usage:').columns].mean(axis='columns') -
                         df[df.filter(like='CPU IO Wait:').columns].mean(axis='columns'),
                         0, label="Mean CPU usage", linestyle='-', alpha=main_alpha)
        if df[df.filter(like='CPU IO Wait:').columns].mean().sum() > 0.1:
            plt.fill_between(time_series,
                             df[df.filter(like='CPU Usage:').columns].mean(axis='columns'),
                             df[df.filter(like='CPU Usage:').columns].mean(axis='columns') -
                             df[df.filter(like='CPU IO Wait:').columns].mean(axis='columns'),
                             label="Mean CPU IO Wait", linestyle='-', alpha=main_alpha, color='red')
        plt.ylim([0, 102])
        plt.xlim([time_series[0], time_series[-1]])
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.5, -0.1), loc='upper center')
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("CPU usage (%)", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_MeanCPU_Usage.png', bbox_inches='tight', dpi=DPI)
    # All CPUs
    if all_cpu:
        N_Cores = len(df.filter(like='CPU Usage:').columns)
        sub_xSize, sub_ySize = 20, 15
        N_rows = 8
        N_columns = int(N_Cores / N_rows)
        Yscaling = 0.95
        Xscaling = 0.99

        AllCPU = plt.figure(figsize=(sub_xSize, sub_ySize))
        AllCPU.suptitle("Individual CPU usage (Percentage)", fontsize=20)
        cpuNumber = np.array([int(x[-2:]) for x in df.filter(like='CPU Usage:').columns.array])
        Usage_columns = df.filter(like='CPU Usage:').columns.array
        sorted_columns = np.array([x for _, x in sorted(zip(cpuNumber, Usage_columns))])
        for i, cpuUsage in enumerate(sorted_columns):
            row, col = np.abs((i // N_columns) - N_rows), i % N_columns
            location = [((col) / N_columns) * Xscaling + 0.005, (row - 1) / N_rows * Yscaling + 0.01,
                        1 / (N_columns) * Xscaling, (1 / N_rows) * Yscaling]
            ax = AllCPU.add_axes(location)
            title = cpuUsage[10:]
            cpu_number = cpuUsage[9:]
            ax.set_title(title, y=1.0, pad=-14)
            ax.xaxis.set_major_formatter(mdt.DateFormatter('%d-%T'))
            ax.hlines(y=100, linestyle='--', xmin=time_series[0], xmax=time_series[-1], alpha=0.25)
            ax.fill_between(time_series, df[cpuUsage] - df['CPU IO Wait' + cpu_number],
                            y2=0, label=cpuUsage, linestyle='-', alpha=main_alpha)
            if df['CPU IO Wait' + cpu_number].max() > 0.1:
                ax.fill_between(time_series, df[cpuUsage],
                                df[cpuUsage] - df['CPU IO Wait' + cpu_number],
                                label=cpuUsage, linestyle='-', alpha=main_alpha, color='red')
            ax.set_ylim([0, 105])
            ax.set_xlim([time_series[0], time_series[-1]])
            ax.yaxis.set_visible(False)
            ax.xaxis.set_visible(False)
            # ax.locator_params(axis='x', nbins=4)
        plt.savefig(name_prefix + '_AllCPU_Usages.png', bbox_inches='tight', dpi=DPI)
    # Memory Plots
    if memory:
        memory_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        memory_figure.suptitle("RAM usage [GB]", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        plt.gca().yaxis.set_major_formatter('{x:.04f}')
        if cwl_file is not None:
            plot_shades(df_steps, label)
        plt.fill_between(time_series, df['Memory Usage [GB]'], 0, label="RAM usage [GB]", linestyle='-', alpha=main_alpha)
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.5, -0.1), loc='upper center')
        plt.ylim([0, df['Memory Usage [GB]'].max()])
        plt.xlim([time_series[0], time_series[-1]])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("RAM usage [GB]", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_Memory_Usage.png', bbox_inches='tight', dpi=DPI)
    # IO Plots
    if io_plot:
        IO_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        IO_figure.suptitle("IO usage [Write positive, Read negative kB]", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        plt.gca().yaxis.set_major_formatter('{x:.04f}')
        if cwl_file is not None:
            plot_shades(df_steps, label)
        maxY = 0
        minY = 0
        for column in df.filter(like='Write:').columns:
            plt.fill_between(time_series, df[column], 0, label=column, linestyle='-', alpha=main_alpha)
            if maxY < df[column].max():
                maxY = df[column].max()
        for column in df.filter(like='Read:').columns:
            plt.fill_between(time_series, -df[column], 0, label=column, linestyle='-', alpha=main_alpha)
            if minY < df[column].max():
                minY = df[column].max()
        plt.vlines(0, time_series.min(), time_series.max())
        plt.ylim([-minY * 1.25, maxY * 1.25])
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.5, -0.1), loc='upper center')
        plt.xlim([time_series[0], time_series[-1]])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("IO usage kB", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_IO_Usage.png', bbox_inches='tight', dpi=DPI)
    # Network Plots
    if network:
        network_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        network_figure.suptitle("Network usage [Received positive, Sent negative kB]", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        plt.gca().yaxis.set_major_formatter('{x:.04f}')
        if cwl_file is not None:
            plot_shades(df_steps, label)
        maxY = 0
        minY = 0
        for column in df.filter(like='Received:').columns:
            plt.fill_between(time_series, df[column], 0, label=column, linestyle='-', alpha=main_alpha)
            if network_three_mean:
                maxY = df[column].mean() * 3
            else:
                if maxY < df[column].max():
                    maxY = df[column].max()
        for column in df.filter(like='Sent:').columns:
            plt.fill_between(time_series, -df[column], 0, label=column, linestyle='-', alpha=main_alpha)
            if network_three_mean:
                minY = df[column].mean() * 3
            else:
                if minY < df[column].max():
                    minY = df[column].max()
        plt.vlines(0, time_series.min(), time_series.max())
        plt.ylim([-minY * 1.25, maxY * 1.25])
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.5, -0.1), loc='upper center')
        plt.xlim([time_series[0], time_series[-1]])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("Network usage kB", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_Network_Usage.png', bbox_inches='tight', dpi=DPI)
    # Gant Plot
    if gant and cwl_file is not None:
        Gant_figure = plt.figure(figsize=(50, 100))
        Gant_figure.suptitle("Gant Chart", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        plt.barh(y=df_steps['Step'],
                 width=(mdt.date2num(df_steps['End']) - mdt.date2num(df_steps['Start']) + 0.001),
                 left=mdt.date2num(df_steps['Start']), color=df_steps['Status'])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.xlim([time_series[0], time_series[-1]])
        plt.ylabel("Step", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_StepGant.png', bbox_inches='tight', dpi=DPI)
    return