import json
import os
import numpy as np
import argparse
from memory_profiler import profile
import ijson
import sys
import multiprocessing

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

# @profile
def main(arguments):
    extn, keyword = arguments
    try:
        log_files = [f for f in os.listdir(f'./vv8_logs/{extn}/{keyword}/') if f.endswith('.processed')]
        # print(log_files)

        log_file_path = f'./vv8_logs/{extn}/{keyword}/{log_files[0]}'
        # parser = ijson.parse(open(log_file_path, 'r'))
        # for prefix, event, value in parser:
        #     if prefix.endswith('.key'):
        #         print(value)
        # for item in parser:
        #     print(item['value'])

        base = []
        next = []
        common_script_set = set()
        granular_info_set = set()
        intersection_dict = {}
        intersection_dict['id_to_script'] = {}
        intersection_dict['granular_info'] = {}
        for log_file in log_files:
            log_file_path = f'./vv8_logs/{extn}/{keyword}/{log_file}'
            if base == []:
                base = json.load(open(log_file_path, 'r'))
                # keys - 'id_to_script' & 'granular_info'
                common_script_set = set(base['id_to_script'].keys())
                granular_info_set = set(base['granular_info'].keys())
            else:
                next = json.load(open(log_file_path, 'r'))
                # master[count] = ijson.items(open(log_file_path, 'r'), 'item')
                common_script_set = common_script_set & set(next['id_to_script'].keys())
                granular_info_set = granular_info_set & set(next['granular_info'].keys())

        for key in common_script_set:
            intersection_dict['id_to_script'][key] = base['id_to_script'][key]

        for log_file in log_files[1:]:
            log_file_path = f'./vv8_logs/{extn}/{keyword}/{log_file}'
            next = json.load(open(log_file_path, 'r'))
            for key in granular_info_set:
                if key not in common_script_set:
                    print(f"{keyword} - {key} - WEIRD OBSERVATION!")
                    # print(master[0]['granular_info'][key])
                    # continue

                set_of_dicts = set()
                for d in base['granular_info'][key]:
                    set_of_dicts.add(tuple(d.items()))
                intersection_dict['granular_info'][key] = set_of_dicts
                    
                set_of_dicts = set()
                for d in next['granular_info'][key]:
                    set_of_dicts.add(tuple(d.items()))
                intersection_dict['granular_info'][key] = intersection_dict['granular_info'][key] & set_of_dicts

        json.dump(intersection_dict, open(f'./vv8_logs/{extn}/{keyword}/intersection.json', 'w'), cls=SetEncoder)
    except Exception as e:
        print(keyword, e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get Extension')
    parser.add_argument('--extn', type=str, default='control')
    parser.add_argument('--url', type=str)
    args = parser.parse_args()

    urls = open(args.url, 'r').read().splitlines()
    arguments = []
    for url in urls:
        keyword = ''
        if 'http' in url:
            keyword = url.split('://')[1].split('/')[0]
        else:
            keyword = url.split('/')[0]

        if 'www' in keyword:
            keyword = keyword.split('www.')[1]
        arguments.append((args.extn, keyword))

    try:
        # Create a pool of worker processes
        with multiprocessing.Pool() as pool:
            # Map the worker function to the arguments
            results = pool.map(main, arguments)
            
        # Print the results
        # for i, (stdout, stderr) in enumerate(results):
        #     print(f'Result from worker {i}:')
        #     print('stdout:', stdout)
        #     print('stderr:', stderr)
    except Exception as e:
        print(e)
    # main(args.extn, keyword)