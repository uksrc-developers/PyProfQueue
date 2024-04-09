# PyProfQueue
The package PyProfQueue provides the Script class, which takes the path and name of
the bash script to be submitted and profiled in order to read in the queue options
and add any needed initialisations in order to profile using prometheus and likwid.

The Script class has a few methods that can be called, these are:

- **add_likwid**(likwid_req: list, likwid_output: str ='./')
  - Adds necessary initiation to use likwid to create a roof-line model
  - likwid_req is a list that should contain the necessary lines for the system in use to be able to use liquid. 
For example, loading the likwid module:
```
likwid_req = ['module load oneAPI_comp', 'module load likwid']
```
- **add_prometheus**(prometheus_req: list, prometheus_output: str ='./')
  - Adds necessary initiation to use likwid to create a roof-line model
  - prometheus_req is a list that should contain the necessary lines for the system in use to be able to use
prometheus.
It is necessary to at least add the following two entries:
``` 
prometheus_req = [
    'export PROMETHEUS_SOFTWARE=<Path to Prometheus software>',
    'export PROMPYTHON=<Path to Python file for read_prometheus.py>'
]
```
- **change_options**(queue_options: dict)
  - Allows for options to be changed post initiation of a Script object, in case the options given in the 
initialisation are no longer desired.

Beyond these three, it is also possible to call the method 'create_profilefile' if one wants to create the
bash files. This method is called automatically by the submit option and is provided as an optional method
to validate the content of the files to be submitted.

## Requirements
### Python Packages

For the sake of PyProfQueue, the required python version is at least 3.10, as this package utilises the match 
functionality. In order to run *read_prometheus.py*, the path to a python implementation/environment needs to 
be provided. This implementation needs to have the following packages:
- promql_http_api   
- numpy             
- pytz              
- pandas            
- datetime          

This python implementation does not need to be the same as the one being used to submit the scripts, but does
need to be present on the system on which the job is being submitted.

### Non python requirements

In addition to the python requirements listed above, PyProfQueue also needs to have the following software on 
the system to which the job will be submitted:
- [Prometheus](https://prometheus.io/)
- [likwid](https://github.com/RRZE-HPC/likwid)

For prometheus, it is enough to download the software as long as prometheus can be launched by the user without 
sudo rights. For the sake of likwid, it needs to be installed or loaded in such a way that a user could run the 
following command without sudo rights:
```
likwid-perfctr -g MEM_DP -f <executable>
```
