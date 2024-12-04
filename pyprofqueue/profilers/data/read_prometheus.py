# Built in Modules
from time import strftime, localtime
from datetime import datetime
import argparse

# External packages
from promql_http_api import PromqlHttpApi
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser(description="Just an example")
parser.add_argument("-o", "--output", type=str, help="output path where data should be stored")
parser.add_argument("-s", "--start_time", type=str, help="start time of the code")
parser.add_argument("-e", "--end_time", type=str, help="end time of the code")
parser.add_argument("-i", "--ip_address", type=str, default="http://localhost:9090",
                    help="IP address of the Prometheus instance")
parser.add_argument("-a", "--store_all", action='store_true', help="store all data from the database")
args = parser.parse_args()


def check_options():
    global args
    if args.output is None:
        exit("output is required")

    if args.start_time is None:
        exit("Start time is required")
    try:
        start_time = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        exit("start time was not defined in the format '%Y-%m-%d %H:%M:%S', "
             "the value was {}".format(str(args.start_time)))

    if args.end_time is None:
        exit("End time is required")
    try:
        end_time = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        exit("end time was not defined in format '%Y-%m-%d %H:%M:%S', "
             "the value was {}".format(str(args.end_time)))

    return start_time, end_time


def prometheus_scrape(connection: PromqlHttpApi, command: str, begin: datetime, end: datetime,
                      given_name: str, name_convention: str = None, step: str = '10s'):
    queue_results = connection.query_range(command, start=begin, end=end, step=step)()['result']
    queue_dict = {}
    for result in queue_results:
        if name_convention is not None:
            key_name = given_name + ' ' + result['metric'][name_convention]
        else:
            key_name = given_name
        queue_dict[key_name] = np.array([[float(x[0]), float(x[1])] for x in result['values']])
    return queue_dict


def prometheus_scrape_all(connection: PromqlHttpApi, begin: datetime, end: datetime, step: str = '5s'):
    queue_results = connection.query_range('{job!=""}', start=begin, end=end, step=step)()['result']
    queue_dict = {}
    for result in queue_results:
        key_name = result['metric']['job'] + '=' + result['metric']['__name__']
        queue_dict[key_name] = np.array([[float(x[0]), float(x[1])] for x in result['values']])
    return queue_dict


def pandas_merge(dictionary: dict, dataframe: pd.DataFrame = None):
    for key in dictionary.keys():
        if dataframe is None:
            dataframe = pd.DataFrame({'Time': dictionary[key][:, 0], key: dictionary[key][:, 1]})
        else:
            dataframe = pd.merge(dataframe, pd.DataFrame({'Time': dictionary[key][:, 0],
                                                          key: dictionary[key][:, 1]}), on='Time')
    return dataframe


def main():
    global args
    api = PromqlHttpApi(args.ip_address)
    start_time, end_time = check_options()
    if args.store_all:
        full_scrape_dict = prometheus_scrape_all(connection=api,
                                                 begin=start_time, end=end_time)
        Full_df = pandas_merge(dictionary=full_scrape_dict)
        Full_df['Time'] = Full_df['Time'].apply(lambda x: strftime('%Y-%m-%d %H:%M:%S', localtime(x)))

        Full_df.to_feather(args.output + '/full_prometheus_data')
    else:
        cpu_usage_dict = prometheus_scrape(connection=api,
                                           command='100 - irate(node_cpu_seconds_total{mode="idle"}[1m])*100',
                                           begin=start_time, end=end_time,
                                           given_name='CPU Usage:', name_convention='cpu')
        Full_df = pandas_merge(dictionary=cpu_usage_dict)

        cpu_iowait_dict = prometheus_scrape(connection=api,
                                            command='irate(node_cpu_seconds_total{mode="iowait"}[1m])*100',
                                            begin=start_time, end=end_time,
                                            given_name='CPU IO Wait:', name_convention='cpu')
        Full_df = pandas_merge(dictionary=cpu_iowait_dict, dataframe=Full_df)

        max_memory_dict = prometheus_scrape(connection=api,
                                        command='(node_memory_MemTotal_bytes)/(1000000000)',
                                        begin=start_time, end=end_time,
                                        given_name='Memory Total [GB]')
        Full_df = pandas_merge(dictionary=max_memory_dict, dataframe=Full_df)

        memory_dict = prometheus_scrape(connection=api,
                                        command='(node_memory_MemTotal_bytes-node_memory_MemAvailable_bytes)/(1000000000)',
                                        begin=start_time, end=end_time,
                                        given_name='Memory Usage [GB]')
        Full_df = pandas_merge(dictionary=memory_dict, dataframe=Full_df)

        disk_write_dict = prometheus_scrape(connection=api,
                                            command='(irate(node_disk_written_bytes_total[1m]))/(1000000000)',
                                            begin=start_time, end=end_time,
                                            given_name='Write:', name_convention='device')
        Full_df = pandas_merge(dictionary=disk_write_dict, dataframe=Full_df)

        disk_read_dict = prometheus_scrape(connection=api,
                                           command='(irate(node_disk_read_bytes_total[1m]))/(1000000000)',
                                           begin=start_time, end=end_time,
                                           given_name='Read:', name_convention='device')
        Full_df = pandas_merge(dictionary=disk_read_dict, dataframe=Full_df)

        network_receive_KB_dict = prometheus_scrape(connection=api,
                                                    command='irate(node_network_receive_bytes_total[1m])/1e3',
                                                    begin=start_time, end=end_time,
                                                    given_name='Received:', name_convention='device')
        Full_df = pandas_merge(dictionary=network_receive_KB_dict, dataframe=Full_df)

        network_send_KB_dict = prometheus_scrape(connection=api,
                                                 command='irate(node_network_transmit_bytes_total[1m])/1e3',
                                                 begin=start_time, end=end_time,
                                                 given_name='Sent:', name_convention='device')
        Full_df = pandas_merge(dictionary=network_send_KB_dict, dataframe=Full_df)

        Full_df['Time'] = Full_df['Time'].apply(lambda x: strftime('%Y-%m-%d %H:%M:%S', localtime(x)))

        Full_df.to_feather(args.output + '/prometheus_data')


if __name__ == '__main__':
    main()