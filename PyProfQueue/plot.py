from datetime import datetime, timedelta
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import matplotlib.dates as mdt

import pandas as pd
import numpy as np
import pytz

alpha = 0.75
DPI = 100
avg_xSize, avg_ySize = 50, 10
MeanMult = 3
LegCols = 7


tz = pytz.timezone('UTC')


def load_df(feather_path: str):
    df = pd.read_feather(feather_path)
    df['Time'] = df['Time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    time_series = df['Time'].values
    return df, time_series


def cwl_pass(cwl_output: str):
    df_steps = pd.DataFrame(columns=['Step', 'Start', 'End'])
    workflow_steps = []
    with open(cwl_output) as f:
        for line in f.readlines():
            if 'starting step' in line or ('[step ' in line and 'completed success' in line) or (
                    '[step ' in line and 'completed skipped' in line) or (
                    '[step ' in line and 'completed permanentFail' in line):
                bracketStart = [i for i, x in enumerate(line) if x == '[']
                bracketEnd = [i for i, x in enumerate(line) if x == ']']
                time = tz.localize(datetime.strptime(line[bracketStart[1] + 1:bracketEnd[0]], '%Y-%m-%d %H:%M:%S'))
                if 'starting step' in line:
                    df_steps = pd.concat(
                        [df_steps, pd.DataFrame([{'Step': line[line.index("starting step") + 14:-1], 'Start': time}])],
                        ignore_index=True)
                elif 'completed success' in line:
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'End'] = time
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'Status'] = 'g'
                elif 'completed skipped' in line:
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'End'] = time
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'Status'] = 'y'
                elif 'completed permanentFail' in line:
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'End'] = time
                    df_steps.loc[df_steps['Step'] == line[line.index('[step') + 6:bracketEnd[1]], 'Status'] = 'r'
            if '[workflow' in line:
                bracketStart = [i for i, x in enumerate(line) if x == '[']
                bracketEnd = [i for i, x in enumerate(line) if x == ']']
                workflow = line[bracketStart[5] + 10: bracketEnd[1]]
                if len(workflow) > 1:
                    if workflow not in workflow_steps:
                        workflow_steps += [workflow]
                        df_steps = df_steps.drop(df_steps[df_steps['Step'] == workflow].index)
    df_steps['Start'] = pd.to_datetime(df_steps['Start'])
    df_steps['End'] = pd.to_datetime(df_steps['End'])
    df_steps['Time'] = (df_steps['End'] - df_steps['Start']).dt.total_seconds()
    return df_steps


def plot_shades(df_steps: pd.DataFrame, label: bool = True):
    for index, row in df_steps.iterrows():
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
            plt.axvspan(row['Start'], row['End'] + timedelta(seconds=10), 0,100,
                        alpha=alpha, color=c, label=row['Step'], linestyle='--', hatch=h)
        else:
            plt.axvspan(row['Start'], row['End'] + timedelta(seconds=10), 0,100,
                        alpha=alpha, color=c, linestyle='--', hatch=h)


def plot_profiling(df: pd.DataFrame, time_series: np.array, name_prefix: str, 
                   cwl_file: str = None, label: bool = True, network_three_mean: bool = True,
                   mean_cpu: bool = True, all_cpu: bool = True, memory: bool = True, 
                   network: bool = True, gant: bool = True):
    if cwl_file is not None:
        df_steps = cwl_pass(cwl_file)
    # Mean CPU
    if mean_cpu:
        MeanCPU_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        MeanCPU_figure.suptitle("Mean CPU usage (Percentage)", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        if cwl_file is not None:
            plot_shades(df_steps, label)
        plt.hlines(y=100, linestyle='--', xmin=time_series[0],
                   xmax=time_series[-1], alpha=0.25)
        plt.fill_between(time_series,
                         df[df.filter(like='CPU Usage:').columns].mean(axis='columns') -
                         df[df.filter(like='CPU IO Wait:').columns].mean(axis='columns'),
                         0, label="Mean CPU usage", linestyle='-', alpha=alpha)
        if df[df.filter(like='CPU IO Wait:').columns].mean().sum() > 0.1:
            plt.fill_between(time_series,
                             df[df.filter(like='CPU Usage:').columns].mean(axis='columns'),
                             df[df.filter(like='CPU Usage:').columns].mean(axis='columns') -
                             df[df.filter(like='CPU IO Wait:').columns].mean(axis='columns'),
                             label="Mean CPU IO Wait", linestyle='-', alpha=alpha, color='red')
        plt.ylim([0, 102])
        plt.xlim([time_series[0], time_series[-1]])
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.96, -0.1))
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
                            y2=0, label=cpuUsage, linestyle='-', alpha=alpha)
            if df['CPU IO Wait' + cpu_number].mean() > 0.1:
                ax.fill_between(time_series, df[cpuUsage],
                                df[cpuUsage] - df['CPU IO Wait' + cpu_number],
                                label=cpuUsage, linestyle='-', alpha=alpha, color='red')
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
        if cwl_file is not None:
            plot_shades(df_steps, label)
        plt.fill_between(time_series, df['Memory Usage [GB]'], 0, label="RAM usage [GB]", linestyle='-', alpha=alpha)
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.96, -0.1))
        plt.ylim([0, df['Memory Usage [GB]'].max() * 1.25])
        plt.xlim([time_series[0], time_series[-1]])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("RAM usage [GB]", fontsize=20)
        plt.yticks(fontsize=20)
        plt.savefig(name_prefix + '_Memory_Usage.png', bbox_inches='tight', dpi=DPI)
    # Network Plots
    if network: 
        network_figure = plt.figure(figsize=(avg_xSize, avg_ySize))
        network_figure.suptitle("Network usage [Received positive, Sent negative KB]", fontsize=20)
        plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%y-%m-%d %T'))
        if cwl_file is not None:
            plot_shades(df_steps, label)
        maxY = 0
        minY = 0
        for column in df.filter(like='Received:').columns:
            plt.fill_between(time_series, df[column], 0, label=column, linestyle='-', alpha=alpha)
            if network_three_mean:
                maxY = df[column].mean() * 3
            else:
                if maxY < df[column].max():
                    maxY = df[column].max()
        for column in df.filter(like='Sent:').columns:
            plt.fill_between(time_series, -df[column], 0, label=column, linestyle='-', alpha=alpha)
            if network_three_mean:
                minY = df[column].mean() * 3
            else:
                if minY < df[column].max():
                    minY = df[column].max()
        plt.vlines(0, time_series.min(), time_series.max())
        plt.ylim([-minY * 1.25, maxY * 1.25])
        plt.legend(ncol=LegCols, prop={'size': 20}, framealpha=1, bbox_to_anchor=(0.96, -0.1))
        plt.xlim([time_series[0], time_series[-1]])
        plt.xlabel("Time", fontsize=20)
        plt.xticks(fontsize=20)
        plt.ylabel("Network usage KB", fontsize=20)
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


def plot_roof(name_prefix: str, maxperf: float, maxband: float,
              code_name: str = 'code', code_mflop: float = None, code_opint: float = None):
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
