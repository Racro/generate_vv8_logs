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
    # 1. Data Manipulation & Processing
    "Data Manipulation & Processing": [
        "FileReader",
        "FileSystem",
        "IndexedDB",
        "localStorage",
        "sessionStorage",
        "Clipboard API",
        "ReadableStream",
        "WritableStream",
        "TextEncoder",  # Encoding/decoding strings
        "TextDecoder",  # Encoding/decoding strings
        "ArrayBuffer",  # Binary data handling
        "DataView",     # Binary data manipulation
        "Blob",         # Binary large objects
        "FormData",     # Handling form data
        "URLSearchParams",  # Query string manipulation
        "structuredClone"  # Deep cloning objects
    ],

    # 2. DOM Manipulation & Rendering
    "DOM Manipulation & Rendering": [
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
        "ResizeObserver",
        "IntersectionObserver",  # Observing element visibility
        "requestAnimationFrame",  # Smooth animations
        "CustomEvent",           # Creating custom DOM events
        "ShadowRoot",            # Shadow DOM manipulation
        "Element.animate"        # CSS animations via JS
    ],

    # 3. Asynchronous Operations & Network Communication
    "Asynchronous Operations & Network Communication": [
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
        "ServerSentEvents",
        "BroadcastChannel",  # Communication between browsing contexts
        "MessageChannel",    # Direct communication between scripts
        "EventSource"        # Server-sent events
    ],

    # 4. User Interaction & Event Handling
    "User Interaction & Event Handling": [
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
        "SpeechSynthesis",
        "DragEvent",          # Drag-and-drop interactions
        "InputEvent",         # Input field events
        "Fullscreen API",     # Fullscreen interactions
        "Pointer Lock API",   # Locking pointer to an element
        "Vibration API"       # Device vibration feedback
    ],

    # 5. Utility Functions & Performance Optimization
    "Utility Functions & Performance Optimization": [
        "performance.now",
        "performance.mark",
        "performance.measure",
        "navigator.storage.estimate",
        "PageVisibility",
        "BatteryManager",
        "DeviceMemory",
        "NetworkInformation",
        "console",            # Logging and debugging
        "Intl.DateTimeFormat",  # Date and time formatting
        "Intl.NumberFormat",    # Number formatting
        "Intl.Collator",        # String comparison
        "navigator.geolocation",  # Geolocation API
        "navigator.connection",   # Network connection info
        "PerformanceObserver",  # Observing performance metrics
        "ReportingObserver"     # Observing deprecated API usage
    ],

    # 6. Security, Authentication, & Cryptography
    "Security, Authentication, & Cryptography": [
        "Crypto",
        "crypto.getRandomValues",
        "crypto.subtle",       # SubtleCrypto API for encryption/decryption
        "WebAuthn",            # Web Authentication API
        "Credential Management API",  # Managing user credentials
        "Permissions API",     # Managing permissions (e.g., camera, mic)
        "Content Security Policy (CSP)",  # Enforcing security policies
        "Trusted Types",       # Preventing DOM-based XSS
        "Sanitizer API"        # Sanitizing HTML input
    ],

    # 7. Functional Programming & Advanced Patterns
    "Functional Programming & Advanced Patterns": [
        "Promise.all",
        "Promise.race",
        "Array.prototype.map",
        "Array.prototype.reduce",
        "Array.prototype.filter",
        "Array.prototype.forEach",
        "GeneratorFunction",
        "SharedArrayBuffer",
        "Atomics",
        "Proxy",               # Creating proxy objects
        "Reflect",             # Reflection API for meta-programming
        "WeakMap",             # Weak references for objects
        "WeakSet",             # Weak references for objects
        "Symbol",              # Creating unique identifiers
        "Iterator",            # Custom iterators
        "AsyncIterator"        # Custom async iterators
    ],

    # 8. Other / Miscellaneous
    "Others": [
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
        "HID",
        "WebAssembly",         # Running low-level code in the browser
        "WebTransport",        # Modern transport protocol
        "WebCodecs",           # Encoding/decoding audio and video
        "WebMIDI",             # MIDI device integration
        "WebHID",              # Human Interface Device API
        "WebNFC",              # Near Field Communication API
        "WebShare API",        # Sharing content to other apps
        "WebLocks API"         # Managing resource locks
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
    granular_scripts = {}
    granular_scripts['set'] = defaultdict(int)
    granular_scripts['call'] = defaultdict(int)

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
                                granular_scripts['call'][category] += 1
                                # Assuming each API belongs to only one category, we can break here.
                                check = 1
                                break
                        if check == 0:
                            granular_scripts['call']['Others'] += 1
                        
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

def find_script_utility(filepath):
    cats = FileHandler.load_json('analysis_json/script_categories.json')
    # llm_cats = {'categories': [], 'explanations': []}
    llm_cats = []

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

    for i in cats[50:]:
        try:
            system_prompt = """
                You are an expert JavaScript analyst. You must classify the code under these categories:
                    ## 1. Data Manipulation & Processing  
                    *Definition:* Involves creating, transforming, and interpreting data structures (arrays, strings, objects), as well as mathematical and algorithmic operations.  
                    * `Arrays:` Filtering, mapping, reducing (`filter`, `map`, `reduce`).  
                    * `Strings:` Extracting and replacing segments (`substring`, `replace`).  
                    * `Objects:` Merging, copying, enumerating keys (`Object.assign`, `Object.keys`).  
                    * `Mathematical Functions:` Built-in math methods (`Math.sqrt`, `Math.random`, `Math.round`).  
                    * `Custom Algorithms:` Advanced numeric or data-structure logic (e.g., custom sorting).  
                    * `State Management:` Managing application state (e.g., Redux, Vuex, `localStorage`, `sessionStorage`).  
                    
                    ---

                    ## 2. DOM Manipulation & Rendering  
                    *Definition:* Focuses on altering or interacting with the web page’s structure and style, including performance optimizations.  
                    * `Adding/Removing Elements:` `appendChild`, `removeChild`.  
                    * `Modifying Styles:` `style.backgroundColor`, `classList.add`.  
                    * `Event Handling:` `addEventListener`, `removeEventListener` to respond to user actions.  
                    * `Performance Optimizations:` Lazy loading, virtual DOM, rendering optimizations.  
                    
                    ---

                    ## 3. Asynchronous Operations & Network Communication  
                    *Definition:* Covers code that runs outside the normal synchronous flow, often involving server communication and third-party integrations.  
                    * `Fetching Data:` `fetch`, `XMLHttpRequest`, Axios.  
                    * `Promises & Async/Await:` `then`, `catch`, `finally`, `async/await`.  
                    * `Timers:` `setTimeout`, `setInterval` for scheduled tasks.  
                    * `Third-Party Integrations:` Google Analytics, payment gateways, social media widgets.  
                    
                    ---

                    ## 4. User Interaction & Event Handling  
                    *Definition:* Handles direct actions from users and visual/interactive responses, including accessibility features.  
                    * `Event Listeners:` `click`, `scroll`, `hover`, `keydown`.  
                    * `Input Validation:` Checking formats (email, password strength).  
                    * `Feedback:` `alert`, `confirm`, or custom UI messages.  
                    * `Accessibility:` Focus management, ARIA attributes, screen reader support.  
                    
                    ---

                    ## 5. Utility Functions & Performance Optimization  
                    *Definition:* Provides shared helpers and cross-cutting features, including debugging, storage, and performance monitoring.  
                    * `Logging & Debugging:` `console.log`, `console.error`.  
                    * `Date & Time:` Creating and formatting dates (`Date.now`, `Date.toLocaleString`).  
                    * `State & Storage:` `localStorage`, `sessionStorage`, caching.  
                    * `Performance Monitoring:` Debouncing, throttling, metrics collection.  
                    
                    ---

                    ## 6. Security, Authentication, & Cryptography  
                    *Definition:* Focuses on securing applications, managing user authentication, and handling cryptographic operations.  
                    * `User Authentication:` OAuth, JWT, session management.  
                    * `Input Validation & Sanitization:` Preventing XSS, SQL injection.  
                    * `Secure Storage:` Encrypted cookies, token handling.  
                    * `Cryptography:` Using the `SubtleCrypto` API for encryption/decryption.  
                    
                    ---

                    ## 7. Functional Programming & Advanced Patterns  
                    *Definition:* Emphasizes advanced patterns where functions operate on or produce other functions, and includes reusable logic.  
                    * `Higher-Order Functions:` Currying, partial application.  
                    * `Functional Composition:` Combining smaller functions for reusable logic.  
                    * `Advanced Patterns:` Memoization, reactive programming, custom hooks.  
                    
                    ---

                    ## 8. Others  
                    *Definition:* Covers specialized or advanced tasks not fitting neatly in the categories above.  
                    * `Progressive Web App (PWA) Features:` Service workers, push notifications, offline caching.  
                    * `Localization & Internationalization:` Dynamic content translation, locale-specific formatting.  
                    * `Advanced Browser APIs:` WebAssembly, device APIs (Bluetooth, camera), push notifications.  
                    * `Workers:` Off-main-thread processing (e.g., Web Workers, Service Workers).

                ###

                Then produce a detailed JSON explanation with exactly four keys:
                {
                "categories": [...],
                "explanations": "...",
                "relevantFunctions": [
                    {
                    "functionName": "...",
                    "description": "...",
                    "argumentsExample": "...",
                    "roleInDifferentialBehavior": "..."
                    }
                ],
                "differentialBehavior": [...]
                }

                Where:
                    - "categories": an array of the applicable categories by name.
                    - "explanations": a thorough textual explanation of how the script works, referencing relevant variables or objects as needed.
                    - "relevantFunctions": a short list of the script's key functions/objects, focusing on those that indicate important or potentially differential/fallback behavior. For each:
                    - functionName: the name or short alias used in the code.
                    - description: what it does or why it's significant.
                    - argumentsExample: show an example or typical arguments if relevant.
                    - roleInDifferentialBehavior: e.g., "adblock fallback," "paywall logic," or "none" if not involved in differential behavior.
                    - "differentialBehavior": an array listing bullet points about possible differential logic or fallback, including a final mini-summary of whether it's *actually* differential w.r.t. adblock. For example:
                    [
                        "Bullet point on what functions are interesting in the context of adblocking",
                        "Bullet point on region-based gating",
                        "Final verdict: This does/does not appear to truly be differential behavior for adblock usage."
                    ]

                Return ONLY the JSON object (no extra text, Markdown, disclaimers, or formatting).
            """
            user_prompt = f"""
                Classify and explain this JavaScript under the specified categories. Cite only the critical minified/short functions or objects you think are important. Describe any fallback or differential behavior. Return only JSON (nothing else).

                SOURCE URL: {i[0]}
                SOURCE CODE: {i[1]}
            """

    
            body = {
                'messages': [
                    {
                        "role": "user",
                        "content": system_prompt
                    },
                    {
                        "role": "system",
                        "content": user_prompt
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
                print(cat)
                llm_cats.append(cat)
                # llm_cats['categories'].append(cat['categories'])
                # llm_cats['explanations'].append(cat['explanations'])
                # print(cat)
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

        FileHandler.save_json(llm_cats, filepath)

def process_script_utility():
    a = FileHandler.load_json('analysis_json/llm_script_categories.json')
    cat_count = defaultdict(int)

    for lst in a['categories']:
        for cat in lst:
            cat_count[cat] += 1

    FileHandler.save_json(cat_count, 'analysis_json/llm_script_categories_count.json')


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
    # investigate_granular_scripts(args.directory, args.extn)
    # identify_script_categories()
    find_script_utility("analysis_json/llm_script_categories_rest.json")
    # process_script_utility()

    # investigator = APIInvestigator(args.extn, args.url, args.directory)
    # investigator.process_urls()