import re
import jsbeautifier
import os
import json
import hashlib
import sys
import argparse
import multiprocessing
import numpy as np

# remove \n from js
pattern = r'(?<!\\)\\n'

def split_unescaped_colons(s):
    # Regular expression pattern to match unescaped colons
    pattern = r'(?<!\\):'
    # Split the string using the pattern
    result = re.split(pattern, s)
    # Replace escaped colons with actual colons in the result
    result = [part.replace(r'\:', ':') for part in result]
    return result

def extract_js_from_log_line(line):
    # Regular expression to match the filename and JavaScript code part
    js_code_pattern = re.compile(r'(\w+://[\w/._-]+):\s*(.*)')
    match = js_code_pattern.search(line)
    if match:
        filename = match.group(1)
        js_code = match.group(2)
        return filename, js_code
    return None, None

def decode_escape_sequences(js_code):
    try:
        # Replace problematic surrogates
        cleaned_code = js_code.encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
        
        # Decode the escape sequences using 'unicode_escape'
        decoded_string = bytes(cleaned_code, "utf-8").decode("unicode_escape")
        
        # Handle any surrogate pairs
        corrected_string = decoded_string.encode('utf-16', 'surrogatepass').decode('utf-16')
        
        return corrected_string
    except UnicodeDecodeError as e:
        return f"UnicodeDecodeError: {e}"
# def decode_escape_sequences(js_code):
#     # Decode escape sequences
#     return bytes(js_code, "utf-8").decode("unicode_escape")

def beautify_js(js_code):
    # Beautify the JavaScript code
    return jsbeautifier.beautify(js_code)

def find_rogue_files(directory, threshold=0.5):
    file_sizes = []
    for filename in os.listdir(directory):
        if filename.endswith(".log"):
            file_path = os.path.join(directory, filename)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            file_sizes.append((filename, file_size))
    
    if not file_sizes:
        return []

    max_size = max(size for _, size in file_sizes)
    rogue_threshold = max_size * threshold

    # sizes = np.array([size for _, size in file_sizes])
    # mean_size = np.mean(sizes)
    # std_dev = np.std(sizes)
    # print(mean_size)
    # print(std_dev)
    # rogue_files = [(filename, size) for filename, size in file_sizes if size < (mean_size - std_dev)]
    rogue_files = [(filename, size) for filename, size in file_sizes if size < rogue_threshold]
    return [t[0] for t in rogue_files]

# def detect_rogue_files_in_directories(directories):
#     rogue_files_dict = {}
#     for directory in directories:
#         rogue_files = find_rogue_files(directory)
#         if rogue_files:
#             rogue_files_dict[directory] = rogue_files
#     return rogue_files_dict

def process_log_file(arguments):
    try:
        log_file_path, keyword, extn, url = arguments
        # print(log_file_path, keyword, extn)
        name_to_src = {}
        id_to_md5 = {}
        id_to_script = {}
        id_to_script['window'] = {}
        granular_info = {}

        cfg = [] ###
        
        # Read the log file
        with open(log_file_path, 'r') as file:
            lines = file.readlines()

        last_seen_script = 0
        last_seen_api_calls = [] ###
        for line in lines:
            if line[-1] == '\n':
                line = line[:-1]
            try:
                # filename, js_code = extract_js_from_log_line(line)
                if line[:3] == '~0x':
                    id_to_script['context'] = hashlib.md5(line.encode('utf-8')).hexdigest()[:8]
                elif line[0] == '@':
                    hash = hashlib.md5(line[1:].encode('utf-8')).hexdigest()[:8]
                    if hash not in id_to_script['window'].keys():
                        id_to_script['window'][hash] = line[1:]
                elif line[0] == '$':
                    line = split_unescaped_colons(line[1:])
                    data = {}

                    if (line[1].isnumeric()):
                        data['src_name'] = id_to_md5[line[1]]
                    else:
                        data['src_name'] = line[1]
                    
                    data['src'] = decode_escape_sequences(line[2])
                    data['src'] = re.sub(pattern, '', data['src'])
                    data['src'] = re.sub(r'[\s\x0B\x0C]+', '', data['src'])

                    sid_hash = hashlib.md5(data['src'].encode('utf-8')).hexdigest()[:8]
                    id_to_md5[line[0]] = sid_hash
                    
                    if sid_hash in id_to_script.keys() and data['src'] != id_to_script[sid_hash]['src']:
                        print("\nCOLLISION DETECTED WOOOOO!!!!\n")
                        print(data['src_name'], log_file_path, id_to_script[sid_hash]['src_name'])
                        sid_hash = hashlib.sha256(data['src'].encode('utf-8')).hexdigest()
                    
                    id_to_script[sid_hash] = data
                    
                    line[1] = line[1].replace('"', '').replace('\\', '')
                    if line[1] and line[1] != url.split('#')[0]:
                        try:
                            val = int(line[1])
                        except Exception as e:
                            if line[1] in name_to_src.keys():
                                name_to_src[line[1]].append(sid_hash)
                            else:
                                name_to_src[line[1]] = [sid_hash]

                elif line[0] == '!':
                    if line[1] == '?':
                        last_seen_script = '?'
                    else:
                        cfg.append((last_seen_script, hashlib.sha256(str(last_seen_api_calls).encode('utf-8')).hexdigest())) ###
                        last_seen_api_calls = [] ###
                        
                        last_seen_script = id_to_md5[line[1:]]
                
                elif line[0] == 'c':
                    # print(line)
                    line = split_unescaped_colons(line[1:])
                    data = {}
                    data['action'] = 'call'
                    data['offset'] = line[0]
                    data['func_name'] = line[1]

                    last_seen_api_calls.append(line) ###
                    # data['receiver'] = line[2]
                    # if (len(line) > 3):
                    #     data['script'] = decode_escape_sequences(line[3])
                    #     data['script'] = re.sub(pattern, '', data['script'])
                    #     data['script'] = re.sub(r'[\s\x0B\x0C]+', '', data['script'])
                        
                    # if (len(line) > 4):
                    #     # print(f'the function call log (cXXX) has more fields: {len(line)}')
                    #     data['rest'] = ":".join(line[4:])
                    
                    if last_seen_script in granular_info.keys():
                        granular_info[last_seen_script].append(data)
                    else:
                        granular_info[last_seen_script] = [data]
                elif line[0] == 'n':
                    line = split_unescaped_colons(line[1:])
                    data = {}
                    data['action'] = 'new'
                    data['offset'] = line[0]
                    data['func_name'] = line[1]

                    last_seen_api_calls.append(line) ###
                    # if (len(line) > 2):
                    #     # print(f'the function call log (nXXX) has more fields: {len(line)}')
                    #     data['rest'] = line[2]   
                    if last_seen_script in granular_info.keys():
                        granular_info[last_seen_script].append(data)
                    else:
                        granular_info[last_seen_script] = [data]
                elif line[0] == 'g':
                    line = split_unescaped_colons(line[1:])
                    data = {}
                    data['action'] = 'get'
                    data['offset'] = line[0]
                    # data['parent'] = line[1]
                    data['property_name'] = line[2]

                    last_seen_api_calls.append(line) ###
                
                    if last_seen_script in granular_info.keys():
                        granular_info[last_seen_script].append(data)
                    else:
                        granular_info[last_seen_script] = [data]
                elif line[0] == 's':
                    line = split_unescaped_colons(line[1:])
                    data = {}
                    data['action'] = 'set'
                    data['offset'] = line[0]
                    # data['parent'] = line[1]
                    data['property_name'] = line[2]
                    data['new_val'] = decode_escape_sequences(line[3])
                    data['new_val'] = re.sub(pattern, '', data['new_val'])
                    data['new_val'] = re.sub(r'[\s\x0B\x0C]+', '', data['new_val'])

                    last_seen_api_calls.append(line) ###

                    if last_seen_script in granular_info.keys():
                        granular_info[last_seen_script].append(data)
                    else:
                        granular_info[last_seen_script] = [data]
                else:
                    print(f"Invalid character detected in logFile: {log_file_path}")
                    sys.exit(1)
            except Exception as e:
                print(f'Exception: {e}')
                print(f'Line: {line} in logFile: {log_file_path}')

        output_file_path = log_file_path.split('/')[-1] + '.processed'
        with open(f'./{args.directory}/{extn}/{keyword}/{output_file_path}', 'w') as f:
            write_data = {}
            write_data['name_to_src'] = name_to_src
            write_data['id_to_md5'] = id_to_md5
            write_data['id_to_script'] = id_to_script
            write_data['granular_info'] = granular_info
            json.dump(write_data, f)
        f.close()

        json.dump(cfg, open(f'./{args.directory}/{extn}/{keyword}/{output_file_path}.cfg', 'w')) ###
    except Exception as e:
        print('Exception 2')
        print(e)
        print(arguments)
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get Extension')
    parser.add_argument('--extn', type=str, default='control')
    parser.add_argument('--url', type=str, default='control')
    parser.add_argument('--directory', type=str, default='control')
    args = parser.parse_args()

    if args.url.endswith(".txt"):
        urls = open(args.url, 'r').read().splitlines()
    else:
        urls = [args.url]

    log_file_pool = []
    for url in urls:
        keyword = ''
        if 'http' in url:
            keyword = url.split('://')[1].split('/')[0]
        else:
            keyword = url.split('/')[0]

        if 'www' in keyword:
            keyword = keyword.split('www.')[1]

        try:
            # Example usage
            log_files = [f for f in os.listdir(f'./{args.directory}/{args.extn}/{keyword}') if f.endswith('.log')]
            rogue_files = find_rogue_files(f'./{args.directory}/{args.extn}/{keyword}')
            # print(keyword, rogue_files)
            if len(rogue_files) > 3:
                print(f'Dropping {keyword}: Too many rogue files')
                continue
            for log_file in log_files:
                if log_file in rogue_files:
                    continue
                log_file_path = f'./{args.directory}/{args.extn}/{keyword}/{log_file}'
                log_file_pool.append((log_file_path, keyword, args.extn, url))
                # process_log_file(log_file_path, keyword)
        except OSError as e:
            continue

    try:
        # Create a pool of worker processes
        # print(log_file_pool)
        with multiprocessing.Pool() as pool:
            # Map the worker function to the arguments
            results = pool.map(process_log_file, log_file_pool)
            
        # Print the results
        # print(results)
        # for i, (stdout, stderr) in enumerate(results):
        #     print(f'Result from worker {i}:')
        #     print('stdout:', stdout)
        #     print('stderr:', stderr)
        for i in results:
            if i == None:
                continue
            # print(f'Result from worker {i}:')
            print('stdout:', i[0])
            print('stderr:', i[1])
    except Exception as e:
        print('Exception 1')
        print(e)