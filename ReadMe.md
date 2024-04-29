# PyProfQueue

---
PyProfQueue serves as a python package that can take in existing bash scripts, add prometheus monitoring calls and 
likwid performance measure calls, and submit the script to an HPC queue system on the users' behalf.
___
# Description

---
PyProfQueue takes existing bash scripts, scrapes any queue options from them and creates two temporary files. The first 
file, is equivalent to the user provided bash script but with queue options removed from it. The second bash script is
the file that will be submitted to the queue on the users' behalf. This second temporary script contains the queue 
options provided by the user as well as any additionally required commands to initialise prometheus monitoring and/or
likwid performance measuring of the users bash script.
## Component details
The two main components for users of PyProfQueue are the *Script* class and the *submit* function.
### Script Class
The *Script* class is used in the following way, and the following options are available:
```
script = PyProfQueue.Script(queue_system: str,
                            work_script: str,
                            read_queue_system: str =None,
                            queue_options: dict = None,
                            likwid: bool = False,
                            likwid_req: list = None,
                            prometheus: bool = False,
                            prometheus_ip: str = None, 
                            prometheus_req: list = None
                            )   
```
|           Option           | Description                                                                                                                                                                     |
|:--------------------------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|        queue_system        | The intended target queue system (Supports Slurm and PBS Torque)                                                                                                                |
|        work_script         | The bash script which contains the queue options and work to be done                                                                                                            |
|read_queue_system (Optional)| The name of the queue system for which the script was written if it was written for a queue system                                                                              |
|  queue_options (Optional)  | Any queue options to add or override when compared to the work_script                                                                                                           |
|     likwid (Optional)      | Bool to determine if likwid should be used. Defaults to False.                                                                                                                  |
|   likwid_req (Optional)    | Likwid requirements, details can be found in the section about **add_likwid**. Required if likwid Bool is True.                                                                 |
|   prometheus (Optional)    | Bool to determine if prometheus should be used. Defaults to False.                                                                                                              |
|  prometheus_ip (Optional)  | IP address of a pre-existing prometheus instance, not providing an address will result in launching a prometheus instance with the address 'http://localhost:9090'              |
| prometheus_req (Optional)  | Prometheus requirements, details can be found in the section about **add_prometheus**. Required if prometheus Bool is True and no pre-existing prometheus instance is provided. |


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
#### add_likwid
```
add_likwid(likwid_req: list)
```
- Adds necessary initiation to use likwid to create a roof-line model and plot the work_script onto the model
- This can be used if a *Script* object was not initiated with likwid options, or if they are to be changed
- likwid_req is a list that should contain the necessary lines for the system in use to be able to use liquid. 

For example, loading the likwid module:
```
likwid_req = ['module load likwid']
```
Example usage of *add_likwid* on a system that has the module environment, but where the likwid module requires the
oneApi module to be loaded first:
```
script.add_likwid(likwid_req=['module load oneApi', 'module load likwid'])
```
#### add_prometheus
```
add_prometheus(prometheus_req: list, prometheus_ip: str = None)
```
- Adds necessary initiation to use measure computing resource usage
- This can be used if a *Script* object was not initiated with prometheus options, or if they are to be changed
- prometheus_req is a list that should contain the necessary lines for the system in use to be able to use
prometheus. The example below shows how to define required environment variable **PROMETHEUS_SOFTWARE**. This variable
needs to be the path to the prometheus software to be used. This only required if prometheus_ip is not being provided.
- prometheus_ip is a string which is the ip-address of a pre-existing prometheus instance, if it exists.
``` 
prometheus_req = [
    'export PROMETHEUS_SOFTWARE=<Path to Prometheus software>'
]
```
Example usage of *add_prometheus* where we provide the path to the **PROMETHEUS_SOFTWARE** directory:
```
script.add_prometheus(prometheus_req = ['export PROMETHEUS_SOFTWARE=/home/PrometheusSoftware'])
```
The **PROMETHEUS_SOFTWARE** directory should have the following structure at minimum, but may contain more files 
depending on where it was stored and the version of node_exporter and prometheus being used.
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


##  In- and Outputs
### Inputs
The inputs to the *Script* class and *submit* function have already been described above, what has not been described
in detail in the input file that users provide. Users must provide the bash script that they wish to profile and submit
to a queue system. If a bash script with no queue options is provided, then the *read_queue_system* option can be left
off, or set to None. In this case, unless both *read_queue_system* and *queue_system* are set to None, *queue_options* 
have to be provided. If queue options are available in the script then *read_queue_system* should be set to the name
of the queue system that th


## Example usage
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
                           likwid=True,
                           likwid_req=['module load likwid'],
                           prometheus=True,
                           prometheus_req=['export PROMETHEUS_SOFTWARE=/home/Software'],
                           queue_options={
                               'workdir': '/home/queue_work/%x.%j',
                               'account': 'example_project',
                               'cores': '16',
                               'nodes': '1',
                               'output': '/home/queue_work/%x.%j/output.out',
                               'partition': 'example_partition',
                               'name': 'TestSubmission',
                               'tasks': '1',
                               'time': '00:05:00'
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

## Software Requirements
### Python Requirements
For the sake of PyProfQueue, the required python version is at least 3.10, as this package utilises the match 
functionality.
- numpy
- pytz
- pyarrow
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
## Container Compatibility (If applicable)
This package does not require a container and since it submits to a queue, we do not know how recommended it is to 
use it from within a container.
## Hardware Requirements
As of now, no minimum Hardware requirements are known other than those forced by python 3.10, prometheus, node_exporter
and likwid.
## Directory Structure
```md
PyProfQueue
├── PyProfQueue
│   ├── data
│   │   ├── read_prometheus.py
│   │   ├── likwid_commands.txt
│   │   └── prometheus_commands.txt
│   ├── __init__.py
│   ├── script.py
│   └── submission.py
├── ReadMe.md
└── setup.py
```
The directory *PyProfQueue/data* contains a script called *read_prometheus.py* which is used to scrape the prometheus 
database into a pandas dataframe. It also includes the two text files, *likwid_commands.txt* and 
*prometheus_commands.txt*, which list the bash commands needed to initialise and end likwid and prometheus respectively.

The directory *PyProfQueue/PyProfQueue* contains the *script.py* and *submission.py* scripts which contain the 
definition of the *Script* class and *submission()* function respectively.

The base directory contains the ReadMe.md file, and the setup.py file so that the package can be installed.

## Jira, Confluence and external documentation Links
This package was initially created because of the Jira Ticket [TEAL-391](https://jira.skatelescope.org/browse/TEAL-391).

A Confluence page of what the prometheus and likwid results look like can be found on the 
[SKAO Confluence](https://confluence.skatelescope.org/display/SRCSC/Profiling+LOFAR+VLBI+Workflow)
## Future work

### Adding new Queue system compatibility
A future goal for development on PyProfQueue is to add additional queue suport beyond slurm and torque. In order to add 
new queue system compatibility refer to the block comments in the *Script* class in script.py. Each of the four section 
that needs changes is marked with "Queue System specifics" followed by a {1}, {2}, {3} or {4}.

### Developers and Contributors

---
Developers:
- Keil, Marcus (UCL)

Contributors:
- Morabito, Leah (Durham)
- Qaiser, Fawada (Durham)
- Yates, Jeremy (UCL)
___