import multiprocessing
import subprocess
import argparse
import time
import os
from pyvirtualdisplay import Display

def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]

def worker(args):
    """Function to execute a.py with given arguments and capture output"""
    script_name = 'check_selector.js'
    arg1, arg2, arg3, arg4 = args
    
    try:
        # Execute the script with arguments
        result = subprocess.run(
            ['node', script_name, str(arg1), str(arg2), str(arg3)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Capture stdout and stderr
        stdout = result.stdout
        stderr = result.stderr
        
        return (stdout, stderr)
    except subprocess.CalledProcessError as e:
        return (e.stdout, e.stderr)
    except Exception as e:
        return (e.stdout, e.stderr)

def main(extn, url, headless, display):
    # Arguments to pass to the script a.py
    # URL = 'https://www.geeksforgeeks.org/deletion-in-linked-list/'
    arguments = [(f'--headless={headless}', f'--extn={extn}', f'--url={url}', f'--display={display}') for i in range(5)]
    
    try:
        # Create a pool of worker processes
        with multiprocessing.Pool(processes=5) as pool:
            # Map the worker function to the arguments
            results = pool.map(worker, arguments)
            
        # Print the results
        for i, (stdout, stderr) in enumerate(results):
            print(f'Result from worker {i}:')
            print('stdout:', stdout)
            print('stderr:', stderr)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run crawlers in parallel')
    parser.add_argument('--headless', type=str, default='true')
    parser.add_argument('--extn', type=str, default='control')
    parser.add_argument('--url', type=str)
    args = parser.parse_args()

    xvfb_args = [
        '-maxclients', '1024'
    ]
    vdisplay = Display(backend='xvfb', size=(1920, 1280), extra_args=xvfb_args)
    vdisplay.start()
    display = vdisplay.display
    os.environ['DISPLAY'] = f':{display}'

    SIZE = 2
    urls = open(args.url, 'r').read().splitlines()
    urls = divide_chunks(urls, SIZE)
    for url in urls:
        print(url)
        jobs = []
        for item in url:
            p = multiprocessing.Process(target=main, args=(args.extn, item, args.headless, display, ))
            jobs.append(p)
        for job in jobs:
            job.start()
        for job in jobs:
            job.join()
        
        time.sleep(2)
        for item in url:
            os.system(f'python3 clean.py --extn {args.extn} --site {item}')
    
        time.sleep(2)
        os.system('pkill chrome')
        os.system('rm -rf vv8-*.log')
        time.sleep(2)

    vdisplay.stop()

    print('exiting this code peacefully!')