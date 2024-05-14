# PyProfQueue

___
___
PyProfQueue serves as a python package that can take in existing bash scripts, add prometheus monitoring calls and 
likwid performance measure calls, and submit the script to an HPC queue system on the users' behalf.
___
___
# Description

___
___
PyProfQueue takes existing bash scripts, scrapes any queue options from them and creates two temporary files. The first 
file, is equivalent to the user provided bash script but with queue options removed from it. The second bash script is
the file that will be submitted to the queue on the users' behalf. This second temporary script contains the queue 
options provided by the user as well as any additionally required commands to initialise prometheus monitoring and/or
likwid performance measuring of the users bash script.
## Component details
___
The two main components for users of PyProfQueue are the *Script* class and the *submit* function.
### Script Class
The *Script* class is used in the following way, and the following options are available:
```
script = PyProfQueue.Script(queue_system: str,
                            work_script: str,
                            read_queue_system: str =None,
                            queue_options: dict = None,
                            profiling: dict = None
                            )   
```
|           Option           | Description                                                                                                                        |
|:--------------------------:|------------------------------------------------------------------------------------------------------------------------------------|
|        queue_system        | The intended target queue system (Supports Slurm and PBS Torque)                                                                   |
|        work_script         | The bash script which contains the queue options and work to be done                                                               |
|read_queue_system (Optional)| The name of the queue system for which the script was written if it was written for a queue system                                 |
|  queue_options (Optional)  | Any queue options to add or override when compared to the work_script                                                              |
|    profiling (Optional)    | Dictionary with keys representing which profiler to use with values of dictionaries listing profiler options such as "requirements"|


The options *queue_options* that PyProfQueue currently supports are:
- 'user'
  - The user ID of the system with which to submit the job (requires admin rights usually)
- 'nodes'
  - The number of nodes to be requested.
- 'cores'
  - The number of cores each task will need.
- 'tasks'
  - The number of tasks to perform.
- 'time'
  - The walltime this job is allowed to run for in hh:mm:ss.
- 'partition'
  - The specific queue/partition to submit to.
- 'account'
  - The account to charge for the used resources.
- 'subname'
  - Name of the submitted job.
- 'workdir'
  - The directory in which the work should be done.
- 'output'
  - The file, including path, to write the STDOUT to.

Any *Script* object, then comes with three additional methods intended to be used by users. These methods are:

#### change_options
```
change_options(queue_options: dict)
```
- Allows for options to be changed post initiation of a *Script* object, in case the options given in the 
initialisation are no longer desired.

As an example usage of *change_options*, let us assume we have a *Script* object that has the option {'time': 12:00:00}
meaning that the script would be terminated if it takes longer than 12 hours. We now wish to make it so that the script
is allowed to run for 24 hours. So we use the following:
```
script.change_options(queue_options={'time':'24:00:00'})
```
*change_options* does not overwrite existing options if they aren't specifically listed to be changed.
### submit function
The *submit* function serves as the point of execution for PyProfQueue. When called, it will take the given *Script* 
object, and submit it to the queue system the *Script* object is configured for.
```
PyProfQueue.submit(script: Script,
                   tmp_work_script: str = './tmp_workfile.sh',
                   tmp_profile_script: str = './tmp_profilefile.sh',
                   bash_options: list = [''],
                   leave_scripts: bool = True,
                   test: bool = False):
```
|           Option            | Description                                                                                                                                                                                                        |
|:---------------------------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|           script            | *Script* object to be submitted to queue                                                                                                                                                                           |
| tmp_work_script (Optional)  | Desired name of temporary work script. Defaults to "tmp_workfile.sh".                                                                                                                                              |
|tmp_profile_script (Optional)| Desired name of temporary profile script. Defaults to "tmp_profilefile.sh".                                                                                                                                        |
|   bash_options (Optional)   | List of options that the user provided bash script may require. Defaults to [' '].                                                                                                                                 |
|  leave_scripts (Optional)   | Boolean to determine if the temporary scripts should be left or removed after submission. Defaults to True                                                                                                         |
|       test (Optional)       | Boolean to determine if the script should be submitted, or if the command that would be used should be printed to the terminal. Additionally, this leaves the temporary scripts in tackt so they can be inspected. |

### plot.load_df function
This function reads the prometheus database created by using prometheus profiling with *PyProfQueue* and stores it 
into a pandas.DataFrame. This then has the time converted into the format of "yyyy-mm-dd HH:MM:SS" for user readability.
The times at which datapoints exist are then also given out as a numpy.array on top of returning the dataframe. 

|    Option    | Description                             |
|:------------:|-----------------------------------------|
| feather_path | path to the scraped prometheus database |
### plot.plot_profiling function
This function plots the results of a prometheus profiling effort. It is compatible with additional features for 
[Common Workflow Language](https://www.commonwl.org/) (CWL) workflows, if the output from a CWL call is saved to a file.

|            Option            | Description                                                                                                                      |
|:----------------------------:|----------------------------------------------------------------------------------------------------------------------------------|
|              df              | pandas.DataFrame of the prometheus profiling data. Obtained from load_df                                                         |
|         time_series          | numpy.array of the times at which data was collected. Obtained from load_df                                                      |
|         name_prefix          | Desired path and name prefix for the plots                                                                                       |
|network_three_mean (Optional) | Boolean on if the network y-limit should be restricted to three times the mean value                                             |
|     mean_cpu (Optional)      | Boolean on if the mean_cpu usage should be plotted                                                                               |
|      all_cpu (Optional)      | Boolean on if all cpu usages should be plotted                                                                                   |
|      memory (Optional)       | Boolean on if the memory usage should be plotted                                                                                 |
|      network (Optional)      | Boolean on if the network usage should be plotted                                                                                |
|     cwl_file (Optional)      | Path to a text file containing the ouput of CWL, if it was used to run a workflow. This is used to shade when each step occured. |
|       label (Optional)       | Boolean to label each CWL step on shaded graphs if cwl_file was provided                                                         |
|       gant (Optional)        | Boolean on if a gant chart like plot should be created if CWL was used to run a workflow                                         |

### plot.plot_roof function
This function plots the results of a likwid profiling effort.

|        Option         | Description                                                          |
|:---------------------:|----------------------------------------------------------------------|
|      name_prefix      | Desired path and name prefix for the plot                            |
|        maxperf        | Float of the maximum performance listed in likwid output file        |
|      maxband          | Float of the maximum memory bandwidth listed in likwid output file   |
| code_name (Optional)  | String of what to call the code in the legend of the plot            |
| code_mflop (Optional) | Float of the codes MFLOP/s listed in the likwid output               |
| code_opint (Optional) | Float of the codes Operational Intensity listed in the likwid output |

___
##  In- and Outputs
___
### Inputs
The inputs to the *Script* class and *submit* function have already been described above, what has not been described
in detail in the input file that users provide. Users must provide the bash script that they wish to profile and submit
to a queue system. If a bash script with no queue options is provided, then the *read_queue_system* option can be left
off, or set to None. In this case, unless both *read_queue_system* and *queue_system* are set to None, *queue_options* 
have to be provided. If queue options are available in the script then *read_queue_system* should be set to the name
of the queue system that the original script was intended for.
#### Likwid specific inputs
In order to use likwid, the key 'likwid' needs to be used in the *profiling* option for the *Script* object. This key 
then needs to have a value of "requirements" which contains a list of all commands that need to be executed prior to 
being able to use likwid on the HPC system the script is being submitted to. If, for example, a simple module loading
is required, it could look like this
```python
profiling = {"likwid": {"requirements":["module load likwid"]}}
```
#### Prometheus specific inputs
In order to use prometheus, the key 'prometheus' needs to be used in the *profiling* option for the *Script* object. 
This key then needs to have a value of "requirements" which has to contain the path to the prometheus instance to use, 
or it has to contain "ip_address" which then has an IP address, stored as a string, of a pre-existing prometheus
instance that can be scraped. Here is an example of both, where "<path/to/prometheus>" is used to represent the path
to the prometheus instance the user would want to use.
```python
profiling = {"prometheus": {"requirements":["export PROMETHEUS_SOFTWARE=<path/to/prometheus>"]}}
# OR
profiling = {"prometheus": {"ip_address":["127.0.0.1:9090"]}}
```

#### Both likwid and prometheus
Here is an example of how the dictionary could look, if both likwid and prometheus were to be used:
```python
profiling = {"likwid": {"requirements":["module load likwid"]}, 
             "prometheus": {"requirements":["export PROMETHEUS_SOFTWARE=<path/to/prometheus>"]}
             }
```

### Outputs
The output of the *Script* class, is an object that contains all the given options, file paths and other variables 
needed in order to create the bash scripts that can be submitted to a queue system. The outputs from *submit* 
depend on the given options. If the *test* and *leave_scripts* are set to **False**, then the output of *submit* is 
the same as the output of the submission command for the respective queue system being used. If *test* or 
*leave_scripts* are set to **True** then the output includes two bash scripts. The first contains the original work 
to be performed, the other contains all the necessary variable declarations and command calls in order to perform 
the profiling of the given bash script. It is the profiling script that is submitted to the queue. Additionally,
if *test* is **True**, then the command line will output what command would be used in order to submit the job, but
the command will not actually be called.

For the plotting functions, the outputs are .png files of each requested plot.
___
## Example usage
___
Let us look at a toy example to show how this script would be used. Let us assume we have an HPC system that uses slurm.
This system requires loading the likwid module if we want to use it, and we have downloaded the prometheus codes to the
directory **/home/Software** and ensured that we can execute both without sudo commands. Let us assume we have the 
following bash script:
```bash
#!/bin/bash
#SBATCH -A example_project
#SBATCH -c 16
#SBATCH -N 1
#SBATCH -o /home/queue_work/%x.%j/output.out
#SBATCH -p example_partition
#SBATCH -J TestSubmission
#SBATCH -n 1
#SBATCH -t 00:05:00

echo "The first option was:"
echo ${1}
echo "The second option was:"
echo ${2}
```

The following example python script can be used to add the prometheus monitoring, likwid performance profiling and to 
submit the script to the queue. We have listed the queue options in the *Script* object initialisation even though it 
would pull them from the bash script in order to show an example of how they would be listed.
```python 
import PyProfQueue as ppq

ProfileScript = ppq.Script(queue_system='slurm',
                           work_script='./tmp_workfile.sh',
                           queue_options={
                               'workdir': '/home/queue_work/%x.%j',
                               'account': 'example_project',
                               'cores': '16',
                               'nodes': '1',
                               'output': '/home/queue_work/%x.%j/output.out',
                               'partition': 'example_partition',
                               'name': 'TestSubmission',
                               'tasks': '1',
                               'time': '00:05:00'},
                           profiling={"likwid": {'requirements': ['module load oneAPI_comp/2021.1.0',
                                                                  'module load likwid/5.2.0']},
                                      "prometheus": {'requirements': ['export PROMETHEUS_SOFTWARE=/home/Software']}
                                      })

ppq.submit(ProfileScript, 
           tmp_work_script = './test_workfile.sh',
           tmp_profile_script = './test_profilefile.sh',
           bash_options=['"Hello "', '"World!"'],
           test=True)
```
This python script prints the following to the command line, but does not submit a job:
```
The following command would be used to submit a job to the queue:
sbatch ./test_profilefile.sh
```
Following this, it has created two files, test_workfile.sh and test_profilefile.sh. test_workfile.sh should look like
the original bash script provided by the user, but with the options removed:
```bash
#!/bin/bash

# Any work that users may want to do on an HPC system, including environment initialisations
# For the sake of example we simply call
echo "The first option was:"
echo ${1}
echo "The second option was:"
echo ${2}
```

While test_profiliefile.sh contains all the necessary initialisations and terminations for prometheus and likwid to run
and provide the correct outputs. The entire file won't be listed here as it is quite length, however we will 
state how the test_workfile.sh is called within test_profilefile.sh
```bash
likwid-perfctr -g MEM_DP -f bash ./test_workfile.sh  "Hello " "World!"
```
___

## Software Requirements
___
### Python Requirements
For the sake of PyProfQueue, the required python version is at least 3.10, as this package utilises the match 
functionality.
- numpy
- pytz
- pyarrow
- matplotlib
- promql_http_api==0.3.3
- pandas<=2.2.1
### Non Python Requirements
In addition to the python requirements listed above, PyProfQueue also needs to have the following software on the system 
to which the job will be submitted:
- [node_exporter](https://prometheus.io/docs/guides/node-exporter/)
- [prometheus](https://prometheus.io/)
- [likwid](https://github.com/RRZE-HPC/likwid)

For prometheus and node_exporter, it is enough to download the software as long as they can both be launched by the 
user without sudo rights. However, they need to be put into the same directory so that the following directory structure
is in place:
```md
${PROMETHEUS_SOFTWARE}
├── node_exporter
│   └── node_exporter
└── prometheus
    ├── prometheus
    └── prometheus.yml
```
Where *node_exporter/node_exporter* is the executable for node_exporter, *prometheus/prometheus* is the executable for 
prometheus, and *prometheus/prometheus.yml* is the configuration file to be used for prometheus.

For the sake of likwid, it needs to be installed or loaded in, in such a way that a user could run the following 
command without sudo rights:
```
likwid-perfctr -g MEM_DP -f <executable>
```
___
## Container Compatibility
___
This package does not require a container and since it submits to a queue, we do not know how recommended it is to 
use it from within a container.
___
## Hardware Requirements
___
As of now, no minimum Hardware requirements are known other than those forced by python 3.10, prometheus, node_exporter
and likwid.
___
## Directory Structure
___
```md
PyProfQueue
├── PyProfQueue
│   ├── profilers
│   │   ├── data
│   │   │   ├── read_prometheus.py
│   │   │   ├── _template_commands.txt
│   │   │   ├── likwid_commands.txt
│   │   │   └── prometheus_commands.txt
│   │   ├── __init__.py
│   │   ├── _template_profiler.py
│   │   ├── likwid.py
│   │   └── prometheus.py
│   ├── __init__.py
│   ├── plot.py
│   ├── script.py
│   └── submission.py
├── ReadMe.md
└── setup.py
```
The directory *PyProfQueue/PyProfQueue* contains the *plot.py*. *script.py* and *submission.py* scripts which contain the 
definition of the plotting functions, *Script* class and *submission()* function respectively.

The directory *PyProfQueue/PyProfQueue/profilers* contains scripts of the individual profilers that PyProfQueue is 
compatible with including a template version that can be used to add additional profiling software compatibility to 
PyProfQueue. *PyProfQueue/PyProfQueue/profilers/data* contains a script called *read_prometheus.py* which is used to 
scrape the prometheus database into a pandas dataframe. It also includes the text files that list the bash commands 
needed to initialise run and end profiling software, as well as a template version for adding more profiling software 
compatibility.



The base directory contains the ReadMe.md file, and the setup.py file so that the package can be installed.
___
## Adding new Queue systems
___
A future goal for development on PyProfQueue is to add additional queue suport beyond slurm and torque. In order to add 
new queue system compatibility refer to the block comments in the *Script* class in script.py. Each of the four section 
that needs changes is marked with "Queue System specifics" followed by a {1}, {2}, {3} or {4}.
___
## Adding new Profiling software
___
In order to add new profiling software compatibility, a new script would need to be added to the 
*PyProfQueue/PyProfQueue/profilers* directory. This script would need to have the name of how the specific profiler
should be called, as well as the following two functions:
- define_initialise(profilefile: io.TextIOWrapper, profilerdict: dict = None)
- define_end(profilefile: io.TextIOWrapper)

Both of these functions can read from a .txt file, which can be stored in *PyProfQueue/PyProfQueue/profilers/data*.
The first *define_initialise* is there to add any variable declarations or code to the profiling bash script that would
be needed in order to run the profiler. The second is any calls needed in order to terminate, or collect data post 
running the profiler.

If the profiler being added needs to be used in order to execute the user provided bash script, then the function 
*define_run(profilefile: io.TextIOWrapper, bash_options: list, tmp_work_script: str)* should be defined in the 
script for the specific profiler. This function should write the needed command to use the profilerto the profiling 
file.
___
___


# To Do
___
___
- Update the package format to follow more modern conventions for installing requirements
  - e.g. add pyproject.toml 
- Add Vtune profiling support
- Add Linaro Forge profiling support
___
___
# UKSRC related Links
This package was initially created because of the Jira Ticket [TEAL-391](https://jira.skatelescope.org/browse/TEAL-391).

A Confluence page of what the prometheus and likwid results look like can be found on the 
[SKAO Confluence](https://confluence.skatelescope.org/display/SRCSC/Profiling+LOFAR+VLBI+Workflow)

### Developers and Contributors
___
Developers:
- Keil, Marcus (UCL)
- Qaiser, Fawada (Durham)

Contributors:
- Morabito, Leah (Durham)
- Yates, Jeremy (UCL)
___