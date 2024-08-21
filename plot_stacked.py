import json
import matplotlib.pyplot as plt
import numpy as np

f = json.load(open('investigate_scripts_no_inline.json', 'r'))

plot_apis = {}
plot_actions = {}

for key in f['granular_info'].keys():
    for action in f['granular_info'][key][1]:
        if action not in plot_apis.keys():
            plot_apis[action] = {}
        for api in f['granular_info'][key][1][action]:
            if api not in plot_apis[action]:
                plot_apis[action][api] = [f['granular_info'][key][1][action][api]]
            else:
                plot_apis[action][api].append(f['granular_info'][key][1][action][api])

for key in f['granular_info'].keys():
    for action in f['granular_info'][key][0]:
        if action not in plot_actions.keys():
            plot_actions[action] = [f['granular_info'][key][0][action]]
        else:
            plot_actions[action].append(f['granular_info'][key][0][action])

print(f.keys())
print(plot_apis.keys())

plt.figure(figsize=(15, 15))
max_len = max(len(val) for val in plot_actions.values())
# Pad the shorter lists with zeros
padded_values = [val + [0] * (max_len - len(val)) for val in plot_actions.values()]
padded_values = np.array(padded_values)
# Create an array of zeros for the bottom parameter in barh
bottoms = np.zeros(len(plot_actions))
# Create horizontal bar plot
for i in range(max_len):
    plt.barh(range(len(plot_actions)), padded_values[:, i], left=bottoms)
    bottoms += padded_values[:, i]
# plt.bar(range(len(plot_actions)), list(plot_actions.values()), align='center')
plt.yticks(range(len(plot_actions)), list(plot_actions.keys()), fontsize= 15)
plt.savefig("plots_no_inline/all_actions_stacked.jpg")

plt.figure(figsize=(15, 50))
# Find the maximum length of the value lists
max_len = max(len(val) for val in plot_apis['call'].values())
# Pad the shorter lists with zeros
padded_values = [val + [0] * (max_len - len(val)) for val in plot_apis['call'].values()]
padded_values = np.array(padded_values)
# Create an array of zeros for the bottom parameter in barh
bottoms = np.zeros(len(plot_apis['call']))
# Create horizontal bar plot
for i in range(max_len):
    plt.barh(range(len(plot_apis['call'])), padded_values[:, i], left=bottoms)
    bottoms += padded_values[:, i]
# plt.barh(range(len(plot_apis['call'])), list(plot_apis['call'].values()), align='center')
plt.yticks(range(len(plot_apis['call'])), list(plot_apis['call'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_calls_stacked.jpg")

plt.figure(figsize=(15, 60))
max_len = max(len(val) for val in plot_apis['new'].values())
# Pad the shorter lists with zeros
padded_values = [val + [0] * (max_len - len(val)) for val in plot_apis['new'].values()]
padded_values = np.array(padded_values)
# Create an array of zeros for the bottom parameter in barh
bottoms = np.zeros(len(plot_apis['new']))
# Create horizontal bar plot
for i in range(max_len):
    plt.barh(range(len(plot_apis['new'])), padded_values[:, i], left=bottoms)
    bottoms += padded_values[:, i]
# plt.barh(range(len(plot_apis['new'])), list(plot_apis['new'].values()), align='center')
plt.yticks(range(len(plot_apis['new'])), list(plot_apis['new'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_news_stacked.jpg")

plt.figure(figsize=(15, 35))
max_len = max(len(val) for val in plot_apis['set'].values())
# Pad the shorter lists with zeros
padded_values = [val + [0] * (max_len - len(val)) for val in plot_apis['set'].values()]
padded_values = np.array(padded_values)
# Create an array of zeros for the bottom parameter in barh
bottoms = np.zeros(len(plot_apis['set']))
# Create horizontal bar plot
for i in range(max_len):
    plt.barh(range(len(plot_apis['set'])), padded_values[:, i], left=bottoms)
    bottoms += padded_values[:, i]
# plt.barh(range(len(plot_apis['set'])), list(plot_apis['set'].values()), align='center')
plt.yticks(range(len(plot_apis['set'])), list(plot_apis['set'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_sets_stacked.jpg")