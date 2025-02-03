import json
import matplotlib.pyplot as plt
import os
import argparse
import numpy as np
import re
import sys
import re
import requests

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
parser.add_argument('--directory', type=str)
args = parser.parse_args()

urls = open(args.url, 'r').read().splitlines()
name_to_src = {}
super_script_set = []
sub_script_set = []
granular_info_set = {}
index = {}

# interesting_apis = ['removeItem', 'createTextNode', 'remove', 'removeChild', 'setInterval', 'insertBefore', 'removeEventListener', 'createElement', 'add', 'postMessage', 'about', 'appendChild', 'removeAttribute', 'setTimeout', 'fetch', 'append', 'addEventListener']
interesting_apis = ['removeItem', 'createTextNode', 'remove', 'removeChild', 'setInterval', 'insertBefore', 'removeEventListener', 'createElement', 'add', 'postMessage', 'appendChild', 'removeAttribute', 'setTimeout', 'fetch', 'append']
# actions = ['call', 'set', 'new', 'get']
actions = ['call']#, 'set', 'new', 'get']

def check_if_ad(url, resource):
    original_directory = os.getcwd()
    target_directory = '/root/breakages/Ad-BlockerResearch/2. Resources (js)/blacklist_parser'

    try:
        # Change to the target directory
        os.chdir(target_directory)
        print(f"Changed to directory: {os.getcwd()}")

        # Run the Node.js script
        result = subprocess.run(['node', 'mytest.js', '--url', url, '--resource', resource], capture_output=True, text=True, check=True)

        os.chdir(original_directory)
        print(f"Returned to original directory: {os.getcwd()}")

        # print(result.stdout)
        if result.stdout == '':
            return False
        else:
            return True

    except Exception as e:
        print(f"Error in check_ad: {e}")
        return False

def get_method(src_name_c, offset):
    # Find method
    if src_name_c != '':
        try:
            response = requests.get(src_name_c)
            if response.status_code == 200:
                script_content = response.text
                if len(script_content) > offset:
                    return script_content[offset-5:offset+15]
                else:
                    print(f'script_content wrong. len(script_content) = {len(script_content)} and offset={offset}')
                    return ''
            else:
                script_content = ''
                print(f"Failed to retrieve the script. Status code: {response.status_code}")
                return script_content
        except requests.exceptions.MissingSchema as e:
            print('invalid url --> ', src_name_c)
            return ''
        except Exception as e:
            print(e, src_name_c)
            return ''

def split_unescaped_colons(s):
    # Regular expression pattern to match unescaped colons
    pattern = r'(?<!\\):'
    # Split the string using the pattern
    result = re.split(pattern, s)
    # Replace escaped colons with actual colons in the result
    result = [part.replace(r'\:', ':') for part in result]
    return result

# {"action": "call", "offset": "15618", "func_name": "%appendChild"}
def investigate_apis(keyword, apis_list, src_text):
    # Define the simplified pattern
    pattern_parts = []
    apis = {}
    helper_dict = {}
    for i in apis_list:
        func, offset, key, id = i
        helper_dict[(func, id)] = (key, offset) # THERE CAN BE MANY BUT LETS JUST PICK ONE FOR NOW
        if f'c{offset}:%{func}:' not in pattern_parts:
            pattern_parts.append(f'c{offset}:%{func}:')
    
    # Compile the patterns into regex objects
    regex_objects = [re.compile(pattern) for pattern in pattern_parts]
    # print(helper_dict.keys())

    id_to_src = {}
    last_seen_script = ''
    for string in src_text:
        if string[0] == '$':
            line = split_unescaped_colons(string[1:])
            id_to_src[line[0]] = line[2].replace('\\x0a', '').replace('\\\\n', '')
        elif string[0] == '!':
            if string[1] == '?':
                last_seen_script = '?'
            else:
                last_seen_script = string[1:]
        elif string[0] == 'c':
            for regex in regex_objects:
                if regex.match(string):
                    func = string.split('%')[1].split(':')[0]
                    if (func, last_seen_script) not in helper_dict.keys():
                        continue
                    offset = int(helper_dict[(func, last_seen_script)][1])

                    # get method from src - requests
                    method = get_method(line[1].replace('\\', '').replace('"', ''), offset)

                    try:
                        if keyword in apis:
                            apis[keyword].append((string, helper_dict[(func, last_seen_script)][0], id_to_src[last_seen_script][offset-20:offset+20], method))
                        else:
                            apis[keyword] = [(string, helper_dict[(func, last_seen_script)][0], id_to_src[last_seen_script][offset-20:offset+20], method)]
                        
                        break
                    except Exception as e:
                        # pass
                        print(e)
                        print(id_to_src.keys())
                        sys.exit(0)

    json.dump(apis, open(f'apis/apis_{keyword}.json', 'w'))

substrings_all = ["doubleclick", "securepubads", "pagead2", "adsystem", "chrome-extension://", "ads.adthrive"]
substrings = ["chrome-extension://"]
pattern = '|'.join(re.escape(substring) for substring in substrings)
pattern_all = '|'.join(re.escape(substring) for substring in substrings_all)

for url in urls:
    keyword = ''
    if 'http' in url:
        keyword = url.split('://')[1].split('/')[0]
    else:
        keyword = url.split('/')[0]

    if 'www' in keyword:
        keyword = keyword.split('www.')[1]

    try:
        b = json.load(open(f'{args.directory}_diff/ctrl_{args.extn}_{keyword}.json', 'r'))
        a = json.load(open(f'{args.directory}_diff/{args.extn}_ctrl_{keyword}.json', 'r'))
        # src_file = json.load(open(f'vv8.run1/{args.extn}/{keyword}/intersection.json', 'r'))

        path = f'../generate_vv8_logs_{args.extn}/{args.directory}/{args.extn}/{keyword}/'
        log_file = [f for f in os.listdir(path) if f.endswith('.log')][0]
        src_text = open(f'{path}/{log_file}', 'r').read().splitlines()
        
        log_file = [f for f in os.listdir(path) if f.endswith('.processed')][0]
        src_dict = json.load(open(f'{path}/{log_file}', 'r'))
    except OSError as e:
        continue
    except Exception as e:
        print('Exception2: ', e)
        continue

    # DIFF of all sites
    ## scripts
    tuples = []
    # print('keys = ', len(a['id_to_script'].keys()))
    for key in a['id_to_script'].keys():
        if key in index.keys():
            index[key].append(keyword)
        else:
            index[key] = [keyword]
        src_name = a['id_to_script'][key]['src_name']
        
        ## remove inline scripts
        src_name_c = src_name.replace('\\', '').replace('"', '')
        url_c = url
        if '#' in url:
            url_c = url.split('#')[0] 
        url_c2 = url_c.replace('www.', '')

        if src_name_c == url_c or src_name_c == url_c2:
            print(f'removing inline scripts for url = {url}')
            continue
        
        ## extension related scripts
        if re.search(pattern, src_name) or '/web_accessible_resources' in a['id_to_script'][key]['src'] or 'uBlockOrigin-abrowserextensiontoblockrequests' in a['id_to_script'][key]['src']:
            # print(src_name)
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
    valid_keys = [key for key, src_name in super_script_set]
    for key in a['granular_info'].keys(): 
        # if key not in valid_keys:
        #     # print('Invalid key! Not in ID_TO_SCRIPT')
        #     continue
        for action in a['granular_info'][key]: 
            try: 
                if str(action[0]) not in count.keys(): 
                    count[str(action[0])] = 1 
                else: 
                    count[str(action[0])] += 1 
            except Exception as e:
                print('Exception1: ', action[0])
    # print(count)

    # number of functions in specific action
    functions = {}
    apis_list = []
    for action in actions:
        functions[f'{action}'] = {}
        for key in a['granular_info'].keys():
            try:
                src_name = src_dict['id_to_script'][key]['src_name']
                
                # for fetching via requests 
                src_name_c = src_name.replace('\\', '').replace('"', '')
                
                src = src_dict['id_to_script'][key]['src']
            except Exception as e:
                print(e, key)
                continue
            if check_if_ad(url, src_name) or re.search(pattern_all, src_name) or '/web_accessible_resources' in src or 'uBlockOrigin-abrowserextensiontoblockrequests' in src:
                # print(src_name)
                continue
            for action_elem in a['granular_info'][key]:
                try:
                    if str(action_elem[0]) == f"['action', '{action}']":
                        func = action_elem[2][1][1:]
                        offset = action_elem[1][1]

                        if func in interesting_apis:
                            # FIND ID FROM KEY(md5)
                            id1 = ''
                            for ids in src_dict['id_to_md5'].keys():
                                if src_dict['id_to_md5'][ids] == key:
                                    id1 = ids
                                    print(f'id1: {id1}, key: {key}, keyword: {keyword}')
                                    break

                            # print(func)
                            apis_list.append((func, offset, key, id1))
                            # if len(script_content) > offset:
                            #     apis_list.append((func, offset, key, id1, script_content[offset-5:offset+15]))
                            # else:
                            #     apis_list.append((func, offset, key, id1, ''))
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
    # print(apis_list)
    if apis_list != []:
        investigate_apis(keyword, apis_list, src_text)
    else:
        print('apis_list is empty!')

    granular_info_set[keyword] = [count, functions]


    # INTERSECTION of all sites

# result = {}
# result['index'] = index

# super_script_set = list(super_script_set)
# sub_script_set = list(sub_script_set)

# result['superset'] = sorted(super_script_set, key=lambda x: x[1])
# result['subset'] = sorted(sub_script_set, key=lambda x: x[1])
# result['granular_info'] = granular_info_set

# with open('investigate_scripts_{args.directory}.json', 'w') as f:
#     json.dump(result, f, cls=SetEncoder)
# f.close()

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

    # D = dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1]))
    # plt.figure(figsize=(15, 15))
    # plt.bar(range(len(D)), list(D.values()), align='center')
    # plt.xticks(range(len(D)), list(D.keys()), rotation=90)
    # plt.savefig(f"{action}.jpg")
