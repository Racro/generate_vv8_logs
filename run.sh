#!/bin/bash

URL='https://www.geeksforgeeks.org/deletion-in-linked-list/';

# pushd ./verify > /dev/null
for i in $(seq 1 1);
do
    node check_selector.js --headless=false --extn=control
    sleep 2
    python3 clean.py --extn control
done

for i in $(seq 1 1);
do
    node check_selector.js --headless=false --extn=ublock
    sleep 2
    python3 clean.py --extn ublock
done
# popd > /dev/null

sleep 5

python3 process_v8_logs.py --extn control
python3 process_v8_logs.py --extn ublock

sleep 5

python3 intersection.py --extn control
python3 intersection.py --extn ublock

sleep 5

python3 diff.py --extn ublock