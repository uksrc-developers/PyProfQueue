# PyProfQueue
The package PyProfQueue provides the Script class, which takes the path and name of the bash script to be submitted and 
profiled in order to read in the queue options and add any needed initialisations in order to profile using prometheus 
and likwid.

When initiating a *Script* object, the following arguments are available:
```
script = PyProfQueue.Script(queue_system: str,
                            work_script: str,
                            read_queue_system: str =None,
                            queue_options: dict = None,
                            likwid: bool = False,
                            likwid_req: list = None,
                            prometheus: bool = False,
                            prometheus_req: list = None
                            )   
```
- queue_system: The intended target queue system
- work_script: The bash script which contains the queue options and work to be done
- read_queue_system (Optional: defaults to queue_system): The name of the queue system for which the script was written 
if different from queue_system
- queue_options(Optional): Any queue options to add or override when compared to the work_script 
- likwid (Optional: defaults to False): Bool to determine if likwid should be used
- likwid_req (Optional): Likwid requirements, details can be found in the section about **add_likwid**
- prometheus (Optional: defaults to False): Bool to determine if prometheus should be used
- prometheus_req (Optional): Prometheus requirements, details can be found in the section about **add_prometheus**

The *Script* class has a few methods that are intended for external use, these are:

- **add_likwid**(likwid_req: list, likwid_output: str ='./')
  - Adds necessary initiation to use likwid to create a roof-line model and plot the work_script onto the model
  - This can be used if a *Script* object was not initiated with likwid options, or if they are to be changed
  - likwid_req is a list that should contain the necessary lines for the system in use to be able to use liquid. 
For example, loading the likwid module:
```
likwid_req = ['module load likwid']
```
- **add_prometheus**(prometheus_req: list, prometheus_output: str ='./')
  - Adds necessary initiation to use measure computing resource usage
  - This can be used if a *Script* object was not initiated with prometheus options, or if they are to be changed
  - prometheus_req is a list that should contain the necessary lines for the system in use to be able to use
prometheus.
It is necessary to at least add the following entry:
``` 
prometheus_req = [
    'export PROMETHEUS_SOFTWARE=<Path to Prometheus software>'
]
```

- **change_options**(queue_options: dict)
  - Allows for options to be changed post initiation of a *Script* object, in case the options given in the 
initialisation are no longer desired.

Beyond these three, it is also possible to call the method 'create_profilefile' if one wants to create the bash files. 
This method is called automatically by the submit option and is provided as an optional method to validate the content 
of the files to be submitted.

## Requirements
### Python Packages

For the sake of PyProfQueue, the required python version is at least 3.10, as this package utilises the match 
functionality. In order to run *read_prometheus.py*, the path to a python implementation/environment needs to be 
provided. This implementation needs to have the following packages:
- promql_http_api   
- numpy             
- pytz              
- pandas            
- datetime          

This python implementation does not need to be the same as the one being used to submit the scripts, but does needs to 
be present on the system on which the job is being submitted. By default, these packages are requested to be installed 
with PyProfQueue.

### Non python requirements

In addition to the python requirements listed above, PyProfQueue also needs to have the following software on the system 
to which the job will be submitted:
- [Prometheus](https://prometheus.io/)
- [likwid](https://github.com/RRZE-HPC/likwid)

For prometheus, it is enough to download the software as long as prometheus can be launched by the user without sudo 
rights. For the sake of likwid, it needs to be installed or loaded in such a way that a user could run the following 
command without sudo rights:
```
likwid-perfctr -g MEM_DP -f <executable>
```

## Adding new Queue system compatibility

In order to add new queue system compatibility refer to the block comments in the *Script* class in script.py. Each of 
the four section that needs changes is marked with "Queue System specifics" followed by a {1}, {2}, {3} or {4}.
