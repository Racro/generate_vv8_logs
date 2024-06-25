import os
from collections import Counter
import math 

def count_keyword_in_file(file_path, keyword):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content.count(keyword)

def find_top_n_files_with_close_frequencies(file_list, keyword):
    # Step 1: Count the keyword occurrences in each file
    file_keyword_counts = []
    for file_path in file_list:
        count = count_keyword_in_file(file_path, keyword)
        file_keyword_counts.append((file_path, count))
    
    # Step 2: Sort the files by the frequency of the keyword
    file_keyword_counts.sort(key=lambda x: x[1], reverse=True)
    file_keyword_counts = file_keyword_counts[:5]
    
    # Step 3: Select the top n files where the frequencies are close to each other
    top_files = []
    mark = file_keyword_counts[0][1]
    for i in range(len(file_keyword_counts)):
        # Check the frequency difference within the current window of size n
        if math.abs(file_keyword_counts[i][1] - mark) < 20:  # Adjust this threshold as needed
            top_files.append(file_keyword_counts[i][0])
    return top_files

# Example usage
file_list = os.listdir('./template_crawler/')
log_files = []
for file in file_list:
    if '.log' in file:
        log_files.append(file)

file_list = [os.path.join('./template_crawler/', file) for file in log_files]
keyword = "www.cricbuzz.com"

top_files = find_top_n_files_with_close_frequencies(file_list, keyword)
for file_path, count in top_files:
    print(f"File: {file_path}, Count: {count}")

