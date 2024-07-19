import json
import matplotlib.pyplot as plt
import os
import argparse
import numpy as np
import re

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

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
parser.add_argument('--url', type=str)
args = parser.parse_args()

urls = open(args.url, 'r').read().splitlines()

super_script_set = []
sub_script_set = []
granular_info_set = {}
index = {}

# substrings = ["doubleclick", "securepubads", "pagead2", "adsystem", "chrome-extension://", "ads.adthrive"]
substrings = ["chrome-extension://"]
pattern = '|'.join(re.escape(substring) for substring in substrings)

for url in urls:
    keyword = ''
    if 'http' in url:
        keyword = url.split('://')[1].split('/')[0]
    else:
        keyword = url.split('/')[0]

    if 'www' in keyword:
        keyword = keyword.split('www.')[1]

    try:
        b = json.load(open(f'diff_logs/ctrl_{args.extn}_{keyword}.json', 'r'))
        a = json.load(open(f'diff_logs/{args.extn}_ctrl_{keyword}.json', 'r'))

        path = f'./vv8_logs/{args.extn}/{keyword}/'
        log_file = [f for f in os.listdir(path) if f.endswith('.processed')][0]
        src_dict = json.load(open(f'{path}/{log_file}', 'r'))
    except Exception as e:
        print(e)
        continue
    
    #### scripts
    tuples = []
    for key in a['id_to_script'].keys():
        if key in index.keys():
            index[key].append(keyword)
        else:
            index[key] = [keyword]
        src_name = a['id_to_script'][key]['src_name']
        if re.search(pattern, src_name) or '/web_accessible_resources' in a['id_to_script'][key]['src'] or 'uBlockOrigin-abrowserextensiontoblockrequests' in a['id_to_script'][key]['src']:
            print(src_name)
            continue
        tuples.append((key, src_name))
        
    if super_script_set == []:
        super_script_set = set(tuples)
        sub_script_set = set(tuples)
    else:
        super_script_set = super_script_set | set(tuples)
        sub_script_set = sub_script_set & set(tuples)

    #### granular_info
    # number of each calls
    count = {}
    for key in a['granular_info'].keys(): 
        for action in a['granular_info'][key]: 
            try: 
                if str(action[0]) not in count.keys(): 
                    count[str(action[0])] = 1 
                else: 
                    count[str(action[0])] += 1 
            except Exception as e:
                print(action[0])
    # print(count)

    # number of functions in specific action
    functions = {}
    actions = ['call', 'set', 'new', 'get']
    for action in actions:
        functions[f'{action}'] = {}
        for key in a['granular_info'].keys():
            for action_elem in a['granular_info'][key]:
                try:
                    if str(action_elem[0]) == f"['action', '{action}']":
                        func = action_elem[2][1]
                        # if 'setTimeout' in func:
                        #     print(src_dict['id_to_script'][key]['src_name'])
                        if func in functions[f'{action}']:
                            functions[f'{action}'][func] += 1
                        else:
                            functions[f'{action}'][func] = 1
                    # print(action) 
                except Exception as e: 
                    print(e)
    # # print(functions)
    # print(dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1])))
        functions[f'{action}'] = dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1]))

    granular_info_set[keyword] = [count, functions]

result = {}
result['index'] = index

super_script_set = list(super_script_set)
sub_script_set = list(sub_script_set)

result['superset'] = sorted(super_script_set, key=lambda x: x[1])
result['subset'] = sorted(sub_script_set, key=lambda x: x[1])
result['granular_info'] = granular_info_set

with open('investigate_scripts.json', 'w') as f:
    json.dump(result, f, cls=SetEncoder)
f.close()

    # # number of each calls
    # count = {}
    # for key in a['granular_info'].keys(): 
    #     for action in a['granular_info'][key]: 
    #         try: 
    #             if str(action[0]) not in count.keys(): 
    #                 count[str(action[0])] = 1 
    #             else: 
    #                 count[str(action[0])] += 1 
    #         except Exception as e:
    #             print(action[0])
    # print(count)

    # # number of functions in specific action
    # functions = {}
    # action = 'call'
    # functions[f'{action}'] = {}
    # for key in a['granular_info'].keys():
    #     for action_elem in a['granular_info'][key]:
    #         try:
    #             if str(action_elem[0]) == f"['action', '{action}']":
    #                 func = action_elem[2][1]
    #                 if 'setTimeout' in func:
    #                     print(src_dict['id_to_script'][key]['src_name'])
    #                 if func in functions[f'{action}']:
    #                     functions[f'{action}'][func] += 1
    #                 else: 
    #                     functions[f'{action}'][func] = 1
    #             # print(action) 
    #         except Exception as e: 
    #             print(e)
    # # print(functions)
    # print(dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1])))

    # # D = dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1]))
    # # plt.figure(figsize=(15, 15))
    # # plt.bar(range(len(D)), list(D.values()), align='center')
    # # plt.xticks(range(len(D)), list(D.keys()), rotation=90)
    # # plt.savefig(f"{action}.jpg")