#!/bin/bash

# URL='https://www.geeksforgeeks.org/deletion-in-linked-list/';
# URL='https://www.cricbuzz.com'
URL='websites_1000.txt'

# pushd ./verify > /dev/null
# for i in $(seq 1 5);
# do
    # node check_selector.js --headless=false --extn=control --url=$URL 
python3 generate_parallel_logs.py --headless 'true' --extn $1 --url $2 --directory $3
# sleep 2
# python3 clean.py --extn control --site $URL
# done

sleep 5

# # for i in $(seq 1 5);
# # do
#     # node check_selector.js --headless=false --extn=ublock --url=$URL
# python3 generate_parallel_logs.py --headless 'true' --extn ublock --url $URL
# # sleep 2
# # python3 clean.py --extn ublock --site $URL
# # done
# # popd > /dev/null

# sleep 5

python3 process_v8_logs.py --extn $1 --url $URL --directory $3
# # python3 process_v8_logs.py --extn ublock --url $URL

sleep 5

python3 intersection.py --extn $1 --url $URL --directory $3
# python3 intersection.py --extn ublock --url $URL

# sleep 5

# python3 diff.py --extn ublock --url $URL
