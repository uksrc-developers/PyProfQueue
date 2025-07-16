import os
import h5py
import subprocess
import numpy as np
import pandas as pd
from os import listdir
import matplotlib.pyplot as plt
from os.path import isfile, join
from numpy.f2py.auxfuncs import throw_error

def find_nth_instance(string_to_search, character_of_interest, n):
    start = string_to_search.find(character_of_interest)
    while start >= 0 and n > 1:
        start = string_to_search.find(character_of_interest, start + 1)
        n -= 1
        if start < 0:
            throw_error(f"{string_to_search} does not contain {n} instances of {character_of_interest}")
    return start


def rfind_nth_instance(string_to_search, character_of_interest, n):
    end = string_to_search.rfind(character_of_interest)
    while end >= 0 and n > 1:
        end = string_to_search.rfind(character_of_interest, 0, end)
        n -= 1
    if end < 0:
        throw_error(f"{string_to_search} does not contain {n} instances of {character_of_interest}")
    return end

def h5py_dataset_iterator(g, prefix=''):
    for key in g.keys():
        item = g[key]
        path = '{}/{}'.format(prefix, key)
        if isinstance(item, h5py.Dataset):  # test for dataset
            yield (path, item)
        elif isinstance(item, h5py.Group):  # test for group (go down)
            yield from h5py_dataset_iterator(item, path)


def get_dataframe(filename: str):
    dataframes = {}
    i = 0
    with h5py.File(filename, 'r') as f:
        for (path, dset) in h5py_dataset_iterator(f):
            DataPath = path
        dataframes[f"{DataPath[rfind_nth_instance(DataPath, '/', 2)+1:rfind_nth_instance(DataPath, '/', 1)]}_{i}"] = pd.read_hdf(filename, key=DataPath)
        i += 1
    if len(dataframes.keys()) <= 0:
        throw_error(f"No dataset was found in {filename}")
    else:
        return dataframes


def get_multiple_dataframes(slurm_path:str, job_info: dict):
    for d in job_info:
        dataframes = {}
        dataframes.update(get_dataframe(f"{slurm_path}/{job_info[d]['job_id']}_profile.h5"))
        job_info[d].update(dataframes)
    return job_info


def get_job_id(job_path: str, slurm_path:str) -> dict:
    log_path = job_path + "/toil/logs"
    if not os.path.isdir(slurm_path):
        subprocess.run(f'mkdir {slurm_path}', shell=True)
    job_info = {}
    files = [file for file in [f for f in listdir(log_path) if isfile(join(log_path, f))] if "out.log" in file]
    os.chdir(slurm_path)
    for file in files:
        job_id = file[file[:-8].rfind(".") + 1:-8]
        try:
            if not os.path.isfile(f"{slurm_path}/{job_id}_profile.h5"):
                subprocess.run(f'sh5util -S -j {job_id} -o {slurm_path}/{job_id}_profile.h5', shell=True)
        except: pass
        job_info[file[:file.rfind(job_id) - 1][file[:file.rfind(job_id) - 1].rfind(".") + 1:]] = {"job_id": job_id}
    return job_info


def get_job_details(job_path: str, slurm_path :str) -> dict:
    job_info = get_job_id(job_path, slurm_path)
    results_path = None
    name = None
    for fname in os.listdir(job_path):
        if os.path.isdir(job_path + os.sep + fname):
            if "_results" in fname:
                results_path = job_path + os.sep + fname
                name = fname[:fname.rfind("_")]
                break
    if name is None:
        throw_error(f"No '_results' directory was found in: {job_path}")
    with open(f'{results_path}/{name}.out', 'r') as file:
        for line in file:
            if line[0] == "[":
                result_list = eval(line)
                job_number = result_list[2][
                             find_nth_instance(result_list[2], '_', 2) + 1:find_nth_instance(result_list[2], '_', 3)]
                workpath = result_list[2][find_nth_instance(result_list[2], '_', 3) + 1:]
                job_info[job_number]["workpath"] = workpath
                memory = None
                cpus_per_task = None
                for result in result_list[2:]:
                    if '--mem=' in result:
                        memory = result[6:]
                    if '--cpus-per-task=' in result:
                        cpus_per_task = result[16:]
                if memory is None:
                    memory = "No Memory requirements set"
                if cpus_per_task is None:
                    cpus_per_task = "No CPU per task requirements set"
                job_info[job_number]["memory"] = memory
                job_info[job_number]["cpus_per_task"] = cpus_per_task
            else:
                break
    return job_info


def get_profiling_data_by_path(job_path: str):
    slurm_path = job_path + "/slurm_profiling"
    job_info = get_job_details(job_path, slurm_path)
    job_info = get_multiple_dataframes(slurm_path, job_info)
    return job_info

def get_profiling_data_by_id(job_id, sbatch_script):
    if not os.path.isfile(f"{job_id}_profile.h5"):
        subprocess.run(f'sh5util -S -j {job_id} -o {job_id}_profile.h5', shell=True)
    job_info = {"job_id": job_id}
    with open(f'{sbatch_script}', 'r') as file:
        for line in file:
            if "#SBATCH " in line:
                if "--mem" in line:
                    job_info["memory"] = line[find_nth_instance(line, " ", 2)+1:]
                elif "--cpus-per-task" in line:
                    job_info["cpus_per_task"] = line[find_nth_instance(line, " ", 2)+1:]
            else:
                break
    return job_info


def plot_profiling_data(job_path = None, job_id = None, sbatch_script = None):
    if job_id is not None and sbatch_script is not None:
        jobs_info = get_profiling_data_by_id(job_id, sbatch_script)
        return jobs_info
    elif job_id is not None:
        jobs_info = get_profiling_data_by_path(job_path)
        for job_number, job_info in jobs_info.items():
            for key in job_info.keys():
                if "Task" in key and len(job_info[key]) > 2:
                    fig, ax = plt.subplots(nrows=3, ncols=1, layout='constrained', sharex=True, figsize=(10, 8))
                    fig.suptitle(f"Step {job_number}: {job_info['workpath']}")
                    try:
                        cpu_count = int(job_info["cpus_per_task"])
                    except:
                        cpu_count = 1
                    ax[0].fill_between(job_info[key]["ElapsedTime"],
                             job_info[key]["CPUUtilization"]/cpu_count,
                             0, linestyle='-', alpha=0.9)
                    ax[0].axhline(y=100, color = 'k', linestyle='--')
                    ax[0].set_title("Mean CPU usage")
                    ax[0].set_ylim(0,120)
                    ax[0].set_ylabel("% CPU Utilization", rotation=90)

                    ax[1].fill_between(job_info[key]["ElapsedTime"],
                                       (job_info[key]["RSS"] + job_info[key]["Pages"]*4)/1000000,
                             0, label="RAM usage", linestyle='-', alpha=0.9)
                    ax[1].set_title("RAM usage")
                    ax[1].axhline(y=(float(job_info["memory"])/1000), color = 'k', linestyle='--', label="Requested ram")
                    ax[1].set_ylabel("GB", rotation=90)
                    ax[1].set_ylim(0,(float(job_info["memory"])/1000) * 1.2)
                    ax[1].legend()

                    ax[2].fill_between(job_info[key]["ElapsedTime"],
                             job_info[key]["ReadMB"]/1000,
                             0, label="Read", linestyle='-', alpha=0.9, color='b')
                    ax[2].fill_between(job_info[key]["ElapsedTime"], 0,
                             -job_info[key]["WriteMB"]/1000, label="Write", linestyle='-', alpha=0.9, color='r')
                    ax[1].axhline(y=0, color = 'k', linestyle='--')
                    ax[2].set_title("I/O usage")
                    ax[2].set_ylabel("GB", rotation=90)
                    ax[2].set_xlabel("Elapsed time (s)")
                    ax[2].legend()

                    plt.savefig(f"{job_path}/slurm_profiling/{job_number}_{key}.png")
    else:
        raise Exception("No job_path OR job_id with sbatch_script given.")
    return jobs_info
