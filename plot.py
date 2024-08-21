import json
import matplotlib.pyplot as plt

f = json.load(open('investigate_scripts_no_inline.json', 'r'))

plot_apis = {}
plot_actions = {}

for key in f['granular_info'].keys():
    for action in f['granular_info'][key][1]:
        if action not in plot_apis.keys():
            plot_apis[action] = {}
        for api in f['granular_info'][key][1][action]:
            if api not in plot_apis[action]:
                plot_apis[action][api] = f['granular_info'][key][1][action][api]
            else:
                plot_apis[action][api] += f['granular_info'][key][1][action][api]

for key in f['granular_info'].keys():
    for action in f['granular_info'][key][0]:
        if action not in plot_actions.keys():
            plot_actions[action] = f['granular_info'][key][0][action]
        else:
            plot_actions[action] += f['granular_info'][key][0][action]

print(f.keys())
print(plot_apis.keys())

plt.figure(figsize=(15, 15))
plt.bar(range(len(plot_actions)), list(plot_actions.values()), align='center')
plt.xticks(range(len(plot_actions)), list(plot_actions.keys()), rotation=90, fontsize= 15)
plt.savefig("plots_no_inline/all_actions.jpg")

plt.figure(figsize=(15, 50))
plt.barh(range(len(plot_apis['call'])), list(plot_apis['call'].values()), align='center')
plt.yticks(range(len(plot_apis['call'])), list(plot_apis['call'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_calls.jpg")

plt.figure(figsize=(15, 60))
plt.barh(range(len(plot_apis['new'])), list(plot_apis['new'].values()), align='center')
plt.yticks(range(len(plot_apis['new'])), list(plot_apis['new'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_news.jpg")

plt.figure(figsize=(15, 35))
plt.barh(range(len(plot_apis['set'])), list(plot_apis['set'].values()), align='center')
plt.yticks(range(len(plot_apis['set'])), list(plot_apis['set'].keys()), fontsize=10)
plt.savefig("plots_no_inline/all_sets.jpg")