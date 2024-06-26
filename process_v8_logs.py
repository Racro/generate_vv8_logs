import re
import jsbeautifier
import os
import json
import hashlib
import sys
import argparse

parser = argparse.ArgumentParser(description='Get Extension')
parser.add_argument('--extn', type=str, default='control')
args = parser.parse_args()

# remove \n from js
pattern = r'(?<!\\)\\n'

id_to_md5 = {}
id_to_script = {}
id_to_script['window'] = {}

granular_info = {}

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
    # Decode escape sequences
    return bytes(js_code, "utf-8").decode("unicode_escape")

def beautify_js(js_code):
    # Beautify the JavaScript code
    return jsbeautifier.beautify(js_code)

def process_log_file(log_file_path):
    # Read the log file
    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    last_seen_script = 0
    for line in lines:
        if line[-1] == '\n':
            line = line[:-1]
        try:
            # filename, js_code = extract_js_from_log_line(line)
            if line[:3] == '~0x':
                id_to_script['context'] = hashlib.md5(line.encode('utf-8')).hexdigest()[:6]
            elif line[0] == '@':
                hash = hashlib.md5(line[1:].encode('utf-8')).hexdigest()[:6]
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

                sid_hash = hashlib.md5(data['src'].encode('utf-8')).hexdigest()[:6]
                id_to_md5[line[0]] = sid_hash

                id_to_script[sid_hash] = data

            elif line[0] == '!':
                if line[1] == '?':
                    last_seen_script = '?'
                else:
                    last_seen_script = id_to_md5[line[1:]]
            
            elif line[0] == 'c':
                # print(line)
                line = split_unescaped_colons(line[1:])
                data = {}
                data['action'] = 'call'
                data['offset'] = line[0]
                data['func_name'] = line[1]
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

                if last_seen_script in granular_info.keys():
                    granular_info[last_seen_script].append(data)
                else:
                    granular_info[last_seen_script] = [data]
            else:
                print("Invalid character detected")
                sys.exit(1)
        except Exception as e:
            print(e)
            print(f'Line: {line}')

    output_file_path = log_file_path.split('/')[-1] + '.processed'
    with open(f'./vv8_logs/{args.extn}/{output_file_path}', 'w') as f:
        write_data = {}
        write_data['id_to_md5'] = id_to_md5
        write_data['id_to_script'] = id_to_script
        write_data['granular_info'] = granular_info
        json.dump(write_data, f)
    f.close()

# Example usage
log_files = [f for f in os.listdir(f'./vv8_logs/{args.extn}') if f.endswith('.log')]
# print(log_files)
for log_file in log_files:
    log_file_path = f'./vv8_logs/{args.extn}/{log_file}'
    process_log_file(log_file_path)
