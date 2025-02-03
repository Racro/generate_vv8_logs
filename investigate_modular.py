import json
import os
import re
import sys
import requests
import argparse
import numpy as np
import subprocess

import base64
from openai import OpenAI
import pandas as pd
import requests
from json.decoder import JSONDecodeError
from collections import defaultdict

api_categories = {
    "Data Manipulation": [
        "removeItem",
        "FileReader",
        "FileSystem",
        "IndexedDB",
        "localStorage",
        "sessionStorage",
        "Clipboard API",
        "ReadableStream",
        "WritableStream"
    ],
    "DOM Manipulation": [
        "createElement",
        "createTextNode",
        "appendChild",
        "append",              # Modern DOM method for appending nodes or strings
        "removeChild",
        "insertBefore",
        "remove",
        "removeAttribute",
        "querySelector",
        "querySelectorAll",
        "getElementById",
        "setAttribute",
        "getAttribute",
        "classList",
        "innerHTML",
        "textContent",
        "MutationObserver",
        "ResizeObserver"
    ],
    "Asynchronous & Network Operations": [
        "setTimeout",
        "setInterval",
        "Promise",
        "async",
        "await",
        "postMessage",
        "XMLHttpRequest",
        "fetch",
        "WebSocket",
        "ServiceWorker",
        "CacheStorage",
        "navigator.sendBeacon",
        "fetchEvent",
        "Notification",
        "BackgroundSync",
        "ServerSentEvents"
    ],
    "Mathematical & Algorithmic Functions": [
        "Math",
        "Intl.Collator",
        "Intl.DateTimeFormat",
        "Intl.NumberFormat",
        "Crypto",
        "crypto.getRandomValues",
        "TextEncoder",
        "TextDecoder"
    ],
    "User Interaction": [
        "addEventListener",
        "removeEventListener",
        "PointerEvent",
        "MouseEvent",
        "KeyboardEvent",
        "TouchEvent",
        "FocusEvent",
        "Gamepad",
        "ScreenOrientation",
        "SpeechRecognition",
        "SpeechSynthesis"
    ],
    "Utility Functions": [
        "performance.now",
        "performance.mark",
        "performance.measure",
        "navigator.storage.estimate",
        "PageVisibility",
        "BatteryManager",
        "DeviceMemory",
        "NetworkInformation"
    ],
    "Higher-Order & Functional Programming": [
        "Promise.all",
        "Promise.race",
        "Array.prototype.map",
        "Array.prototype.reduce",
        "Array.prototype.filter",
        "Array.prototype.forEach",
        "GeneratorFunction",
        "SharedArrayBuffer",
        "Atomics",
        "add"  # if referring to e.g. Set.prototype.add
    ],
    "Other / Miscellaneous": [
        "CanvasRenderingContext2D",
        "WebGLRenderingContext",
        "WebGPU",
        "AudioContext",
        "MediaStream",
        "MediaSource",
        "Presentation",
        "WebXR",
        "PictureInPicture",
        "DevicePosture",
        "NFC",
        "Bluetooth",
        "USB",
        "Serial",
        "HID"
    ]
}

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

class FileHandler:
    @staticmethod
    def load_json(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return None

    @staticmethod
    def save_json(data, filepath, encoder=SetEncoder):
        with open(filepath, 'w') as f:
            json.dump(data, f, cls=encoder)

    @staticmethod
    def read_lines(filepath):
        try:
            with open(filepath, 'r') as f:
                return f.read().splitlines()
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return []

def investigate_new_scripts(directory, extn):
    diff_files = [f'{directory}_diff/{f}' for f in os.listdir(f'{directory}_diff') if f.startswith(extn)]

    new_scripts = {}
    for f in diff_files:
        a = FileHandler.load_json(f)
        try:
            for key, items in a['id_to_script'].items():
                if f.split('_')[-1] not in new_scripts.keys():
                    new_scripts[f.split('_')[-1].split('.json')[0]] = []
                new_scripts[f.split('_')[-1].split('.json')[0]].append((items['src_name'], items['src']))
        except Exception as e:
            print(e, len(a['id_to_script']), f, new_scripts.keys())
            sys.exit(0)
    FileHandler.save_json(new_scripts, 'analysis_json/new_scripts.json')

def investigate_granular_scripts(directory, extn):
    diff_files = [f'{directory}_diff/{f}' for f in os.listdir(f'{directory}_diff') if f.startswith(extn)]

    # granular_scripts = {category: 0 for category in api_categories}
    granular_scripts = defaultdict(int)
    granular_scripts['set'] = defaultdict(int)

    for f in diff_files:
        a = FileHandler.load_json(f)
        try:
            for key, items in a['granular_info'].items():
                for api in items:
                    if api[0][1] == 'set':
                        granular_scripts['set'][api[2][1].strip('\"\\')] += 1
                    elif api[0][1] == 'call':
                        api_call = api[2][1].split('%')[-1]
                        # Check each category to see if this API is included.
                        check = 0
                        for category, apis in api_categories.items():
                            if api_call in apis:
                                granular_scripts[category] += 1
                                # Assuming each API belongs to only one category, we can break here.
                                check = 1
                                break
                        if check == 0:
                            granular_scripts['Others'] += 1
                        
        except Exception as e:
            print(e, len(a['granular_info']), f, granular_scripts.keys())
            sys.exit(0)
    FileHandler.save_json(granular_scripts, 'analysis_json/granular_scripts_count.json')

def identify_script_categories():
    cats = []
    resources = []
    new_scripts = FileHandler.load_json('analysis_json/new_scripts.json')
    for key in new_scripts:
        for url, src in new_scripts[key]:
            resources.append((f'https://{key}', url, src))

    ret = ScriptProcessor.check_if_ad(resources)
    
    count = 0
    for i in range(len(ret)):
    # for i in range(1):
        if ret[i] == False:
            cats.append((resources[i][1], resources[i][2]))
        else:
            count += 1

    print(count)
    FileHandler.save_json(cats, 'analysis_json/script_categories.json') 

def find_script_utility():
    cats = FileHandler.load_json('script_categories.json')
    llm_cats = {'categories': [], 'explanations': []}

    api_key = os.getenv("OPENAI_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_KEY environment variable.")

    URL = "https://genai-prod-nyu-rit-ai-apicast-production.apps.cloud.rt.nyu.edu/chat-openai?gateway=default"

    headers = {
        "AUTHORIZATION_KEY": api_key,
        "rit_access": "266|rr3953|gpt-4o",
        "rit_timeout": "60",
        "Content-Type": "application/json"
    }

    for i in cats:
        try:
            body = {
                'messages': [
                    {
                        "role": "user",
                        "content": 
                            f"""Classify the given JavaScript into one or more of the seven categories based on following data and return a dictionary in JSON compatible FORMAT with explanations of its functionality:
                            ##
                            SOURCE URL - {i[0]}
                            ##
                            SOURCE CODE - {i[1]}
                            """
                    },
                    {
                        "role": "system",
                        "content": 
                            """
                            You are an expert at analyzing JavaScript files based on both their public source URL and the provided source code. In case source URL is not present or clear, resort to source code based analysis. Your task is to classify each JavaScript instance into one or more of the predefined categories. Also provide verbose explanation of what the script does to the extent possible. Return a list of all categories that can be found in the script. If none of the categories fit, classify it under "Others," which covers topics outside the first seven categories.

                            The eight categories are:  
                            ### 1. Data Manipulation
                            **Definition:** Involves creating, transforming, and interpreting data structures (arrays, strings, objects).  
                            - **Arrays:** Filtering, mapping, reducing (`filter`, `map`, `reduce`).  
                            - **Strings:** Extracting and replacing segments (`substring`, `replace`).  
                            - **Objects:** Merging, copying, enumerating keys (`Object.assign`, `Object.keys`).

                            ---

                            ### 2. DOM Manipulation
                            **Definition:** Focuses on altering or interacting with the web page’s structure and style.  
                            - **Adding/Removing Elements:** `appendChild`, `removeChild`.  
                            - **Modifying Styles:** `style.backgroundColor`, `classList.add`.  
                            - **Event Handling:** `addEventListener`, `removeEventListener` to respond to user actions.

                            ---

                            ### 3. Asynchronous & Network Operations
                            **Definition:** Covers code that runs outside the normal synchronous flow, often involving server communication.  
                            - **Fetching Data:** `fetch`, `XMLHttpRequest`, Axios.  
                            - **Promises & Async/Await:** `then`, `catch`, `finally`, `async/await`.  
                            - **Timers:** `setTimeout`, `setInterval` for scheduled tasks.

                            ---

                            ### 4. Mathematical & Algorithmic Functions
                            **Definition:** Encompasses built-in math methods and custom algorithm implementations.  
                            - **Built-in Math:** `Math.sqrt`, `Math.random`, `Math.round`.  
                            - **Custom Algorithms:** Advanced numeric or data-structure logic (e.g., custom sorting).

                            ---

                            ### 5. User Interaction
                            **Definition:** Handles direct actions from users and visual/interactive responses.  
                            - **Animations:** `requestAnimationFrame`, CSS animations via JS, GSAP.  
                            - **Input Validation:** Checking formats (email, password strength).  
                            - **Feedback:** `alert`, `confirm`, or custom UI messages.

                            ---

                            ### 6. Utility Functions
                            **Definition:** Provides shared helpers and cross-cutting features (debugging, storage, performance logs).  
                            - **Logging & Debugging:** `console.log`, `console.error`.  
                            - **Date & Time:** Creating and formatting dates (`Date.now`, `Date.toLocaleString`).  
                            - **State & Storage:** `localStorage`, session data, caching.  
                            - **Performance/Instrumentation:** Monitoring, metrics collection.

                            ---

                            ### 7. Higher-Order & Functional Programming
                            **Definition:** Emphasizes advanced patterns where functions operate on or produce other functions.  
                            - **Functions That Accept/Return Functions:** Currying, partial application.  
                            - **Functional Composition:** Combining smaller functions for reusable logic.

                            ---
                            
                            ### 8. Others
                            **Definition:** Covers specialized or advanced tasks not fitting neatly in the categories above.

                            - **Workers & Service Workers: Off-main-thread processing, background sync, offline caching.
                            - **Advanced Browser APIs: WebAssembly, device APIs (Bluetooth, camera), push notifications.
                            - **Cryptography & Security: Using SubtleCrypto API, token handling.
                            
                            Take a thoughtful approach when determining the correct category. If you're unsure, take a moment to reconsider and identify the closest match. Only return results when you are certain, and avoid speculative guesses.

                            ### Examples:
                                - SOURCE URL - https://example.com/ui-handler.js, SOURCE - '// Toggles the visibility of a modal on button click
                                document.getElementById('open-modal').addEventListener('click', function () {
                                    const modal = document.getElementById('modal');
                                    if (modal.style.display === 'none') {
                                        modal.style.display = 'block';
                                    } else {
                                        modal.style.display = 'none';
                                    }
                                });' - {"categories": ["DOM Manipulation"], "explanations": "The script changes the color of the modal varible in the DOM."}
                                - SOURCE URL - https://api.example.com/fetch-data.js, SOURCE - '// Fetches data from a remote API and logs the response
                                async function fetchData() {
                                    try {
                                        const response = await fetch('https://api.example.com/data');
                                        if (!response.ok) {
                                            throw new Error('Network response was not ok');
                                        }
                                        const data = await response.json();
                                        console.log(data);
                                    } catch (error) {
                                        console.error('Error fetching data:', error);
                                    }
                                }

                                fetchData();' - {"categories": "Asynchronous & Network Operations", "explanations": "The script source code contains fetch api which fetches data from an api endpoint."}

                            ### Output format:
                            {'categories': [Category1, Category2, ...], 'explanations': explanation}
                            Please don't output any supporting, formatting or explanatory text apart from the dictionary. Return a dictionary of all categories found with verbose explanation of the script functionality in JSON compatible FORMAT.
                            """
                    },
                ],
                'temperature': 0
            }

            res = requests.post(URL, headers=headers, json = body)
            # print(res.json()['choices'][0]['message']['content'].strip())
            try:
                # return res.json()['choices'][0]['message']['content'].strip()
                cat = res.json()['choices'][0]['message']['content'].strip().strip('`')
                # print(type(cat))
                # cat = json.loads(f'''{cat}''')
                # print(cat["categories"])
                cat = json.loads(cat.replace('json', '').strip())

                llm_cats['categories'].append(cat['categories'])
                llm_cats['explanations'].append(cat['explanations'])
                print(cat)
                # llm_cats.append(res.json()['choices'][0]['message']['content'].strip('`'))
                # print(res.json()['choices'][0]['message']['content'])
            except JSONDecodeError as e:
                print(f"Error decoding JSON: {e}", cat)
                # Handle the error or assign default values
                # llm_cats['categories'].append([])
                # llm_cats['explanations'].append('')
            except Exception as e:
                print(e, cat)
        except Exception as e:
            print(f"Error processing batch: {e}")
            # llm_cats.append(None)

        FileHandler.save_json(llm_cats, 'llm_script_categories.json')

def process_script_utility():
    a = FileHandler.load_json('llm_script_categories.json')
    cat_count = defaultdict(int)

    for lst in a['categories']:
        for cat in lst:
            cat_count[cat] += 1

    FileHandler.save_json(cat_count, 'llm_script_categories_count.json')


class ScriptProcessor:
    @staticmethod
    def fetch_script_content(url, offset):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                script_content = response.text
                if len(script_content) > offset:
                    return script_content[offset - 5:offset + 15]
                else:
                    print(f"Invalid offset. Content length: {len(script_content)}, Offset: {offset}")
            else:
                print(f"Failed to fetch script. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}, URL: {url}")
        return ''

    @staticmethod
    def split_unescaped_colons(s):
        # Regular expression pattern to match unescaped colons
        pattern = r'(?<!\\):'
        # Split the string using the pattern
        result = re.split(pattern, s)
        # Replace escaped colons with actual colons in the result
        result = [part.replace(r'\:', ':') for part in result]
        return result

    @staticmethod
    def check_if_ad(resource):
        original_directory = os.getcwd()
        target_directory = '/root/breakages/else/Ad-BlockerResearch/2. Resources (js)/blacklist_parser'

        try:
            # Change to the target directory
            os.chdir(target_directory)
            print(f"Changed to directory: {os.getcwd()}")
            
            ret = []
            for r in resource:
                # Run the Node.js script
                print(r[0], r[1])
                result = subprocess.run(['node', 'mytest.js', '--url', r[0], '--resource', r[1]], capture_output=True, text=True, check=True)

                # print(result.stdout)  
                if result.stdout == '':
                    ret.append(False)
                else:
                    print("STDOUT: ", result.stdout)
                    ret.append(True)

            os.chdir(original_directory)
            print(f"Returned to original directory: {os.getcwd()}")

            return ret

        except Exception as e:
            print(f"Error in check_ad: {e}")
            return False

class APIInvestigator:
    def __init__(self, extn, url_file, directory):
        self.extn = extn
        self.directory = directory
        self.urls = FileHandler.read_lines(url_file)
        self.name_to_src = {}
        self.super_script_set = set()
        self.sub_script_set = set()
        self.granular_info_set = {}
        self.index = {}
        self.substrings_all = ["doubleclick", "securepubads", "pagead2", "adsystem", "chrome-extension://", "ads.adthrive"]
        self.pattern_all = '|'.join(re.escape(substring) for substring in self.substrings_all)
        # self.interesting_apis = ['removeItem', 'createTextNode', 'remove', 'removeChild', 'setInterval', 'insertBefore', 'removeEventListener', 'createElement', 'add', 'postMessage', 'about', 'appendChild', 'removeAttribute', 'setTimeout', 'fetch', 'append', 'addEventListener']
        self.interesting_apis = ['removeItem', 'createTextNode', 'remove', 'removeChild', 'setInterval', 'insertBefore', 'removeEventListener', 'createElement', 'add', 'postMessage', 'appendChild', 'removeAttribute', 'setTimeout', 'fetch', 'append']
        # self.actions = ['call', 'set', 'new', 'get']
        self.actions = ['call']#, 'set', 'new', 'get']

    def process_urls(self):
        for url in self.urls:
            keyword = self.extract_keyword(url)
            try:
                a = FileHandler.load_json(f'{self.directory}_diff/{self.extn}_ctrl_{keyword}.json')
                b = FileHandler.load_json(f'{self.directory}_diff/ctrl_{self.extn}_{keyword}.json')
                if not a or not b:
                    continue

                path = f'../generate_vv8_logs_{self.extn}/{self.directory}/{self.extn}/{keyword}/'
                log_file = self.find_file(path, '.log')
                src_text = FileHandler.read_lines(f'{path}/{log_file}')

                processed_file = self.find_file(path, '.processed')
                src_dict = FileHandler.load_json(f'{path}/{processed_file}')

                self.analyze_scripts(a, src_dict, src_text, url)
            except Exception as e:
                print(f"Error processing URL {url}: {e}")

    def analyze_scripts(self, a, src_dict, src_text, url):
        tuples = []
        keyword = self.extract_keyword(url)
        for key, script_data in a['id_to_script'].items():
            src_name = script_data['src_name']
            src = script_data['src']
            if (not self.is_inline(url, src_name)) and (self.is_valid_script(src_name, src, self.pattern_all)):
                tuples.append((key, src_name))

        if not self.super_script_set:
            self.super_script_set = set(tuples)
            self.sub_script_set = set(tuples)
        else:
            self.super_script_set |= set(tuples)
            self.sub_script_set &= set(tuples)

        self.index_scripts(a, keyword, src_dict, src_text)

    def index_scripts(self, a, keyword, src_dict, src_text):
        count = {}
        functions = {}
        apis_list = []

        for action in self.actions:
            functions[action] = {}
            for key, actions in a['granular_info'].items():     
                try:
                    for action_elem in actions:
                        # COUNT
                        if str(action_elem[0]) not in count.keys(): 
                            count[str(action_elem[0])] = 1 
                        else: 
                            count[str(action_elem[0])] += 1 

                        # GRANULAR INFO
                        if action_elem[0] == ['action', action]:
                            func = action_elem[2][1][1:]
                            offset = action_elem[1][1]
                            if func in self.interesting_apis:
                                # FIND ID FROM KEY(md5)
                                id1 = ''
                                for ids in src_dict['id_to_md5'].keys():
                                    if src_dict['id_to_md5'][ids] == key:
                                        id1 = ids
                                        print(f'id1: {id1}, key: {key}, keyword: {keyword}')
                                        break

                                apis_list.append((func, offset, key, id1))

                            if func in functions[action]:
                                functions[action][func] += 1
                            else:
                                functions[action][func] = 1
                except Exception as e:
                    print(e)

            functions[f'{action}'] = dict(sorted(functions[f'{action}'].items(), key=lambda item: item[1]))

        if apis_list:
            self.investigate_apis(keyword, apis_list, src_text)
        else:
            print('apis_list is empty!')

        # granular_info_set[keyword] = [count, functions]

    # def investigate_apis(self, keyword, apis_list, src_text):
    #     apis = {}
    #     for func, offset, key in apis_list:
    #         method = ScriptProcessor.fetch_script_content(src_text[int(key)], offset)
    #         apis.setdefault(keyword, []).append((func, offset, method))

    #     FileHandler.save_json(f'apis/apis_{keyword}.json', apis)

    # {"action": "call", "offset": "15618", "func_name": "%appendChild"}
    def investigate_apis(self, keyword, apis_list, src_text):
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
                line = ScriptProcessor.split_unescaped_colons(string[1:])
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

    @staticmethod
    def extract_keyword(url):
        keyword = url.split('://')[-1].split('/')[0]
        return keyword.split('www.')[-1]

    @staticmethod
    def is_valid_script(src_name, src, pattern_all):
        return not (re.search(pattern_all, src_name) or '/web_accessible_resources' in src or 'uBlockOrigin-abrowserextensiontoblockrequests' in src)
    
    @staticmethod
    def is_inline(url, src_name):
        url = url.split('#')[0].split('www.')[-1]
        src_name = src_name.replace('\\', '').replace('"', '').split('www.')[-1]
        return src_name == url

    @staticmethod
    def find_file(path, extension):
        try:
            return next(f for f in os.listdir(path) if f.endswith(extension))
        except StopIteration:
            raise FileNotFoundError(f"No {extension} file found in {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get Extension')
    parser.add_argument('--extn', type=str, default='control')
    parser.add_argument('--url', type=str)
    parser.add_argument('--directory', type=str)
    args = parser.parse_args()

    # investigate_new_scripts(args.directory, args.extn)
    investigate_granular_scripts(args.directory, args.extn)
    # identify_script_categories()
    # find_script_utility()
    # process_script_utility()

    # investigator = APIInvestigator(args.extn, args.url, args.directory)
    # investigator.process_urls()