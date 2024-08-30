import os
from collections import Counter
import numpy as np 
import argparse

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
parser.add_argument('--site', type=str)
parser.add_argument('--directory', type=str)
args = parser.parse_args()

def count_keyword_in_file(file_path, keyword):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content.count(keyword)
    except Exception as e:
        print(e)
        return 0
    
def find_top_file_with_highest_frequency(file_list, keyword):
    # Step 1: Count the keyword occurrences in each file
    file_keyword_counts = []
    for file_path in file_list:
        if 'ServiceWorker' in file_path:
            continue
        count = count_keyword_in_file(file_path, keyword)
        file_keyword_counts.append((file_path, count))
    
    if len(file_keyword_counts) > 0:
        # Step 2: Sort the files by the frequency of the keyword
        file_keyword_counts.sort(key=lambda x: x[1], reverse=True)
        return file_keyword_counts[:5]
    else:
        return ''

# Example usage
file_list = os.listdir('./')
log_files = []
for file in file_list:
    if '.log' in file:
        log_files.append(file)

file_list = [os.path.join('./', file) for file in log_files]

keyword = ''
if 'http' in args.site:
    keyword = args.site.split('://')[1].split('/')[0]
else:
    keyword = args.site.split('/')[0]

if 'www' in keyword:
    keyword = keyword.split('www.')[1]

top_files = find_top_file_with_highest_frequency(file_list, keyword)

if not top_files == '': 
    if not os.path.exists(f'{args.directory}/{args.extn}/{keyword}'):
        os.makedirs(f'{args.directory}/{args.extn}/{keyword}')
    
    for file in top_files:
        if file[1] < 15:
            continue
        os.system(f'mv {file[0]} {args.directory}/{args.extn}/{keyword}')
