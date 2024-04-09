# Built in Modules
from time import strftime, localtime
from datetime import datetime
import sys
# External packages
from promql_http_api import PromqlHttpApi
import pandas as pd
import numpy as np
import pytz

n = sys.argv
tz = pytz.timezone('UTC')
# export START=$(date -d '1 hour ago' "+%+4Y-%m-%d %T")
start_time = tz.localize(datetime.strptime(n[1], '%Y-%m-%d %H:%M:%S'))
# export END=$(date +'%+4Y-%m-%d %T')
end_time = tz.localize(datetime.strptime(n[2], '%Y-%m-%d %H:%M:%S'))

api = PromqlHttpApi('http://localhost:9090')



cpu_usage_data = api.query_range('100 - irate(node_cpu_seconds_total{mode="idle"}[1m])*100', start=start_time, end=end_time, step='10s')()['result']
cpu_usage_dict = {}
for i in cpu_usage_data:
    name = 'cpu: ' + i['metric']['cpu']
    cpu_usage_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])

cpu_iowait_data = api.query_range('irate(node_cpu_seconds_total{mode="iowait"}[1m])*100', start=start_time, end=end_time, step='10s')()['result']
cpu_iowait_dict = {}
for i in cpu_iowait_data:
    name = 'cpu: ' + i['metric']['cpu']
    cpu_iowait_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])

memory_GB_data = api.query_range('(node_memory_MemTotal_bytes-node_memory_MemAvailable_bytes)/(1000000000)', start=start_time, end=end_time, step='10s')()['result']
memory_GB_dict = {}
for i in memory_GB_data:
    name = 'RAM (GB)'
    memory_GB_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])

disk_write_GB_data = api.query_range('(irate(node_disk_written_bytes_total[1m]))/(1000000000)', start=start_time, end=end_time, step='10s')()['result']
disk_write_GB_dict = {}
for i in disk_write_GB_data:
    name = 'Write: ' + i['metric']['device']
    disk_write_GB_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])


disk_read_GB_data = api.query_range('(irate(node_disk_read_bytes_total[1m]))/(1000000000)', start=start_time, end=end_time, step='10s')()['result']
disk_read_GB_dict = {}
for i in disk_read_GB_data:
    name = 'Read: ' + i['metric']['device']
    disk_read_GB_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])

network_receive_KB_data = api.query_range('irate(node_network_receive_bytes_total[1m])/1e3', start=start_time, end=end_time, step='10s')()['result']
network_receive_KB_dict = {}
for i in network_receive_KB_data:
    name = 'Received: ' + i['metric']['device']
    network_receive_KB_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])

network_send_KB_data = api.query_range('irate(node_network_transmit_bytes_total[1m])/1e3', start=start_time, end=end_time, step='10s')()['result']
network_send_KB_dict = {}
for i in network_send_KB_data:
    name = 'Sent: ' + i['metric']['device']
    network_send_KB_dict[name] = np.array([[float(x[0]), float(x[1])] for x in i['values']])


first = True
for k in cpu_usage_dict.keys():
    if first:
        first = False
        Full_df = pd.DataFrame({'Time:': cpu_usage_dict[k][:, 0], 'Usage ' + k: cpu_usage_dict[k][:, 1]})
        Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': cpu_usage_dict[k][:, 0], 'IO wait ' + k: cpu_iowait_dict[k][:, 1]}), on='Time:')
    else:
        Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': cpu_usage_dict[k][:, 0], 'Usage ' + k: cpu_usage_dict[k][:, 1]}), on='Time:')
        Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': cpu_usage_dict[k][:, 0], 'IO wait ' + k: cpu_iowait_dict[k][:, 1]}), on='Time:')

Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': memory_GB_dict["RAM (GB)"][:,0], "Memory Usage [GB]": memory_GB_dict["RAM (GB)"][:, 1]}), on='Time:')

for k in disk_write_GB_dict.keys():
    Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': disk_write_GB_dict[k][:, 0], k: disk_write_GB_dict[k][:, 1]}), on='Time:')

for k in disk_read_GB_dict.keys():
    Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': disk_read_GB_dict[k][:, 0], k: disk_read_GB_dict[k][:, 1]}), on='Time:')

for k in network_receive_KB_dict.keys():
    Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': network_receive_KB_dict[k][:, 0], k: network_receive_KB_dict[k][:, 1]}),
                       on='Time:')

for k in network_send_KB_dict.keys():
    Full_df = pd.merge(Full_df, pd.DataFrame({'Time:': network_send_KB_dict[k][:, 0], k: network_send_KB_dict[k][:, 1]}),
                       on='Time:')

Full_df['Time:'] = Full_df['Time:'].apply(lambda x: strftime('%Y-%m-%d %H:%M:%S', localtime(x)))

Full_df.to_feather(n[3]+'/prometheus_data')
