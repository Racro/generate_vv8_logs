#!/bin/bash

URL='https://www.geeksforgeeks.org/deletion-in-linked-list/';

pushd ./verify > /dev/null
for i in $(seq 1 5);
do
    node check_selector.js --headless=true --extn=control
    sleep 2
done
popd > /dev/null

