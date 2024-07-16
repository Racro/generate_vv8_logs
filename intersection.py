import json
import os
import numpy as np
import argparse
from memory_profiler import profile
import ijson
import sys

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
parser.add_argument('--url', type=str, default='control')
args = parser.parse_args()

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

urls = open(args.url, 'r').read().splitlines()

# @profile
def main():
    try:
        for url in urls:
            keyword = ''
            if 'http' in url:
                keyword = url.split('://')[1].split('/')[0]
            else:
                keyword = url.split('/')[0]

            if 'www' in keyword:
                keyword = keyword.split('www.')[1]

            log_files = [f for f in os.listdir(f'./vv8_logs/{args.extn}/{keyword}/') if f.endswith('.processed')]
            print(log_files)

            log_file_path = f'./vv8_logs/{args.extn}/{keyword}/{log_files[0]}'
            parser = ijson.parse(open(log_file_path, 'r'))
            for prefix, event, value in parser:
                if prefix.endswith('.key'):
                    print(value)
            # for item in parser:
            #     print(item['value'])


            master = {}
            count = 0
            for log_file in log_files:
                log_file_path = f'./vv8_logs/{args.extn}/{keyword}/{log_file}'
                # master[count] = json.load(open(log_file_path, 'r'))
                master[count] = ijson.items(open(log_file_path, 'r'), 'item')
                count = count + 1

            for item in master[0]:
                print(item['key'])
            sys.exit(1)

            # keys - 'id_to_script' & 'granular_info'
            common_script_set = set(master[0]['id_to_script'].keys())
            granular_info_set = set(master[0]['granular_info'].keys())

            for key in master.keys():
                common_script_set = common_script_set & set(master[key]['id_to_script'].keys())
                granular_info_set = granular_info_set & set(master[key]['granular_info'].keys())

            intersection_dict = {}
            intersection_dict['id_to_script'] = {}
            intersection_dict['granular_info'] = {}

            for key in common_script_set:
                intersection_dict['id_to_script'][key] = master[0]['id_to_script'][key]

            for key in granular_info_set:
                if key not in common_script_set:
                    print(f"{keyword} - WEIRD OBSERVATION!")
                    # print(master[0]['granular_info'][key])
                    continue

                set_of_dicts = set()
                for d in master[0]['granular_info'][key]:
                    set_of_dicts.add(tuple(d.items()))
                
                intersection_dict['granular_info'][key] = set_of_dicts
                for index in master.keys():
                    set_of_dicts = set()
                    for d in master[index]['granular_info'][key]:
                        set_of_dicts.add(tuple(d.items()))
                    intersection_dict['granular_info'][key] = intersection_dict['granular_info'][key] & set_of_dicts

            json.dump(intersection_dict, open(f'./vv8_logs/{args.extn}/{keyword}/intersection.json', 'w'), cls=SetEncoder)
    except Exception as e:
        print(args.url, e)

if __name__ == "__main__":
    main()