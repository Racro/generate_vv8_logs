import json
import matplotlib.pyplot as plt
import os

extn = 'ublock'
keyword = 'mediaite.com'

b = json.load(open(f'ctrl_{extn}.json', 'r'))
a = json.load(open(f'{extn}_ctrl_{keyword}.json', 'r'))

path = f'./vv8_logs/{extn}/{keyword}/'
log_file = [f for f in os.listdir(path) if f.endswith('.processed')][0]
src_dict = json.load(open(f'{path}/{log_file}', 'r'))

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
print(count)

# number of functions in specific action
functions = {}
action = 'call'
functions[f'{action}'] = {}
for key in a['granular_info'].keys():
    for action_elem in a['granular_info'][key]:
        try:
            if str(action_elem[0]) == f"['action', '{action}']":
                func = action_elem[2][1]
                if 'setTimeout' in func:
                    print(src_dict['id_to_script'][key]['src_name'])
                if func in functions[f'{action}']:
                    functions[f'{action}'][func] += 1
                else: 
                    functions[f'{action}'][func] = 1
            # print(action) 
        except Exception as e: 
            print(e)
# print(functions)
print(dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1])))

# D = dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1]))
# plt.figure(figsize=(15, 15))
# plt.bar(range(len(D)), list(D.values()), align='center')
# plt.xticks(range(len(D)), list(D.keys()), rotation=90)
# plt.savefig(f"{action}.jpg")