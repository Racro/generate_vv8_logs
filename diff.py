import json
import numpy as np
import re
import argparse
import os 

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
parser.add_argument('--url', type=str, default='control')
parser.add_argument('--directory', type=str, default='control')
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

def convert_to_tuple(list1): # list1 is typically [[[], []], [[], []]]
    ret = set()
    for i in range(len(list1)):
        try:
            temp = []
            for j in list1[i]:
                # print('list type:', type(set(j)))
                temp.append(tuple(j))
            # print(temp)
            ret.add(tuple(temp))
        except Exception as e:
            print('0'*50)
            print(e)
            # print(list1[i])

    return ret

# normalizing the unique idenitfier in parent inside 'granular_info'
def is_match(s):
    # Define the regex pattern
    pattern = r'^\{(\d+),([A-Za-z]+)\}$'
    
    # Check if the string matches the pattern
    match = re.match(pattern, s)
    try:
        if match:
            return True, match.group(2)
        else:
            return False, ''
    except Exception as e:
        print(e)
        print(s)

urls = open(args.url, 'r').read().splitlines()
for url in urls:
    keyword = ''
    if 'http' in url:
        keyword = url.split('://')[1].split('/')[0]
    else:
        keyword = url.split('/')[0]

    if 'www' in keyword:
        keyword = keyword.split('www.')[1]

    try:
        ctrl = json.load(open(f'./{args.directory}/control/{keyword}/intersection.json', 'r'))
        adb = json.load(open(f'../generate_vv8_logs_{args.extn}/{args.directory}/{args.extn}/{keyword}/intersection.json', 'r'))
        
        # for key in ctrl['granular_info'].keys():
        #     for i in range(len(ctrl['granular_info'][key])):
        #         for j in range(len(ctrl['granular_info'][key][i])):
        #             if ctrl['granular_info'][key][i][j][0] == 'parent':
        #                 found, strr = is_match(ctrl['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     ctrl['granular_info'][key][i][j] = ["parent", f"{{1,{strr}}}"]
        #             elif ctrl['granular_info'][key][i][j][0] == 'receiver':
        #                 found, strr = is_match(ctrl['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     ctrl['granular_info'][key][i][j] = ["receiver", f"{{1,{strr}}}"]
        #             elif ctrl['granular_info'][key][i][j][0] == 'script':
        #                 found, strr = is_match(ctrl['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     ctrl['granular_info'][key][i][j] = ["script", f"{{1,{strr}}}"]
        #             elif ctrl['granular_info'][key][i][j][0] == 'rest':
        #                 found, strr = is_match(ctrl['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     ctrl['granular_info'][key][i][j] = ["rest", f"{{1,{strr}}}"]

        # for key in adb['granular_info'].keys():
        #     for i in range(len(adb['granular_info'][key])):
        #         for j in range(len(adb['granular_info'][key][i])):
        #             if adb['granular_info'][key][i][j][0] == 'parent':
        #                 found, strr = is_match(adb['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     adb['granular_info'][key][i][j] = ["parent", f"{{1,{strr}}}"]
        #             elif adb['granular_info'][key][i][j][0] == 'receiver':
        #                 found, strr = is_match(adb['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     adb['granular_info'][key][i][j] = ["receiver", f"{{1,{strr}}}"]
        #             elif adb['granular_info'][key][i][j][0] == 'script':
        #                 found, strr = is_match(adb['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     adb['granular_info'][key][i][j] = ["script", f"{{1,{strr}}}"]
        #             elif adb['granular_info'][key][i][j][0] == 'rest':
        #                 found, strr = is_match(adb['granular_info'][key][i][j][1]) 
        #                 if found:
        #                     adb['granular_info'][key][i][j] = ["rest", f"{{1,{strr}}}"]


        ### NOT SURE WHAT THIS PIECE OF CODE WAS DOING
        # ctrl_n2s = {}
        # adb_n2s = {}
        # for key in ctrl['name_to_src']:
        #     if len(ctrl['name_to_src'][key]) > 1:
        #         ctrl_n2s[key] = ctrl['name_to_src'][key]
        # for key in adb['name_to_src']:
        #     if len(adb['name_to_src'][key]) > 1:
        #         adb_n2s[key] = adb['name_to_src'][key]

        ctrl_adb = {}
        adb_ctrl = {}

        ctrl_script_set = set(ctrl['id_to_script'].keys())
        adb_script_set = set(adb['id_to_script'].keys())
        ctrl_granular_set = set(ctrl['granular_info'].keys())
        adb_granular_set = set(adb['granular_info'].keys())

        # ctrl_adb['name_to_src'] = ctrl_n2s
        ctrl_adb['name_to_src'] = ctrl['name_to_src']
        ctrl_adb['id_to_script'] = {}
        ctrl_adb['granular_info'] = {}
        # adb_ctrl['name_to_src'] = adb_n2s
        adb_ctrl['name_to_src'] = adb['name_to_src']
        adb_ctrl['id_to_script'] = {}
        adb_ctrl['granular_info'] = {}
        

        for key in (ctrl_script_set - adb_script_set):
            ctrl_adb['id_to_script'][key] = ctrl['id_to_script'][key]

        for key in (adb_script_set - ctrl_script_set):
            adb_ctrl['id_to_script'][key] = adb['id_to_script'][key]

        for key in ctrl_granular_set:
            try:
                if key not in adb_granular_set:
                    # diff = list(convert_to_tuple(ctrl['granular_info'][key]))
                    diff = []
                else:
                    # print(ctrl['granular_info'][key])
                    diff = list(convert_to_tuple(ctrl['granular_info'][key]) - convert_to_tuple(adb['granular_info'][key]))

                if diff == []:
                    continue
                ctrl_adb['granular_info'][key] = diff
            except Exception as e:
                print('1'*50)
                print(e)
                break

        for key in adb_granular_set:
            if key not in ctrl_granular_set:
                # diff = list(convert_to_tuple(adb['granular_info'][key]))
                diff = []
            else:
                diff = list(convert_to_tuple(adb['granular_info'][key]) - convert_to_tuple(ctrl['granular_info'][key]))

            if diff == []:
                continue
            adb_ctrl['granular_info'][key] = diff

        if not os.path.exists(f'{args.directory}_diff'):
            os.makedirs(f'{args.directory}_diff')
        json.dump(ctrl_adb, open(f'{args.directory}_diff/ctrl_{args.extn}_{keyword}.json', 'w'), cls=SetEncoder)
        json.dump(adb_ctrl, open(f'{args.directory}_diff/{args.extn}_ctrl_{keyword}.json', 'w'), cls=SetEncoder)
    except OSError as e:
        continue
    except Exception as e:
        print('Exception 1: ', e)

