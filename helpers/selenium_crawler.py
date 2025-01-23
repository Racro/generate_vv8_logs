import argparse
import json
import sys
import time
import threading
import pathlib
import re
import multiprocessing
import os

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from webdriver_manager.core.utils import read_version_from_cmd 
from webdriver_manager.core.os_manager import PATTERN
from webdriver_manager.chrome import ChromeDriverManager

with open('./cookies.js', "r") as f:
    COOKIES_SCRIPT = f.read()
f.close()

def is_loaded(webdriver):
    return webdriver.execute_script("return document.readyState") == "complete"

def wait_until_loaded(webdriver, timeout=60, period=0.25, min_time=0):
    start_time = time.time()
    mustend = time.time() + timeout
    while time.time() < mustend:
        if is_loaded(webdriver):
            if time.time() - start_time < min_time:
                time.sleep(min_time + start_time - time.time())
            return True
        time.sleep(period)
    return False

def initialize_driver(extn, num_tries):
    while num_tries > 0:
        try:
            options = Options()
            extensions_path = pathlib.Path("./extn_crx")
            options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.binary_location = "/usr/bin/chromium-browser"
            options.set_capability('goog:logginPrefs', {'browser': 'ALL'})
            options.add_argument("start-maximized")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")

            version = '125.0.6422.141'
            service = Service(ChromeDriverManager(version).install())

            matches = list(extensions_path.glob("{}*.crx".format(extn)))
            if matches and len(matches) == 1:
                options.add_extension(str(matches[0]))

            driver = webdriver.Chrome(options=options, service=service)
            driver.set_page_load_timeout(60)

            if extn == 'adblock':
                time.sleep(15)
            elif extn == 'ghostery':
                windows = driver.window_handles
                for window in windows:
                    try:
                        driver.switch_to.window(window)
                        url_start = driver.current_url[:16]
                        if url_start == 'chrome-extension':
                            element = driver.find_element(By.XPATH, "//ui-button[@type='success']")
                            element.click()
                            time.sleep(2)
                            break
                    except Exception as e:
                        print('ghostery', 1, e)
                        return 0
            else:
                time.sleep(5)

            break
        except Exception as e:
            print(e)
            if num_tries == 1:
                print(f"couldn't create browser session... not trying again")
                print(2, e, driver.current_url)
                return 0
            else:
                print("couldn't create browser session... trying again")
                num_tries = num_tries - 1
                time.sleep(5)
        
    return driver

def run(url, extn, display):
    # os.environ['DISPLAY'] = f":{display}"

    driver = initialize_driver(extn, 3)

    try:
        num_tries = 3
        ret_val = 0

        while num_tries > 0:
            driver.get(url)

            try:
                filepath = f'./page_ss/{extn}'
                if not os.path.isdir(filepath):
                    os.makedirs(filepath, exist_ok=True)
                if driver != None:
                    driver.save_screenshot(f'{filepath}.png')

            except Exception as e:
                print('Cannot take a screenshot')
            
            wait_until_loaded(driver)
            time.sleep(3)

            query = webdriver.execute_script(COOKIES_SCRIPT)

            # ret_val = find_all_iframes(driver)
            # ret_val = detect(driver)
            num_tries -= 1

            if ret_val:
                break

    except Exception as e:
        print(e)

    driver.quit()

if __name__ == "__main__":
    extn = 'ublock'
    url1 = 'https://www.geeksforgeeks.org/deletion-in-linked-list/';
    url2 = 'https://stackoverflow.com/questions/67698176/error-loading-webview-error-could-not-register-service-workers-typeerror-fai'
    url3 = 'https://www.nytimes.com'
    display = 0

    try:
        xvfb_args = [
        '-maxclients', '1024'
        ]
        # vdisplay = Display(backend='xvfb', size=(1920, 1280), extra_args=xvfb_args)
        # # vdisplay = Xvfb(width=1920, height=1280)
        # vdisplay.start()
        # display = vdisplay.display
        
        run(url1, extn, display)
        time.sleep(2)

    except KeyboardInterrupt:
        print('Interrupted')

    except Exception as e:
        print(e)

    # vdisplay.stop()
