import os
from collections import Counter
import numpy as np 
import argparse

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
args = parser.parse_args()

def count_keyword_in_file(file_path, keyword):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content.count(keyword)

def find_top_file_with_highest_frequency(file_list, keyword):
    # Step 1: Count the keyword occurrences in each file
    file_keyword_counts = []
    for file_path in file_list:
        count = count_keyword_in_file(file_path, keyword)
        file_keyword_counts.append((file_path, count))
    
    if len(file_keyword_counts) > 0:
        # Step 2: Sort the files by the frequency of the keyword
        file_keyword_counts.sort(key=lambda x: x[1], reverse=True)
        return file_keyword_counts[0][0]
    else:
        return ''

# Example usage
file_list = os.listdir('./')
log_files = []
for file in file_list:
    if '.log' in file:
        log_files.append(file)

file_list = [os.path.join('./', file) for file in log_files]
keyword = "www.geeksforgeeks.org"

top_file = find_top_file_with_highest_frequency(file_list, keyword)

if not top_file == '': 
    if not os.path.exists(f'vv8_logs/{args.extn}'):
        os.makedirs(f'vv8_logs/{args.extn}')
    os.system(f'mv {top_file} vv8_logs/{args.extn}')
    os.system('rm -rf vv8-*.log')