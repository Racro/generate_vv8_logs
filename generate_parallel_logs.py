import multiprocessing
import subprocess
import argparse
import time
import os

def worker(args):
    """Function to execute a.py with given arguments and capture output"""
    script_name = 'check_selector.js'
    arg1, arg2, arg3 = args
    
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

def main(extn, url, headless):
    # Arguments to pass to the script a.py
    # URL = 'https://www.geeksforgeeks.org/deletion-in-linked-list/'
    arguments = [(f'--headless={headless}', f'--extn={extn}', f'--url={url}') for i in range(5)]
    
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

    urls = open(args.url, 'r').read().splitlines()
    for url in urls:
        main(args.extn, url, args.headless)
        time.sleep(2)
        os.system(f'python3 clean.py --extn {args.extn} --site {url}')
    print('exiting this code peacefully!')